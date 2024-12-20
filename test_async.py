import logging
import asyncio
import numpy as np
from fl2k import Fl2k, BUF_LEN, Fl2kError


def make_sine(freq, sample_rate, time_offset=0, phase=0, num_samples=BUF_LEN):
    t = np.arange(num_samples) / sample_rate + time_offset
    time_offset = t[-1] + 1 / sample_rate # starting time for next buffer

    x = 0.5 * np.sin(2 * np.pi * freq * t + phase) + 0.5
    x *= 255

    x = x.astype(np.uint8).tobytes() 

    return bytearray(x), time_offset

async def test_async():
    fl2k = Fl2k().open()
    fl2k.start().set_sample_rate(10e6)
    sample_rate = fl2k.get_sample_rate()

    time_offset = 0

    while fl2k.ready():
        try:
            buffer_r, time_offset = make_sine(0.1e6, sample_rate, time_offset)
            buffer_g, time_offset = make_sine(0.1e6, sample_rate, time_offset, phase=np.pi / 2)

            await fl2k.write( r_buffer=buffer_r, g_buffer=buffer_g)
        except Exception as e:
            fl2k.stop()
            break

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    asyncio.run(test_async())