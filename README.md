# pyfl2k

A Python wrapper for the [osmo-fl2k](https://osmocom.org/projects/osmo-fl2k/wiki) library that turns cheap FL2000 based USB-VGA adapters into high speed DACs. Three channels (R, G, B) are supported and up to 157 MS/s each can be achieved in C.

Windows and Linux have been tested, but achievable performance will depend on the host system. Being Python, you probably want to use this for lower sample rates if you're generating data in real time (e.g. < 10 MS/s).

# Usage

Make sure you've downloaded and installed [osmo-fl2k](https://osmocom.org/projects/osmo-fl2k/wiki). For Windows, make sure the `libosmo-fl2k.dll` file is in your `PATH` (you can place it in the same directory as your Python script).

All the libosmo-fl2k library functions are provided in a Pythonic interface and basic usage looks like this:

```python
import fl2k

fl = fl2k.Fl2k()
fl.open()

def callback(data_info):
    # write fl2k.BUF_LEN bytes to the R buffer
    data_info.contents.r_buf = ...

fl.start_tx_callback(callback)
fl.set_sample_rate(10e6)

# sleep or generate more data

fl.stop_tx_callback()
```

See `test_callback.py` for another example.

An async interface is also provided and works like this:

```python
import asyncio
import fl2k

async def start():
    fl = fl2k.Fl2k().open()

    fl.start().set_sample_rate(10e6)

    while fl.ready():
        # populate R, G and B buffers with fl2k.BUF_LEN bytes of data each
        await fl.write(r_buffer=..., g_buffer=..., b_buffer=...)

    fl.stop()

asyncio.run(start())
```

The advantage here is that other tasks can be executed instead of having to sleep. See `test_async.py` for another example.

# Sample output

A basic sine wave generator is in `test_async.py` and can produce quadrature sine waves using two channels:
![ScreenImg](https://github.com/user-attachments/assets/a0c1aa43-331f-4c79-9267-df6ac945e604)

# Issues

I've encountered issues with my particular device where the output seems to stop after several seconds to minutes, with no indication on the software side (errors or even crashes). For example, running the official test application `fl2k_test -s 80e6` produces this output:

```
real sample rate: 80005603 current PPM: 70 cumulative PPM: 60
real sample rate: 80005530 current PPM: 69 cumulative PPM: 61
real sample rate: 88466679 current PPM: 105834 cumulative PPM: 6290
```

Monitoring the output of the fl2k device on an oscilloscope shows a clear signal until the jump in PPM value when it disappears. I have also replicated this in other software, like [fl2k_signal_generator](https://github.com/l29ah/fl2k_signal_generator).

It seems to happen more often on slower computers and with higher sample rates. I suspect either a hardware or library issue is responsible.
