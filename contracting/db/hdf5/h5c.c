#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <hdf5.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

// HDF5 Reference Manual: https://support.hdfgroup.org/HDF5/doc/RM/RM_H5Front.html

#define ATT_LEN_MAX 64000 // http://davis.lbl.gov/Manuals/HDF5-1.8.7/UG/13_Attributes.html#SpecIssues
#define ATT_NAME "value"
#define LOCK_SUFFIX "-lock"

static char dirname_buf[PATH_MAX + 1];

static void
lock_acquire(char *filepath)
{
    strcat(dirname_buf, filepath);
    strcat(dirname_buf, LOCK_SUFFIX);
    while(mkdir(dirname_buf, S_IRWXU) != 0)
        ;
    memset(dirname_buf, 0, sizeof(dirname_buf));
}

static void
lock_release(char *filepath)
{
    strcat(dirname_buf, filepath);
    strcat(dirname_buf, LOCK_SUFFIX);
    rmdir(dirname_buf);
    memset(dirname_buf, 0, sizeof(dirname_buf));
}

static PyObject *
set(PyObject *self, PyObject *args)
{
#ifndef DEBUG
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);
#endif

    char *filepath, *group, *value;
    if(!PyArg_ParseTuple(args, "ssz", &filepath, &group, &value))
        return NULL;

    lock_acquire(filepath);

    hid_t fid = H5Fopen(filepath, H5F_ACC_RDWR, H5P_DEFAULT);
    if(fid < 0)
    {
        fid = H5Fcreate(filepath, H5F_ACC_EXCL, H5P_DEFAULT, H5P_DEFAULT);
        if(fid < 0)
        {
            lock_release(filepath);
            return PyErr_Format(PyExc_OSError, "failed to open/create file \"%s\"", filepath);
        }
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
    static char buf[ATT_LEN_MAX + 1];

#ifndef DEBUG
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);
#endif

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
    H5Tset_size(atype, sizeof(buf));
    memset(buf, 0, sizeof(buf));
    if(H5Aread(aid, atype, buf) < 0)
    {
        H5Tclose(atype);
        H5Aclose(aid);
        H5Fclose(fid);
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
#ifndef DEBUG
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);
#endif

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

static herr_t
store_group_name(hid_t id, const char *name, const H5O_info_t *object_info, void *op_data)
{
    if(strcmp(name, ".") == 0 || object_info->num_attrs == 0)
        return 0;
    return PyList_Append((PyObject *) op_data, PyUnicode_FromString(name));
}

static PyObject *
get_groups(PyObject *self, PyObject *args)
{
#ifndef DEBUG
    H5Eset_auto2(H5P_DEFAULT, NULL, NULL);
#endif

    char *filepath;
    if(!PyArg_ParseTuple(args, "s", &filepath))
        return NULL;

    lock_acquire(filepath);

    hid_t fid = H5Fopen(filepath, H5F_ACC_RDONLY, H5P_DEFAULT);
    if(fid < 0)
    {
        lock_release(filepath);
        Py_RETURN_NONE;
    }

    PyObject *group_names = PyList_New(0);
#if (H5_VERS_MAJOR == 1 && H5_VERS_MINOR >= 12) || H5_VERS_MAJOR > 1
    if(H5Ovisit(fid, H5_INDEX_NAME, H5_ITER_NATIVE, store_group_name, group_names, H5O_INFO_ALL) < 0)
#else
    if(H5Ovisit(fid, H5_INDEX_NAME, H5_ITER_NATIVE, store_group_name, group_names) < 0)
#endif
    {
        H5Fclose(fid);
        lock_release(filepath);
        Py_RETURN_NONE;
    }

    H5Fclose(fid);

    lock_release(filepath);

    return group_names;
}

static PyMethodDef methods[] = {
    {"set", set, METH_VARARGS, "Set value"},
    {"get", get, METH_VARARGS, "Get value"},
    {"delete", delete, METH_VARARGS, "Delete value"},
    {"get_groups", get_groups, METH_VARARGS, "Get groups"}
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
