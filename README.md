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

![Screenshot 2024-12-20 155212](https://github.com/user-attachments/assets/4a70291f-d079-4228-93b3-5634f96b37ce)
