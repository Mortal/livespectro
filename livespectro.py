import subprocess
from dataclasses import dataclass
from typing import Iterator, Iterable, Sequence

import numpy as np


@dataclass
class RecordingSettings:
    sample_rate: int = 24000
    seconds: float = 0.2

    @property
    def format_parec(self) -> str:
        return "float32ne"

    @property
    def format_np(self) -> type:
        return np.float32

    @property
    def sample_width(self) -> int:
        return 4

    @property
    def nchannels(self) -> int:
        return 1

    @property
    def nsamples(self) -> int:
        return int(self.sample_rate * self.seconds)

    @property
    def yscale(self) -> float:
        return self.sample_rate / self.nsamples

    @property
    def num_bytes(self) -> int:
        return int(self.nchannels * self.sample_width * self.nsamples)


def live_spectro(settings: RecordingSettings, count: int = -1) -> Iterator[np.ndarray]:
    win = np.hanning(settings.nsamples)
    assert len(win) == settings.nsamples

    cmdline = [
        "parec",
        f"--latency={settings.num_bytes}",
        f"--channels={settings.nchannels}",
        f"--format={settings.format_parec}",
        "-r",
        "--raw",
        f"--rate={settings.sample_rate}",
    ]

    with subprocess.Popen(cmdline, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE) as p:
        assert p.stdout is not None
        try:
            for _ in (range(count) if count >= 0 else iter(lambda: 1, 0)):
                audio_data_bytes = p.stdout.read(settings.num_bytes)
                audio_data: np.ndarray = np.frombuffer(audio_data_bytes, dtype=settings.format_np)
                spec = np.fft.rfft(audio_data * win) / settings.nsamples
                psd = np.abs(spec)
                zero = psd == 0
                psd[zero] = 1
                db = 10 * np.log10(psd)
                db[zero] = -np.inf
                yield db
            p.stdout.close()
            p.terminate()
        except KeyboardInterrupt:
            pass


def colorize(db: np.ndarray, colors: Sequence[str], chars: Sequence[str], steps: Sequence[int | float]) -> Iterator[str]:
    assert len(chars) == len(colors) == len(steps) + 1
    c = colors[0]
    yield c
    for v in db:
        i = sum(s < v for s in steps)
        if c != colors[i]:
            c = colors[i]
            yield c
        yield chars[i]


spectro_colors = [
    "\x1b[0m",
    "\x1b[0;32m",
    "\x1b[0;32;1m",
    "\x1b[0;33;1m",
    "\x1b[0;35;1m",
    "\x1b[0;35m",
    "\x1b[0;31m",
    "\x1b[0;31;1m",
]
spectro_chars = [".", "1", "2", "3", "a", "b", "c", ">"]
spectro_steps = [-48, -42, -36, -30, -24, -18, -12]

wrapon = "\x1b[?7h"
wrapoff = "\x1b[?7l"
cursorvis = "\x1b[?25h"
cursorinvis = "\x1b[?25l"


def print_spectro_lines(dbs: Iterable[np.ndarray]) -> None:
    try:
        print(wrapoff + cursorinvis, end="")
        for db in dbs:
            print("\n" + "".join(colorize(db, spectro_colors, spectro_chars, spectro_steps)), flush=True, end="")
    finally:
        print(wrapon + cursorvis, end="", flush=True)


def main() -> None:
    settings = RecordingSettings(sample_rate=24000, seconds=0.2)
    print_spectro_lines(live_spectro(settings))


if __name__ == "__main__":
    main()
