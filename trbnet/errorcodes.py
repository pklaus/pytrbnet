# -*- coding: utf-8 -*-

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