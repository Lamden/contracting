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
    int cu_costs[144];
    unsigned int cost;
    unsigned int stamp_supplied;
    int started;
    char *cu_cost_fname;

} Tracer;

void read_cu_costs(char *fname, int cu_costs[]) {
    FILE * fp;
    char * line = NULL;
    size_t len = 0;
    ssize_t read_bytes;

    fp = fopen(fname, "r");
    if (fp == NULL) {
        PyErr_SetString(PyExc_AssertionError, "Computational Costs file is not found due to unsuccessful install.\n");
        exit(EXIT_FAILURE);
    }

    while ((read_bytes = getline(&line, &len, fp)) != -1) {
        int opcode = strtol(strtok(line, ","), NULL, 10);
        int cost = strtol(strtok(NULL, ","), NULL, 10);
        cu_costs[opcode] = cost;
    }

    fclose(fp);
    if (line)
        free(line);
}

static int
Tracer_init(Tracer *self, PyObject *args, PyObject *kwds)
{

    char *fname = getenv("CU_COST_FNAME");

    read_cu_costs(fname, self->cu_costs); // Read cu cu_costs from ones interpreted in Python

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
             if (self->cost + self->cu_costs[opcode] > self->stamp_supplied) {
                 PyErr_SetString(PyExc_AssertionError, "The cost has exceeded the stamp supplied!\n");
                 PyEval_SetTrace(NULL, NULL);
                 self->started = 0;
                 return RET_ERROR;
             }
             self->cost += self->cu_costs[opcode];
             break;

         // case PyTrace_EXCEPTION:
         //     printf("EXCEPTION\n");
         //     // return RET_ERROR;
         //     break;

         default:
             break;
     }

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
        PyArg_ParseTuple(args, "i", &self->stamp_supplied);
    return Py_BuildValue("");
}

static PyObject *
Tracer_get_stamp_used(Tracer *self, PyObject *args, PyObject *kwds)
{
    return Py_BuildValue("i", self->cost);
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

    { "set_stamp",  (PyCFunction) Tracer_set_stamp,     METH_VARARGS,
            PyDoc_STR("Set the stamp before starting the tracer") },

    { "get_stamp_used",  (PyCFunction) Tracer_get_stamp_used,     METH_VARARGS,
            PyDoc_STR("Get the stamp usage after it's been completed") },

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
