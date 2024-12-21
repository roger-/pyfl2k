import ctypes
from ctypes import c_int, c_uint32, c_void_p, c_char_p, c_uint8, POINTER
from ctypes.util import find_library
from enum import IntEnum
import logging


log = logging.getLogger(__name__)

def load_library():
    log.debug(f"searching for library")

    # add some candidate driver file names
    driver_files = []
    driver_files += [lambda : find_library('osmo-fl2k'), lambda : find_library('libosmo-fl2k')]
    driver_files += ['libosmo-fl2k.so.0']  # Linux
    driver_files += ['./libosmo-fl2k.dll', '../libosmo-fl2k.dll']   # Windows
    driver_files += ['libosmo-fl2k.dylib'] # MacOS
    
    lib = None

    for driver in driver_files:
        if callable(driver):
            driver = driver()
        if driver is None:
            continue

        try:
            lib = ctypes.CDLL(driver)
            break
        except Exception as e:
            pass
    else:
        raise ImportError('Error loading libosmo-fl2k. Make sure it '\
                          '(and all of its dependencies) are in your path')
    
    log.debug(f"loaded library: {driver}")

    return lib

# error enums
class EnumError(IntEnum):
    SUCCESS = 0
    TRUE = 1
    INVALID_PARAM = -1
    NO_DEVICE = -2
    NOT_FOUND = -5
    BUSY = -6
    TIMEOUT = -7
    NO_MEM = -11

class Fl2kError(Exception):
    def __init__(self, msg: str | None=None, error_code: EnumError | None=None):
        self.error_code = error_code

        if error_code is not None:
            super().__init__(f"FL2K error: {error_code.name}")
        else:
            super().__init__(f"FL2K error: {msg}")            
        
# Define structure fl2k_data_info
class DataInfo(ctypes.Structure):
    _fields_ = [
        ("ctx", ctypes.py_object),
        ("underflow_cnt", c_uint32),
        ("len", c_uint32),
        ("using_zerocopy", c_int),
        ("device_error", c_int),
        ("sampletype_signed", c_int),
        ("r_buf", c_char_p),
        ("g_buf", c_char_p),
        ("b_buf", c_char_p)
    ]

def check_error_code(result, func, args):
    arg_str = ', '.join(map(str, args))
    
    # if return code not in enum then return as-is
    if not isinstance(result, int) or result not in EnumError:
        log.debug(f'{func.__name__}({arg_str}) returned {result}')
        return result  

    error_code = EnumError(result)
    log.debug(f'{func.__name__}({arg_str}) returned {error_code}')

    if result < 0:
        raise Fl2kError(error_code=error_code)
    
    return error_code

BUF_LEN  = (1280 * 1024)
XFER_LEN = (BUF_LEN * 3)

# Define pointer types
DevPtr = c_void_p
TxCb = ctypes.CFUNCTYPE(None, POINTER(DataInfo))

lib = load_library()

# FL2K_API uint32_t fl2k_get_device_count(void);
f = lib.fl2k_get_device_count
f.restype = c_uint32
f.errcheck = check_error_code

# FL2K_API const char* fl2k_get_device_name(uint32_t index);
f = lib.fl2k_get_device_name
f.restype = c_char_p
f.argtypes = [c_uint32]
f.errcheck = check_error_code

# FL2K_API int fl2k_open(fl2k_dev_t **dev, uint32_t index);
f = lib.fl2k_open
f.restype = c_int
f.argtypes = [POINTER(DevPtr), c_uint32]
f.errcheck = check_error_code

# FL2K_API int fl2k_close(fl2k_dev_t *dev);
f = lib.fl2k_close
f.restype = c_int
f.argtypes = [DevPtr]
f.errcheck = check_error_code

# FL2K_API int fl2k_set_sample_rate(fl2k_dev_t *dev, uint32_t target_freq);
f = lib.fl2k_set_sample_rate
f.restype = c_int
f.argtypes = [DevPtr, c_uint32]
f.errcheck = check_error_code

# FL2K_API uint32_t fl2k_get_sample_rate(fl2k_dev_t *dev);
f = lib.fl2k_get_sample_rate
f.restype = c_uint32
f.argtypes = [DevPtr]
f.errcheck = check_error_code

# FL2K_API int fl2k_start_tx(fl2k_dev_t *dev, fl2k_tx_cb_t cb, void *ctx, uint32_t buf_num);
f = lib.fl2k_start_tx
f.restype = c_int
f.argtypes = [DevPtr, TxCb, ctypes.py_object, c_uint32]
f.errcheck = check_error_code 

# FL2K_API int fl2k_stop_tx(fl2k_dev_t *dev);
f = lib.fl2k_stop_tx
f.restype = c_int
f.argtypes = [DevPtr]
f.errcheck = check_error_code

# FL2K_API int fl2k_i2c_read(fl2k_dev_t *dev, uint8_t i2c_addr, uint8_t reg_addr, uint8_t *data);
f = lib.fl2k_i2c_read
f.restype = c_int
f.argtypes = [DevPtr, c_uint8, c_uint8, POINTER(c_uint8)]
f.errcheck = check_error_code

# FL2K_API int fl2k_i2c_write(fl2k_dev_t *dev, uint8_t i2c_addr, uint8_t reg_addr, uint8_t *data);
f = lib.fl2k_i2c_write
f.restype = c_int
f.argtypes = [DevPtr, c_uint8, c_uint8, POINTER(c_uint8)]
f.errcheck = check_error_code
