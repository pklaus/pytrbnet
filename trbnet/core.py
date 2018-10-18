# -*- coding: utf-8 -*-
import ctypes
import os

# TODO: use warnings to indicate access to wrong register or no data

# dictionary with trb error strings. Copied from trberror.h
# TODO: better way to access this directly in libtrbnet
trb_errno_dict = {0: 'TRB_NONE', 1: 'TRB_TX_BUSY', 2: 'TRB_FIFO_NOT_EMPTY',
                  3: 'TRB_FIFO_TIMEOUT', 4: 'TRB_FIFO_HEADERS', 5: 'TRB_FIFO_SEQUENZ',
                  6: 'TRB_FIFO_INVALID_MODE', 7: 'TRB_FIFO_INCOMPLETE_PACKAGE',
                  8: 'TRB_FIFO_INVALID_HEADER', 9: 'TRB_FIFO_MISSING_TERM_HEADER',
                  10: 'TRB_FAILED_WAIT_IS_VALID', 11: 'TRB_FAILED_WAIT_IS_NOT_VALID',
                  12: 'TRB_USER_BUFFER_OVF', 13: 'TRB_INVALID_CHANNEL',
                  14: 'TRB_INVALID_PKG_NUMBER', 15: 'TRB_STATUS_ERROR',
                  16: 'TRB_INVALID_ADDRESS', 17: 'TRB_INVALID_LENGTH',
                  18: 'TRB_ENDPOINT_NOT_REACHED', 19: 'TRB_DMA_UNAVAILABLE',
                  20: 'TRB_DMA_TIMEOUT', 21: 'TRB_READMEM_INVALID_SIZE',
                  22: 'TRB_HDR_DLEN', 23: 'TRB_PEXOR_OPEN', 24: 'TRB_SEMAPHORE',
                  25: 'TRB_FIFO_SHARED_MEM', 26: 'TRB_STATUS_WARNING',
                  27: 'TRB_RPC_ERROR', 28: 'TRB_PEXOR_DATA_ERROR',
                  29: 'TRB_PEXOR_DEVICE_ERROR', 30: 'TRB_PEXOR_DEVICE_TRB_TIMEOUT',
                  31: 'TRB_PEXOR_DEVICE_POLLING_TIMEOUT', 32: 'TRB_PEXOR_DEVICE_DMA_EMPTY',
                  33: 'TRB_PEXOR_DEVICE_INVALID_DMA_SIZE', 34: 'TRB_PEXOR_DEVICE_LOST_CREDENTIAL',
                  35: 'TRB_PEXOR_DEVICE_FIFO_TRANSFER', 36: 'TRB_TRB3_CMD_NOT_SUPPORTED',
                  37: 'TRB_TRB3_SOCKET_ERROR', 38: 'TRB_TRB3_SOCKET_TIMEOUT',
                  39: 'TRB_TRB3_INCOMPLETE_UDP', 40: 'TRB_TRB3_DATA_ERROR',
                  41: 'TRB_TRB3_INVALID_UDP_HEADER'}


class TrbNet(object):
    '''
    Wrapper class for trbnet access using python
    '''

    def __init__(self, trb_server, daq_server, path_to_lib='libtrbnet.so'):
        '''
        Default Constructor. Sets enviromental variable and initialises ports.
        The trbnet daemon has to be running.

        Keyword arguments:
        trbserver -- string for TRB3_SERVER enviromental variable
        daq_server -- string for DAQOPSERVER enviromental variable
        path_to_lib -- full path to libtrbnet.so
        '''
        self.trblib = ctypes.cdll.LoadLibrary(path_to_lib)
        self.declare_types()
        os.environ['TRB3_SERVER'] = trb_server
        os.environ['DAQOPSERVER'] = daq_server
        status = self.trblib.init_ports()
        if status < 0:
            raise Exception('Error initialising ports.')

    def __del__(self):
        '''
        Destructor.
        '''
        self.trblib.close_ports()

    def trb_errno(self):
        '''
        Returns trb_errno flag value
        '''
        return ctypes.c_int.in_dll(self.trblib, 'trb_errno').value

    def declare_types(self):
        '''
        Declare argument and return types of libtrbnet calls via ctypes
        '''
        self.trblib.trb_register_read.argtypes = [ctypes.c_uint16, ctypes.c_uint16,
                                                  ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint]
        self.trblib.trb_register_read.restype = ctypes.c_int
        self.trblib.trb_register_write.argtypes = [ctypes.c_uint16, ctypes.c_uint16,
                                                   ctypes.c_uint32]
        self.trblib.trb_register_write.restype = ctypes.c_int
        self.trblib.trb_register_read_mem.argtypes = [ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint16,
                                                      ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint]
        self.trblib.trb_register_read_mem.restype = ctypes.c_int
        self.trblib.trb_registertime_read_mem.argtypes = [ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint16,
                                                          ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint]
        self.trblib.trb_registertime_read_mem.restype = ctypes.c_int
        self.trblib.trb_read_uid.argtypes = [ctypes.c_uint16, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint]
        self.trblib.trb_read_uid.restype = ctypes.c_int
        self.trblib.trb_set_address.argtypes = [ctypes.c_uint64, ctypes.c_uint8, ctypes.c_uint16]
        self.trblib.trb_set_address.restype = ctypes.c_int
        self.trblib.network_reset.restype = ctypes.c_int
        self.trblib.com_reset.restype = ctypes.c_int
        self.trblib.trb_fifo_flush.argtypes = [ctypes.c_uint8]
        self.trblib.trb_fifo_flush.restype = ctypes.c_int
        self.trblib.trb_send_trigger.argtypes = [ctypes.c_uint8, ctypes.c_uint16,
                                                 ctypes.c_uint8, ctypes.c_uint16]
        self.trblib.trb_send_trigger.restype = ctypes.c_int
        self.trblib.trb_register_setbit.argtypes = [ctypes.c_uint16, ctypes.c_uint16,
                                                    ctypes.c_uint32]
        self.trblib.trb_register_setbit.restype = ctypes.c_int
        self.trblib.trb_register_clearbit.argtypes = [ctypes.c_uint16, ctypes.c_uint16,
                                                      ctypes.c_uint32]
        self.trblib.trb_register_clearbit.restype = ctypes.c_int
        self.trblib.trb_register_loadbit.argtypes = [ctypes.c_uint16, ctypes.c_uint16,
                                                     ctypes.c_uint32, ctypes.c_uint32]
        self.trblib.trb_register_loadbit.restypes = ctypes.c_int
        self.trblib.trb_ipu_data_read.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8,
                                                  ctypes.c_uint16, ctypes.POINTER(ctypes.c_uint32),
                                                  ctypes.c_uint]
        self.trblib.trb_ipu_data_read.restypes = ctypes.c_int
        self.trblib.trb_nettrace.argtypes = [ctypes.c_uint16, ctypes.POINTER(ctypes.c_uint32),
                                                  ctypes.c_uint]
        self.trblib.trb_nettrace.restypes = ctypes.c_int
        

    def trb_register_read(self, trb_address, reg_address):
        '''
        Read value from trb register.

        Keyword arguments:
        trb_address -- trb endpoint address
        reg_address -- register address

        Returns:
        python list [0] TRB-Address of the sender, [1] register value
        '''
        data_array = (ctypes.c_uint32 * 2)()
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        status = self.trblib.trb_register_read(trb_address, reg_address, data_array, 2)
        if status == -1:
            raise Exception('Error while reading trb register, ' + trb_errno_dict[self.trb_errno()])
        print(self.trb_errno())
        return [data_array[i] for i in range(status)]

    def trb_register_write(self, trb_address, reg_address, value):
        '''
        Write trb register

        Keyword Arguments:
        trb_address -- trb endpoint address
        reg_address -- register address
        value -- value to write to register
        '''
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        value = ctypes.c_uint(value)
        status = self.trblib.trb_register_write(trb_address, reg_address, value)
        if status == -1:
            raise Exception('Error while writing trb register, ' + trb_errno_dict[self.trb_errno()])

    def trb_register_read_mem(self, trb_address, reg_address, option, size):
        '''
        Perform several trb register reads

        Keyword Arguments:
        trb_address -- trb endpoint address
        reg_address -- register address
        option -- read option, 0 = read same register several times 1 = read adjacent registers
        size -- number of reads

        Returns:
        python list [0] TRB-Address of the sender, [1:] register values
        '''
        data_array = (ctypes.c_uint32 * (size + 2))()
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        option = ctypes.c_uint8(option)
        status = self.trblib.trb_register_read_mem(trb_address, reg_address, option, ctypes.c_uint16(size), data_array, ctypes.c_uint(size + 2))
        if status == -1:
            raise Exception('Error while reading trb register memory, ' +
                            trb_errno_dict[self.trb_errno()])
        return [data_array[i] for i in range(status)]

    def trb_read_uid(self, trb_address):
        '''
        Read unique id of endpoint

        Keyword Arguments:
        trb_address -- address of endpoint

        Returns:
        python list
        [0]:  UID High-32Bit Word
        [1]: UID Low-32Bit Word
        [2]:  Endpoint Number
        [3]: TRB-Address of the sender
        '''
        data_array = (ctypes.c_uint32 * 4)()
        trb_address = ctypes.c_uint16(trb_address)
        status = self.trblib.trb_read_uid(trb_address, data_array, 4)
        if status == -1:
            raise Exception('Error reading trb uid, ' + trb_errno_dict[self.trb_errno()])
        return [data_array[i] for i in range(status)]

    def trb_set_address(self, uid, endpoint, trb_address):
        '''
        Set trb net address

        Keyword Arguments:
        uid -- the unique ID of the endpoint
        endpoint -- number of the trb endpoint
        trb_address -- new trb address
        '''
        uid = ctypes.c_uint64(uid)
        endpoint = ctypes.c_uint8(endpoint)
        trb_address = ctypes.c_uint16(trb_address)
        status = self.trblib.trb_set_address(uid, endpoint, trb_address)
        if status == -1:
            raise Exception('error setting trb address, ' + trb_errno_dict[self.trb_errno()])

#  rarely used funtions without documentation in trbnet.h
#  meaning of arguments and returned data unknown
    def network_reset(self):
        '''TRB network reset'''
        return self.trblib.network_reset()

    def com_reset(self):
        '''communication reset'''
        return self.trblib.com_reset()

    def trb_fifo_flush(self, channel):
        '''flush trb fifo

        Keyword arguments:
        channel: trb channel (ipu, slowcontrol etc)'''
        channel = ctypes.c_uint8(channel)
        return self.trblib.trb_fifo_flush(channel)

    def trb_send_trigger(self, trigtype, info, random, number):
        '''send trigger to trb

        Keyword arguments:
        trigtype: trigger type (status, calibration)
        info: trigger information
        random: random trigger number
        number: number of triggers
        '''
        trigtype = ctypes.c_uint8(trigtype)
        info = ctypes.c_uint32(info)
        random = ctypes.c_uint8(random)
        number = ctypes.c_uint16(number)
        return self.trblib.trb_send_trigger(trigtype, info, random, number)

    def trb_register_setbit(self, trb_address, reg_address, bitmask):
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        bitmask = ctypes.c_uint32(bitmask)
        return self.trblib.trb_register_setbit(trb_address, reg_address,
                                               bitmask)

    def trb_register_clearbit(self, trb_address, reg_address, bitmask):
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        bitmask = ctypes.c_uint32(bitmask)
        return self.trblib.trb_register_clearbit(trb_address, reg_address,
                                                 bitmask)

    def trb_register_loadbit(self, trb_address, reg_address, bitmask, bitvalue):
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        bitmask = ctypes.c_uint32(bitmask)
        bitvalue = ctypes.c_uint32(bitvalue)
        return self.trblib.trb_register_loadbit(trb_address, reg_address,
                                                bitmask, bitvalue)

    def trb_registertime_read_mem(self, trb_address, reg_address, option, size):
        data_array = (ctypes.c_uint32 * (size + 2))()
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        option = ctypes.c_uint8(option)
        status = self.trblib.trb_register_read_mem(trb_address, reg_address, option, ctypes.c_uint16(size), data_array, ctypes.c_uint(size + 2))
        if status == -1:
            raise Exception('Error while reading trb register memory, ' +
                            trb_errno_dict[self.trb_errno()])
        return [data_array[i] for i in range(status)]

    def trb_ipu_data_read(self, trg_type, trg_info, trg_random, trg_number, size):
        trg_type = ctypes.c_uint8(trg_type)
        trg_info = ctypes.c_uint8(trg_info)
        trg_random = ctypes.c_uint8(trg_random)
        trg_number = ctypes.c_uint16(trg_number)
        data_array = (ctypes.c_uint32 * (size + 2))()
        status = self.trblib.trb_ipu_data_read(trg_type, trg_info, trg_random, trg_number, data_array, ctypes.c_uint(size + 2))
        if status == -1:
            raise Exception('Error while reading trb ipu data, ' +
                            trb_errno_dict[self.trb_errno()])
        return [data_array[i] for i in range(status)]

    def trb_nettrace(self, trb_address, size):
        trb_address = ctypes.c_uint16(trb_address)
        data_array = (ctypes.c_uint32 * (size + 2))()
        status = self.trblib.trb_nettrace(trb_address, data_array, ctypes.c_uint(size + 2))
        if status == -1:
            raise Exception('Error while doing net trace, ' +
                            trb_errno_dict[self.trb_errno()])
        return [data_array[i] for i in range(status)]
