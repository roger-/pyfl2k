import ctypes
from collections.abc import Callable
from typing import Self
import logging
from .libosmo_fl2k import lib, Fl2kError, DevPtr, TxCb, DataInfo, BUF_LEN


log = logging.getLogger(__name__)

class Fl2kBase:
    def __init__(self):
        self.handle = DevPtr() 
        self.cb_tx = None

    @staticmethod
    def get_device_count() -> int:
        '''
        Get the number of available devices
        '''
        count = lib.fl2k_get_device_count()

        return count

    @staticmethod
    def get_device_name(index: int=0) -> str:
        '''
        Get name of device with given index
        '''
        name = lib.fl2k_get_device_name(index)

        if not name:
            raise Fl2kError(msg=f'device {index} not found')
        
        return name.decode()

    def open(self, index: int=0) -> Self:
        log.info(f'opening device {index}: {Fl2kBase.get_device_name(index)}')
        lib.fl2k_open(ctypes.byref(self.handle), index)

        return self

    def close(self) -> Self:
        lib.fl2k_close(self.handle)
        self.handle = DevPtr() 
        log.info(f'closed device') 

        return self

    def set_sample_rate(self, target_freq: int | float) -> Self:
        '''
        Set sample rate (in Hz) to value nearest to `target_freq` supported. Check with get_sample_rate()
        This should be called after TX has started.
        '''
        lib.fl2k_set_sample_rate(self.handle, int(target_freq))

        return self

    def get_sample_rate(self) -> int:
        '''
        Get current sample rate (in Hz)
        '''
        sample_rate = lib.fl2k_get_sample_rate(self.handle)

        return sample_rate

    def start_tx_callback(self, 
                          callback: Callable[[DataInfo], None], 
                          ctx: object=None, 
                          buf_num: int=0) -> Self:
        '''
        Start transmitting data using the callback function `callback`. 
        The callback function should take a single argument of type `DataInfo` and return nothing.
        `ctx` is an optional object that will be passed to the callback function.
        '''
        log.debug(f"Starting TX callback")

        self.cb_tx = TxCb(callback)
        lib.fl2k_start_tx(self.handle, self.cb_tx, ctx, buf_num)

        return self

    def stop_tx_callback(self) -> Self:
        '''
        Stop transmitting.
        '''
        log.debug(f"Stopping TX callback")

        lib.fl2k_stop_tx(self.handle)
        self.cb_tx = None

        return self

    def i2c_read(self, i2c_addr: int, reg_addr: int, data: list[int]) -> list[int]:
        data_arr = (ctypes.c_uint8 * 4)(*data)
        lib.fl2k_i2c_read(self.handle, i2c_addr, reg_addr, data_arr)

        return data

    def i2c_write(self, i2c_addr: int, reg_addr: int, data: list[int]) -> Self:
        data_arr = (ctypes.c_uint8 * 4)(*data)
        lib.fl2k_i2c_write(self.handle, i2c_addr, reg_addr, data_arr)

        return self

