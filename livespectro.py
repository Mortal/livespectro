import numpy as np
import pasimple

# Audio attributes for the recording
fmt = pasimple.PA_SAMPLE_FLOAT32LE
sample_width = pasimple.format2width(fmt)
nchannels = 1
sample_rate = 48000
# nsamples = 2**15
# seconds = nsamples / sample_rate
seconds = 0.2
nsamples = int(sample_rate * seconds)

win = np.hanning(nsamples)
yscale = sample_rate / len(win)


colors = [
    "\x1b[0m",
    "\x1b[0;32m",
    "\x1b[0;32;1m",
    "\x1b[0;33;1m",
    "\x1b[0;35;1m",
    "\x1b[0;35m",
    "\x1b[0;31m",
    "\x1b[0;31;1m",
]
chars = ['.', '1', '2', '3', 'a', 'b', 'c', '>']
steps = [-48, -42, -36, -30, -24, -18, -12]
assert len(chars) == len(colors) == len(steps) + 1

wrapon = "\x1b[?7h"
wrapoff = "\x1b[?7l"


def colorize(db: np.ndarray):
    c = colors[0]
    yield c
    for v in db:
        i = sum(s < v for s in steps)
        if c != colors[i]:
            c = colors[i]
            yield c
        yield chars[i]


try:
    print(wrapoff, end="")
    with pasimple.PaSimple(pasimple.PA_STREAM_RECORD, fmt, nchannels, sample_rate) as pa:
        num_bytes = int(nchannels * sample_width * nsamples)
        for _ in range(int(1000/seconds)):
            audio_data_bytes = pa.read(num_bytes)
            audio_data = np.frombuffer(audio_data_bytes, dtype={pasimple.PA_SAMPLE_FLOAT32LE: np.float32}[fmt])
            spec = np.fft.rfft(audio_data * win) / nsamples
            psd = np.abs(spec)
            db = 10 * np.log10(psd)
            print("".join(colorize(db)), flush=True)
except KeyboardInterrupt:
    pass
finally:
    print(wrapon, end="", flush=True)
