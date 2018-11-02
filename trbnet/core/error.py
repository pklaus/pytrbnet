import enum

class TrbException(Exception):
    def __init__(self, msg, errno, errorstr):
        # Set some exception infomation
        self.msg = msg
        try:
            self.errno = TrbError(errno)
        except ValueError:
            self.errno = errno
        self.errorstr = errorstr

@enum.unique
class TrbError(enum.IntEnum):
    """
    Copied from trbnettools/libtrbnet/trberror.h
    as the names of the enum values are not accessible
    from within the library...
    """
    TRB_NONE = 0
    TRB_TX_BUSY = 1
    TRB_FIFO_NOT_EMPTY = 2
    TRB_FIFO_TIMEOUT = 3
    TRB_FIFO_HEADERS = 4
    TRB_FIFO_SEQUENZ = 5
    TRB_FIFO_INVALID_MODE = 6
    TRB_FIFO_INCOMPLETE_PACKAGE = 7
    TRB_FIFO_INVALID_HEADER = 8
    TRB_FIFO_MISSING_TERM_HEADER = 9
    TRB_FAILED_WAIT_IS_VALID = 10
    TRB_FAILED_WAIT_IS_NOT_VALID = 11
    TRB_USER_BUFFER_OVF = 12
    TRB_INVALID_CHANNEL = 13
    TRB_INVALID_PKG_NUMBER = 14
    TRB_STATUS_ERROR = 15
    TRB_INVALID_ADDRESS = 16
    TRB_INVALID_LENGTH = 17
    TRB_ENDPOINT_NOT_REACHED = 18
    TRB_DMA_UNAVAILABLE = 19
    TRB_DMA_TIMEOUT = 20
    TRB_READMEM_INVALID_SIZE = 21
    TRB_HDR_DLEN = 22
    TRB_PEXOR_OPEN = 23
    TRB_SEMAPHORE = 24
    TRB_FIFO_SHARED_MEM = 25
    TRB_STATUS_WARNING = 26
    TRB_RPC_ERROR = 27
    TRB_PEXOR_DATA_ERROR = 28
    TRB_PEXOR_DEVICE_ERROR = 29
    TRB_PEXOR_DEVICE_TRB_TIMEOUT = 30
    TRB_PEXOR_DEVICE_POLLING_TIMEOUT = 31
    TRB_PEXOR_DEVICE_DMA_EMPTY = 32
    TRB_PEXOR_DEVICE_INVALID_DMA_SIZE = 33
    TRB_PEXOR_DEVICE_LOST_CREDENTIAL = 34
    TRB_PEXOR_DEVICE_FIFO_TRANSFER = 35
    TRB_TRB3_CMD_NOT_SUPPORTED = 36
    TRB_TRB3_SOCKET_ERROR = 37
    TRB_TRB3_SOCKET_TIMEOUT = 38
    TRB_TRB3_INCOMPLETE_UDP = 39
    TRB_TRB3_DATA_ERROR = 40
    TRB_TRB3_INVALID_UDP_HEADER = 41
