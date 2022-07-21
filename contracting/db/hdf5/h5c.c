#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <hdf5.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string.h>

#define BUFSIZE 64000
#define ATT_NAME "value"
#define DIRBUF_SIZE 4096
#define LOCK_SUFFIX "-lock"

static char dirbuf[DIRBUF_SIZE];

void lock_acquire(char *filepath)
{
    strcat(dirbuf, filepath);
    strcat(dirbuf, LOCK_SUFFIX);
    while(mkdir(dirbuf, S_IRWXU) != 0)
        ;
    memset(dirbuf, 0, DIRBUF_SIZE);
}

void lock_release(char *filepath)
{
    strcat(dirbuf, filepath);
    strcat(dirbuf, LOCK_SUFFIX);
    rmdir(dirbuf);
    memset(dirbuf, 0, DIRBUF_SIZE);
}

static PyObject *
set(PyObject *self, PyObject *args)
{
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);

    char *filepath, *group, *value;
    if(!PyArg_ParseTuple(args, "ssz", &filepath, &group, &value))
        return NULL;

    lock_acquire(filepath);

    hid_t fid = H5Fopen(filepath, H5F_ACC_RDWR, H5P_DEFAULT);
    if(fid < 0)
    {
        fid = H5Fcreate(filepath, H5F_ACC_EXCL, H5P_DEFAULT, H5P_DEFAULT);
        if(fid < 0)
            while((fid = H5Fopen(filepath, H5F_ACC_RDWR, H5P_DEFAULT)) < 0)
                ;
    }

    hid_t gid = H5Gopen(fid, group, H5P_DEFAULT);
    if(gid < 0)
    {
        hid_t lcpl = H5Pcreate(H5P_LINK_CREATE);
        H5Pset_create_intermediate_group(lcpl, 1);
        gid = H5Gcreate(fid, group, lcpl, H5P_DEFAULT, H5P_DEFAULT);
        H5Pclose(lcpl);
    }

    hid_t atype = H5Tcopy(H5T_C_S1);
    H5Tset_size(atype, strlen(value));
    H5Adelete(gid, ATT_NAME);
    hid_t aid = H5Acreate(gid, ATT_NAME, atype, H5Screate(H5S_SCALAR), H5P_DEFAULT, H5P_DEFAULT);
    H5Awrite(aid, atype, value);

    H5Tclose(atype);
    H5Aclose(aid);
    H5Gclose(gid);
    H5Fclose(fid);

    lock_release(filepath);

    Py_RETURN_NONE;
}

static PyObject *
get(PyObject *self, PyObject *args)
{
    static char buf[BUFSIZE];

    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);

    char *filepath, *group;
    if(!PyArg_ParseTuple(args, "ss", &filepath, &group))
        return NULL;

    lock_acquire(filepath);

    hid_t fid = H5Fopen(filepath, H5F_ACC_RDONLY, H5P_DEFAULT);
    if(fid < 0)
    {
        lock_release(filepath);
        Py_RETURN_NONE;
    }

    hid_t aid = H5Aopen_by_name(fid, group, ATT_NAME, H5P_DEFAULT, H5P_DEFAULT);
    if(aid < 0)
    {
        H5Fclose(fid);
        lock_release(filepath);
        Py_RETURN_NONE;
    }

    hid_t atype = H5Tcopy(H5T_C_S1);
    H5Tset_size(atype, BUFSIZE);
    memset(buf, 0, BUFSIZE);
    if(H5Aread(aid, atype, buf) < 0)
    {
        lock_release(filepath);
        Py_RETURN_NONE;
    }

    H5Tclose(atype);
    H5Aclose(aid);
    H5Fclose(fid);

    lock_release(filepath);

    return PyUnicode_FromString(buf);
}

static PyObject *
delete(PyObject *self, PyObject *args)
{
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);

    char *filepath, *group;
    if(!PyArg_ParseTuple(args, "ss", &filepath, &group))
        return NULL;

    lock_acquire(filepath);

    hid_t fid = H5Fopen(filepath, H5F_ACC_RDWR, H5P_DEFAULT);
    hid_t gid = H5Gopen(fid, group, H5P_DEFAULT);
    H5Adelete(gid, ATT_NAME);

    H5Gclose(gid);
    H5Fclose(fid);

    lock_release(filepath);

    Py_RETURN_NONE;
}

static PyMethodDef methods[] = {
    {"set", set, METH_VARARGS, "Set value"},
    {"get", get, METH_VARARGS, "Get value"},
    {"delete", delete, METH_VARARGS, "Delete value"}
};

static struct PyModuleDef h5cmodule = {
    PyModuleDef_HEAD_INIT,
    "h5c",
    NULL,
    -1,
    methods
};

PyMODINIT_FUNC
PyInit_h5c(void)
{
    return PyModule_Create(&h5cmodule);
}
