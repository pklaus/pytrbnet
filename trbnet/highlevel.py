# -*- coding: utf-8 -*-
from .lowlevel import _TrbNet
from .util import get_endpoint_dict


class TrbNet(_TrbNet):
    '''
    High level wrapper providing utility functions for the TrbNet class
    '''

    def trb_register_read(self, trb_address, reg_address):
        lin_data = super().trb_register_read(trb_address, reg_address)
        return get_endpoint_dict(lin_data, words_per_endpoint=1)

    def trb_register_read_mem(self, trb_address, reg_address, option, size):
        lin_data = super().trb_register_read_mem(trb_address, reg_address, option, size)
        return get_endpoint_dict(lin_data, words_per_endpoint=size, scalar_if_possible=False)
