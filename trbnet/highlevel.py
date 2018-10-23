# -*- coding: utf-8 -*-
from .lowlevel import _TrbNet


class TrbNet(_TrbNet):
    '''
    High level wrapper providing utility functions for the TrbNet class
    '''

    def trb_register_read(self, trb_address, reg_address):
        lin_data = super().trb_register_read(trb_address, reg_address)
        return self._get_scalar_endpoint_dict(lin_data)

    def trb_register_read_mem(self, trb_address, reg_address, option, size):
        lin_data = super().trb_register_read_mem(trb_address, reg_address, option, size)
        return self._get_dynamic_endpoint_dict(lin_data)

    def _get_dynamic_endpoint_dict(self, lin_data):
        """
        A utility function to structure response data from the
        trb_register_read() and trb_register_read_mem() functions.
        As multiple endpoints can reply to a single request, it
        splits the linar response into the data from each eandpoint.
        Returns a dictionary with the endpoints as keys and the
        respective data as values.

        Returns:
        dict -- key: endpoint trb_address, value: list(int) (32-bit words)
        """
        endpoint_dict = {}
        offset = 0
        while len(lin_data) > offset:
            header = lin_data[offset]
            offset += 1
            length, endpoint = (header >> 16), (header & 0xffff)
            endpoint_dict[endpoint] = lin_data[offset:offset+length]
            offset += length
        return endpoint_dict

    def _get_scalar_endpoint_dict(self, lin_data):
        """
        A utility function to structure response data from the
        trb_register_read() and trb_register_read_mem() functions.
        As multiple endpoints can reply to a single request, it
        splits the linar response into the data from each eandpoint.
        Returns a dictionary with the endpoints as keys and the
        respective scalar data as value.

        Returns:
        dict -- key: endpoint trb_address, value: int (32-bit word)
        """
        endpoint_dict = {}
        if (len(lin_data) % 2) != 0:
            raise ValueError("len(lin_data) =", len(lin_data), " -  expected a multiple of", 2)
        endpoints = lin_data[::2]
        offset = 0
        for endpoint in endpoints:
            endpoint_dict[endpoint] = lin_data[offset + 1]
            offset += 2
        return endpoint_dict
