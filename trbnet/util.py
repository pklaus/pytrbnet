# -*- coding: utf-8 -*-

def get_endpoint_dict(lin_data, words_per_endpoint, scalar_if_possible=True):
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
    if len(lin_data) % (words_per_endpoint + 1) != 0:
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
