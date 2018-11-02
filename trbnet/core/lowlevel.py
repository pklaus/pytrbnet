# -*- coding: utf-8 -*-
import ctypes
import os

from .error import TrbException

# TODO: use warnings to indicate access to wrong register or no data


class TrbTerm(ctypes.Structure):
    """
    The TRB_TERM C Struct representing the information
    carried by network termination packets.
    """
    _fields_ = [ ("status_common", ctypes.c_uint16),
                 ("status_channel", ctypes.c_uint16),
                 ("sequence", ctypes.c_uint16),
                 ("channel", ctypes.c_uint8) ]

class _TrbNet(object):
    '''
    Wrapper class for trbnet access using python
    '''

    def __init__(self, libtrbnet=None, daqopserver=None, trb3_server=None, buffersize=4194304):
        '''
        Constructor for the low level TrbNet class.
        Loads the shared library (libtrbnet), sets enviromental variables and initialises ports.

        Depending on the version of libtrbnet.so used, the connection to TrbNet is established
        either by directly connecting to a TRB board (trbnettools/libtrbnet/libtrbnet.so) or
        by connecting to a trbnet daemon instance (if trbnettools/trbnetd/libtrbnet.so is used).
        Selecting the library can happen by:
        - Specifying the full path to the library via the libtrbnet keyword argument.
        - Specifying the full path to the library via the environment variable LIBTRBNET.
        - Adding the directory, libtrbnet.so resides in to the environment variable LD_LIBRARY_PATH.

        To specify the peer to connect to, the environment variables DAQOPSERVER, TRB3_SERVER
        are read. For easier scripting, those environment variables can also be set inside this
        constructor if the keywords arguments daqopserver or trb3_server are specified.

        Keyword arguments:
        libtrbnet -- full path to libtrbnet.so
        daqopserver -- optional override of the DAQOPSERVER enviromental variable
        trb3_server -- optional override of the TRB3_SERVER enviromental variable
        buffersize -- Size of the buffer in 32-bit words when reading back data (default: 16MiB)
        '''
        if trb3_server: os.environ['TRB3_SERVER'] = trb3_server
        if daqopserver: os.environ['DAQOPSERVER'] = daqopserver
        self.buffersize = buffersize
        if not libtrbnet:
            from .libutils import _find_lib
            libtrbnet =_find_lib('trbnet')
        self.libtrbnet = libtrbnet
        self.trblib = ctypes.cdll.LoadLibrary(libtrbnet)
        self.declare_types()
        status = self.trblib.init_ports()
        if status < 0:
            errno = self.trb_errno()
            raise TrbException('Error initialising ports.', errno, self.trb_errorstr(errno))

    def __del__(self):
        '''
        Destructor.
        '''
        try:
            self.trblib.close_ports()
        except AttributeError:
            pass

    def trb_errno(self):
        '''
        Returns trb_errno flag value
        '''
        return ctypes.c_int.in_dll(self.trblib, 'trb_errno').value

    def trb_term(self):
        term = TrbTerm.in_dll(self.trblib, 'trb_term')
        return (term.status_common, term.status_channel, term.sequence, term.channel)

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
        self.trblib.trb_errorstr.argtypes = [ctypes.c_int]
        self.trblib.trb_errorstr.restype = ctypes.c_char_p
        self.trblib.trb_termstr.argtypes = [TrbTerm]
        self.trblib.trb_termstr.restype = ctypes.c_char_p
        

    def trb_errorstr(self, errno):
        '''
        Get error string for an integer error number.

        Arguments:
        errno -- error number

        Returns:
        python str with description of the error
        '''
        errno = ctypes.c_int(errno)
        _result = self.trblib.trb_errorstr(errno)
        return _result.decode('ascii')

    def trb_register_read(self, trb_address, reg_address):
        '''
        Read value from trb register.

        Arguments:
        trb_address -- node(s) to read from
        reg_address -- register address

        Returns:
        python list [0] TRB-Address of the sender, [1] register value
        '''
        data_array = (ctypes.c_uint32 * self.buffersize)()
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        status = self.trblib.trb_register_read(trb_address, reg_address, data_array, self.buffersize)
        if status == -1:
            errno = self.trb_errno()
            raise TrbException('Error while reading trb register.', errno, self.trb_errorstr(errno))
        return [data_array[i] for i in range(status)]

    def trb_register_write(self, trb_address, reg_address, value):
        '''
        Write trb register

        Arguments:
        trb_address -- node(s) to write to
        reg_address -- register address
        value -- value to write to register
        '''
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        value = ctypes.c_uint(value)
        status = self.trblib.trb_register_write(trb_address, reg_address, value)
        if status == -1:
            errno = self.trb_errno()
            raise TrbException('Error while writing trb register.', errno, self.trb_errorstr(errno))

    def trb_register_read_mem(self, trb_address, reg_address, option, size):
        '''
        Perform several trb register reads

        Arguments:
        trb_address -- node(s) to read from
        reg_address -- register address
        option -- read option, 0 = read same register several times 1 = read adjacent registers
        size -- number of reads

        Returns:
        python list [0] TRB-Address of the sender, [1:] register values
        '''

        data_array = (ctypes.c_uint32 * self.buffersize)()
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        option = ctypes.c_uint8(option)
        status = self.trblib.trb_register_read_mem(trb_address, reg_address, option, ctypes.c_uint16(size), data_array, ctypes.c_uint(self.buffersize))
        if status == -1:
            errno = self.trb_errno()
            raise TrbException('Error while reading trb register memory.',
                               errno, self.trb_errorstr(errno))
        return [data_array[i] for i in range(status)]

    def trb_read_uid(self, trb_address):
        '''
        Read unique id(s) of TrbNet node(s)

        Arguments:
        trb_address -- node(s) to be queried

        Returns:
        python list, length is a multiple of 4
        [i+0]:  UID High-32Bit Word
        [i+1]: UID Low-32Bit Word
        [i+2]:  Endpoint Number
        [i+3]: TRB-Address of the sender
        '''
        data_array = (ctypes.c_uint32 * self.buffersize)()
        trb_address = ctypes.c_uint16(trb_address)
        status = self.trblib.trb_read_uid(trb_address, data_array, self.buffersize)
        if status == -1:
            errno = self.trb_errno()
            raise TrbException('Error reading trb uid.',
                               errno, self.trb_errorstr(errno))
        return [data_array[i] for i in range(status)]

    def trb_set_address(self, uid, endpoint, trb_address):
        '''
        Set trb net address

        Arguments:
        uid -- the unique ID of the node
        endpoint -- number of the trb endpoint
        trb_address -- new trb address
        '''
        uid = ctypes.c_uint64(uid)
        endpoint = ctypes.c_uint8(endpoint)
        trb_address = ctypes.c_uint16(trb_address)
        status = self.trblib.trb_set_address(uid, endpoint, trb_address)
        if status == -1:
            errno = self.trb_errno()
            raise TrbException('Error setting trb address.',
                               errno, self.trb_errorstr(errno))

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

        Arguments:
        channel: trb channel (ipu, slowcontrol etc)'''
        channel = ctypes.c_uint8(channel)
        return self.trblib.trb_fifo_flush(channel)

    def trb_send_trigger(self, trigtype, info, random, number):
        '''send trigger to trb

        Arguments:
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
        data_array = (ctypes.c_uint32 * self.buffersize)()
        trb_address = ctypes.c_uint16(trb_address)
        reg_address = ctypes.c_uint16(reg_address)
        option = ctypes.c_uint8(option)
        status = self.trblib.trb_register_read_mem(trb_address, reg_address, option, ctypes.c_uint16(size), data_array, ctypes.c_uint(self.buffersize))
        if status == -1:
            errno = self.trb_errno()
            raise TrbException('Error while reading trb register memory.', errno, self.trb_errorstr(errno))
        return [data_array[i] for i in range(status)]

    def trb_ipu_data_read(self, trg_type, trg_info, trg_random, trg_number, size):
        trg_type = ctypes.c_uint8(trg_type)
        trg_info = ctypes.c_uint8(trg_info)
        trg_random = ctypes.c_uint8(trg_random)
        trg_number = ctypes.c_uint16(trg_number)
        data_array = (ctypes.c_uint32 * self.buffersize)()
        status = self.trblib.trb_ipu_data_read(trg_type, trg_info, trg_random, trg_number, data_array, ctypes.c_uint(self.buffersize))
        if status == -1:
            errno = self.trb_errno()
            raise TrbException('Error while reading trb ipu data.', errno, self.trb_errorstr(errno))
        return [data_array[i] for i in range(status)]

    def trb_nettrace(self, trb_address, size):
        trb_address = ctypes.c_uint16(trb_address)
        data_array = (ctypes.c_uint32 * self.buffersize)()
        status = self.trblib.trb_nettrace(trb_address, data_array, ctypes.c_uint(self.buffersize))
        if status == -1:
            errno = self.trb_errno()
            raise TrbException('Error while doing net trace.', errno, self.trb_errorstr(errno))
        return [data_array[i] for i in range(status)]

    def trb_termstr(self, term):
        '''
        Get string representation for network termination packet info tuple.

        Arguments:
        term -- network termination packet info
                (TrbTerm instance or tuple of four integer values)

        Returns:
        python str with description of the error
        '''
        if isinstance(term, tuple): term = TrbTerm(*term)
        _result = self.trblib.trb_termstr(term)
        return _result.decode('ascii')
