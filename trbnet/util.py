# -*- coding: utf-8 -*-

def get_endpoint_dict(lin_data, words_per_endpoint=-1, scalar_if_possible=True):
    """
    A utility function to structure response data from the
    trb_register_read() and trb_register_read_mem() functions.
    As multiple endpoints can reply to a single request, it
    splits the linar response into the data from each finds
    the number of endpoints ot Finds the number of endpoints
    Returns a dictionary with the endpoints as keys and the
    respective data as values, either as a list of words (ints)
    or a single (scalar) integer. If scalar_if_possible==False,
    the dictionary value is always a list.
    """
    endpoint_dict = {}
    if words_per_endpoint == -1:
        offset = 0
        while len(lin_data) > offset:
            header = lin_data[offset]
            offset += 1
            length, endpoint = (header >> 16), (header & 0xffff)
            endpoint_dict[endpoint] = lin_data[offset:offset+length]
            offset += length
    else:
        if (len(lin_data) % (words_per_endpoint + 1)) != 0:
            raise ValueError("len(lin_data) =", len(lin_data), " -  expected a multiple of", (words_per_endpoint + 1))
        endpoints = lin_data[::(words_per_endpoint + 1)]
        offset = 0
        for endpoint in endpoints:
            offset += 1
            if words_per_endpoint == 1 and scalar_if_possible:
                endpoint_dict[endpoint] = lin_data[offset]
            else:
                endpoint_dict[endpoint] = lin_data[offset:offset+words_per_endpoint]
            offset += words_per_endpoint
    return endpoint_dict

def _find_lib(inp_lib_name):
    """
    Find location of a dynamic library
    Idea found in <https://github.com/pyepics/pyepics/blob/master/epics/ca.py#L117>
    """
    # Test 1: if LIBTRBNET env var is set, use it.
    import os
    dllpath = os.environ.get('LIBTRBNET', None)

    if (dllpath is not None and os.path.exists(dllpath) and
            os.path.isfile(dllpath)):
        return dllpath

    # Test 2: look in installed python location for dll (not used right now)
    #dllpath = resource_filename('trbnet.clibs', clib_search_path(inp_lib_name))
    #if (os.path.exists(dllpath) and os.path.isfile(dllpath)):
    #    return dllpath

    # Test 3: look for library in LD_LIBRARY_PATH with ctypes.util
    import ctypes.util
    dllpath = ctypes.util._findLib_ld(inp_lib_name)
    if dllpath is not None:
        return dllpath

    raise NameError('cannot find lib'+inp_lib_name)
