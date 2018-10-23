# -*- coding: utf-8 -*-
from .lowlevel import _TrbNet


class TrbNet(_TrbNet):
    '''
    High level wrapper providing utility functions for the TrbNet class
    '''

    def register_read(self, trb_address, reg_address):
        lin_data = super().trb_register_read(trb_address, reg_address)
        if (len(lin_data) % 2) != 0:
            raise ValueError("len(lin_data) == %d -  expected a multiple of %d" % (len(lin_data), 2))
        result = self._get_dynamic_trb_address_dict(lin_data, force_length=1)
        return {key: value[0] for key, value in result.items()}

    def register_read_mem(self, trb_address, reg_address, option, size):
        lin_data = super().trb_register_read_mem(trb_address, reg_address, option, size)
        return self._get_dynamic_trb_address_dict(lin_data)

    def _get_dynamic_trb_address_dict(self, lin_data, force_length=0):
        """
        A utility function to structure response data from the
        trb_register_read() and trb_register_read_mem() functions.
        As multiple TrbNet nodes can reply to a single request, it
        splits the linar response into the data from each eandpoint.
        Returns a dictionary with the trb_address as keys and the
        respective data as values.

        Returns:
        dict -- key: trb_address, value: list(int) (32-bit words)
        """
        trb_address_responses = {}
        offset = 0
        while len(lin_data) > offset:
            header = lin_data[offset]
            offset += 1
            length, trb_address = (header >> 16), (header & 0xffff)
            if force_length: length = force_length
            trb_address_responses[trb_address] = lin_data[offset:offset+length]
            offset += length
        return trb_address_responses
