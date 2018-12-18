# -*- coding: utf-8 -*-

def _find_lib(inp_lib_name):
    """
    Find location of a dynamic library
    Idea found in <https://github.com/pyepics/pyepics/blob/master/epics/ca.py#L117>
    """
    # Test 1: if LIBTRBNET env var is set, use it.
    import os
    dllpath = os.environ.get('LIBTRBNET', None)
    if dllpath is not None:
        dllpath = os.path.expanduser(dllpath)
        if os.path.exists(dllpath) and os.path.isfile(dllpath):
            return dllpath

    # Test 2: look in installed python location for dll (not used right now)
    #dllpath = resource_filename('trbnet.clibs', clib_search_path(inp_lib_name))
    #if (os.path.exists(dllpath) and os.path.isfile(dllpath)):
    #    return dllpath

    # Test 3: look for library in LD_LIBRARY_PATH with ctypes.util
    import ctypes.util
    dllpath = ctypes.util._findLib_ld(inp_lib_name) if hasattr(ctypes.util, '_findLib_ld') else None
    if dllpath is not None:
        return dllpath

    raise NameError('cannot find lib'+inp_lib_name)
