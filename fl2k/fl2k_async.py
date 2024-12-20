import logging
import ctypes
import asyncio
from typing import Optional, Self
from queue import Queue, Empty
from threading import Event
from .fl2k_base import Fl2kBase   
from .libosmo_fl2k import BUF_LEN, Fl2kError


log = logging.getLogger(__name__)

class Fl2kAsync(Fl2kBase):
    def __init__(self, loop=None):
        super().__init__()
        self.loop = loop if loop else asyncio.get_event_loop()        
        self.running = Event()

        # queues for R, G, B channels
        self.queue_r = Queue(maxsize=1)
        self.queue_g = Queue(maxsize=1)
        self.queue_b = Queue(maxsize=1)

    def _callback(self, data_info_p) -> None:
        '''
        Internal callback to get data from the queues and pass it to libosmo-fl2k
        '''
        if not self.running.is_set():
            log.debug('aborting callback: running is False')
            return
        
        info = data_info_p.contents

        if info.underflow_cnt:
            log.warning(f"underflow count: {info.underflow_cnt}")

        if info.device_error:
            log.error(f"device error, stopping TX")
            self.running.clear()
            self._clear_queues() # clear to unblock the wait() mathod
            return
        
        # get data for each channel from queue and write to buffers
        did_write = False
        for (buf_name, queue) in zip(('r_buf', 'g_buf', 'b_buf'), 
                                     (self.queue_r, self.queue_g, self.queue_b)):
            try:
                buffer = queue.get_nowait()
            except Empty:
                log.debug(f'queue {buf_name} empty')
                continue

            log.debug(f'got buffer from queue {buf_name}')

            setattr(info, buf_name, buffer)
            did_write = True       

        if not did_write:
            log.warning('buffers all empty, send data faster')
            return

        log.debug(f'sent all data')

    def _clear_queues(self) -> None:
        for queue in (self.queue_r, self.queue_g, self.queue_b):
            try:
                # only one element max so this should always work
                queue.get_nowait()
            except Empty:
                pass 

    def start(self) -> Self:
        '''
        Enable transmitter. Reads data put in the queues by `write()` and sends it to the device.
        '''
        log.debug('starting TX and clearing queues')
        self.running.set()    
        self._clear_queues()       
        self.start_tx_callback(self._callback)

        return self

    def stop(self) -> Self:
        '''
        Stop the transmitter.
        '''
        log.debug('stopping TX and clearing queues')
        self.running.clear()
        self._clear_queues()      # clear to unblock the wait() mathod
        self.stop_tx_callback()  # stop the TX callback

        return self
        
    async def write(self, 
                    r_buffer: Optional[bytearray | memoryview]=None, 
                    g_buffer: Optional[bytearray | memoryview]=None, 
                    b_buffer: Optional[bytearray | memoryview]=None) -> Self:
        '''
        Write data to the transmission queues.
        One or more of the R, G, B buffers must be provided.
        Buffers must be of length `BUF_LEN` and must be `bytearray` or `memoryview` objects.
        '''
        if not any((r_buffer, g_buffer, b_buffer)):
            raise Fl2kError('no buffers to write')
        
        tasks = []
        for (buffer, queue) in zip((r_buffer, g_buffer, b_buffer), 
                                   (self.queue_r, self.queue_g, self.queue_b)):
            if buffer is None:
                continue
            
            if(len(buffer) != BUF_LEN):
                raise Fl2kError(f'buffer length is {len(buffer)} but should be {BUF_LEN}')
            
            # convert buffer to c pointer
            dtype = ctypes.c_char * len(buffer)
            data = ctypes.cast(dtype.from_buffer(buffer), ctypes.c_char_p)

            log.debug(f'writing {len(buffer)} byte buffer to queue')
            tasks.append(self.loop.run_in_executor(None, queue.put, data))

        await asyncio.gather(*tasks)
        log.debug(f'finished writing buffers to queues')

        return self

    def ready(self) -> bool:
        '''
        Check if device is ready to transmit data. False when shutting down.
        '''
        return self.running.is_set()

async def test_async():
    # make a simple square wave at 1/4 sample rate
    buffer = bytearray(BUF_LEN)
    for i in range(0, BUF_LEN, 4):
        buffer[i] = 0xFF
        buffer[i + 1] = 0xFF

    fl2k = Fl2kAsync().open()
    fl2k.start().set_sample_rate(10e6)

    # repeat the data n times
    n = 20
    i = 0

    while fl2k.ready():
        i += 1

        if i >= n:
            fl2k.stop()

        await fl2k.write(buffer)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    asyncio.run(test_async())