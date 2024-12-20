import time
import logging
import ctypes
from fl2k import Fl2k, BUF_LEN, Fl2kError


log = logging.getLogger(__name__)

buffer = ctypes.create_string_buffer(BUF_LEN)
buffer[0] = b'a'
buffer[1] = b'b'
buffer[2] = b'c'

def tx_callback(data_info):
    print("In callback")

    print(f"  Context: {data_info.contents.ctx}")
    print(f"  Underflow count: {data_info.contents.underflow_cnt}")
    print(f"  Buffer length: {data_info.contents.len}")
    print(f"  Using zerocopy: {data_info.contents.using_zerocopy}")
    print(f"  Device error: {data_info.contents.device_error}")
    print(f"  Sampletype signed: {data_info.contents.sampletype_signed}")

    data_info.contents.r_buf = ctypes.cast(ctypes.pointer(buffer), ctypes.c_char_p)

def test():
    logging.basicConfig(level=logging.INFO)

    fl2k = Fl2k()

    device_count = Fl2k.get_device_count()
    log.info(f"Device count: {device_count}")

    if device_count > 0:
        device_name = Fl2k.get_device_name(0)
        log.info(f"Device name: {device_name}")

        fl2k.open()

        log.info("Starting TX...")
        context = dict(foo='bar')
        fl2k.start_tx_callback(tx_callback, ctx=context)

        fl2k.set_sample_rate(10_000_000)
        sample_rate = fl2k.get_sample_rate()
        log.info(f"Sample rate: {sample_rate}")
        
        time.sleep(0.1)

        log.info("Stopping TX...")
        fl2k.stop_tx_callback()

        fl2k.close()
 
if __name__ == "__main__":
    test()