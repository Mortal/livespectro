import argparse
import shutil
import subprocess

from livespectro import RecordingSettings, live_spectro


parser = argparse.ArgumentParser()


def main() -> None:
    args = parser.parse_args()
    prog = shutil.which("notify-send")

    settings = RecordingSettings(sample_rate=24000, seconds=0.2)
    brum_freq = 10
    t = 0
    f = 0
    time_window = 10
    stable_state: bool | None = None

    if prog is None:
        raise SystemExit("notify-send is not installed")

    for db in live_spectro(settings):
        # v = db[brum_freq - 1] * .25 + db[brum_freq] * .5 + db[brum_freq + 1] * .25
        v = db[brum_freq]
        b = v > -18 
        if b:
            t = min(time_window, t + 1)
            f = max(0, f - 1)
        else:
            f = min(time_window, f + 1)
            t = max(0, t - 1)
        print(b, t, f, stable_state, v)
        if stable_state is True and t < time_window // 2:
            message = "HEADPHONES OFF"
            print(message)
            subprocess.call((prog, message))
            stable_state = False
        elif stable_state is False and t == time_window:
            message = "HEADPHONES ON"
            print(message)
            subprocess.call((prog, message))
            stable_state = True
        elif f == 10:
            stable_state = False
        elif t == 10:
            stable_state = True


if __name__ == "__main__":
    main()
