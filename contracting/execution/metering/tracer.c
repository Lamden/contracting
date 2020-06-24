/* C-based Tracer for Coverage. */

#include "Python.h"
#include "compile.h"        /* in 2.3, this wasn't part of Python.h */
#include "eval.h"           /* or this. */
#include "structmember.h"
#include "frameobject.h"

#include <stdio.h>          /* For reading CU cu_costs */
#include <stdlib.h>
#include <string.h>

/* Py 2.x and 3.x compatibility */

#ifndef Py_TYPE
#define Py_TYPE(o)    (((PyObject*)(o))->ob_type)
#endif

#if PY_MAJOR_VERSION >= 3

#define MyType_HEAD_INIT    PyVarObject_HEAD_INIT(NULL, 0)

#else

#define MyType_HEAD_INIT    PyObject_HEAD_INIT(NULL)  0,

#endif /* Py3k */

/* The values returned to indicate ok or error. */
#define RET_OK      0
#define RET_ERROR   -1

/* The Tracer type. */

typedef struct {
    PyObject_HEAD

    /* Variables to keep track of metering */
    unsigned long long cost;
    unsigned long long stamp_supplied;
    int started;
    char *cu_cost_fname;

} Tracer;

unsigned long long cu_costs[] = {2, 4, 5, 2, 4, 0, 0, 0, 2, 2, 3, 2, 0, 0, 4, 1000, 1000, 0, 30, 3, 0, 4, 3, 3, 3, 4, 4, 4, 5, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 12, 15, 0, 0, 5, 5, 4, 0, 4, 4, 4, 6, 6, 6, 6, 6, 30,
                7, 12, 1000, 1610, 4, 7, 0, 6, 6, 6, 6, 6, 2, 15, 15, 2, 126, 1000, 4, 4, 4, 4, 2, 2, 8, 8, 2, 6, 6, 4,
                4, 0, 2, 2, 2, 5, 8, 7, 4, 4, 38, 126, 4, 4, 4, 4, 4, 4, 3, 0, 0, 2, 4, 2, 3, 0, 2, 2, 2, 1000, 0, 0, 5,
                9, 7, 12, 0, 7, 2, 2, 2, 0, 0, 12, 12, 15, 2, 8, 8, 5, 2, 5, 7, 9, 2, 8, 15, 30, 7, 8, 4};

unsigned long long estimate = 0;
unsigned long long factor = 1000;

static int
Tracer_init(Tracer *self, PyObject *args, PyObject *kwds)
{
    //char *fname = getenv("CU_COST_FNAME");

    //read_cu_costs(fname, self->cu_costs); // Read cu cu_costs from ones interpreted in Python

    self->started = 0;
    self->cost = 0;

    return RET_OK;
}

static void
Tracer_dealloc(Tracer *self)
{
    if (self->started) {
        PyEval_SetTrace(NULL, NULL);
    }

    Py_TYPE(self)->tp_free((PyObject*)self);
}

//static void reprint(PyObject *obj) {
//    PyObject * repr = PyObject_Repr(obj);
//    PyObject * str = PyUnicode_AsEncodedString(repr, "utf-8", "~E~");
//    const char *bytes = PyBytes_AS_STRING(str);
//
//    printf("REPR: %s\n", bytes);
//
//    Py_XDECREF(repr);
//    Py_XDECREF(str);
//}


/*
 * The Trace Function
 */

 static int
 Tracer_trace(Tracer *self, PyFrameObject *frame, int what, PyObject *arg)
 {
     const char * str;
     int opcode;

     // IF, Frame object globals contains __contract__ and it is true, continue
     PyObject *kv = PyUnicode_FromString("__contract__");
     int t = PyDict_Contains(frame->f_globals, kv);

     if (t != 1) {
        return RET_OK;
     }

     switch (what) {
         // case PyTrace_CALL:      /* 0 */
         //     printf("CALL\n");
         //     break;
         //
         // case PyTrace_RETURN:    /* 3 */
         //     printf("RETURN\n");
         //     break;

         case PyTrace_LINE:      /* 2 */
             // printf("LINE\n");
             str = PyBytes_AS_STRING(frame->f_code->co_code);
             opcode = str[frame->f_lasti];
             if (opcode < 0) opcode = -opcode;

             estimate = (self->cost + cu_costs[opcode]) / factor;
             estimate = estimate + 1;
             //estimate = estimate * factor;

             if (estimate > self->stamp_supplied) {
                 PyErr_SetString(PyExc_AssertionError, "The cost has exceeded the stamp supplied!\n");
                 PyEval_SetTrace(NULL, NULL);
                 self->started = 0;
                 return RET_ERROR;
             }
             self->cost += cu_costs[opcode];
             break;

         // case PyTrace_EXCEPTION:
         //     printf("EXCEPTION\n");
         //     // return RET_ERROR;
         //     break;

         default:
             break;
     }
     //}

     return RET_OK;
 }

static PyObject *
Tracer_start(Tracer *self, PyObject *args)
{
    PyEval_SetTrace((Py_tracefunc)Tracer_trace, (PyObject*)self);
    self->cost = 0;
    self->started = 1;
    return Py_BuildValue("");
}

static PyObject *
Tracer_stop(Tracer *self, PyObject *args)
{
    if (self->started) {
        PyEval_SetTrace(NULL, NULL);
        self->started = 0;
    }

    return Py_BuildValue("");
}

static PyObject *
Tracer_set_stamp(Tracer *self, PyObject *args, PyObject *kwds)
{
        PyArg_ParseTuple(args, "L", &self->stamp_supplied);
    return Py_BuildValue("");
}

static PyObject *
Tracer_reset(Tracer *self)
{
    self->cost = 0;
    self->stamp_supplied = 0;
    self->started = 0;
    return Py_BuildValue("");
}

static PyObject *
Tracer_add_cost(Tracer *self, PyObject *args, PyObject *kwds)
{
    // This allows you to arbitrarily add to the cost variable from Python
    // Implemented for adding costs to database read / write operations
    unsigned long long new_cost;
    PyArg_ParseTuple(args, "L", &new_cost);
    self->cost += new_cost;

    if (self->cost > self->stamp_supplied) {
         PyErr_SetString(PyExc_AssertionError, "The cost has exceeded the stamp supplied!\n");
         PyEval_SetTrace(NULL, NULL);
         self->started = 0;
         return NULL;
     }

    return Py_BuildValue("");
}

static PyObject *
Tracer_get_stamp_used(Tracer *self, PyObject *args, PyObject *kwds)
{
    return Py_BuildValue("L", self->cost);
}

static PyObject *
Tracer_is_started(Tracer *self)
{
    return Py_BuildValue("i", self->started);
}

static PyMemberDef
Tracer_members[] = {
    { "started",       T_OBJECT, offsetof(Tracer, started), 0,
            PyDoc_STR("Whether or not the tracer has been enabled") },
};

static PyMethodDef
Tracer_methods[] = {
    { "start",      (PyCFunction) Tracer_start,         METH_VARARGS,
            PyDoc_STR("Start the tracer") },

    { "stop",       (PyCFunction) Tracer_stop,          METH_VARARGS,
            PyDoc_STR("Stop the tracer") },

    { "reset",       (PyCFunction) Tracer_reset,          METH_VARARGS,
            PyDoc_STR("Resets the tracer") },

    { "add_cost",       (PyCFunction) Tracer_add_cost,          METH_VARARGS,
            PyDoc_STR("Add to the cost. Throws AssertionError if cost exceeds stamps supplied.") },

    { "set_stamp",  (PyCFunction) Tracer_set_stamp,     METH_VARARGS,
            PyDoc_STR("Set the stamp before starting the tracer") },

    { "get_stamp_used",  (PyCFunction) Tracer_get_stamp_used,     METH_VARARGS,
            PyDoc_STR("Get the stamp usage after it's been completed") },

    { "is_started",  (PyCFunction) Tracer_is_started,     METH_VARARGS,
            PyDoc_STR("Returns 1 if tracer is started, 0 if not.") },

    { NULL }
};

static PyTypeObject
TracerType = {
    MyType_HEAD_INIT
    "contracting.execution.metering.tracer",         /*tp_name*/
    sizeof(Tracer),            /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)Tracer_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "Tracer objects",          /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    Tracer_methods,            /* tp_methods */
    Tracer_members,            /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Tracer_init,     /* tp_init */
    0,                         /* tp_alloc */
    0,                         /* tp_new */
};

/* Module definition */

#define MODULE_DOC PyDoc_STR("Fast tracer for Smart Contract metering.")

#if PY_MAJOR_VERSION >= 3

static PyModuleDef
moduledef = {
    PyModuleDef_HEAD_INIT,
    "contracting.execution.metering.tracer",
    MODULE_DOC,
    -1,
    NULL,       /* methods */
    NULL,
    NULL,       /* traverse */
    NULL,       /* clear */
    NULL
};


PyObject *
PyInit_tracer(void)
{
    Py_Initialize();
    PyObject * mod = PyModule_Create(&moduledef);
    if (mod == NULL) {
        return NULL;
    }
    TracerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&TracerType) < 0) {
        Py_DECREF(mod);
        printf("Not ready");
        return NULL;
    }
    Py_INCREF(&TracerType);
    PyModule_AddObject(mod, "Tracer", (PyObject *)&TracerType);
    return mod;
}

#else

void
inittracer(void)
{
    PyObject * mod;
    mod = Py_InitModule3("contracting.execution.metering.tracer", NULL, MODULE_DOC);

    if (mod == NULL) {
        return;
    }

    TracerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&TracerType) < 0) {
        return;
    }

    Py_INCREF(&TracerType);
    PyModule_AddObject(mod, "Tracer", (PyObject *)&TracerType);
}

#endif /* Py3k */
