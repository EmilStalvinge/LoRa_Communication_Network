import pycom
import time

def clamp01(x: int) -> int:
    return max(0, min(1, x))

def main():
    pycom.heartbeat(False)

    t = 0.0
    while True:
        red   = int(0x15 * clamp01(1 - t if t < 2 else t - 2)) << 16
        green = int(0x15 * clamp01(1 - abs(t - 1))) << 8
        blue  = int(0x15 * clamp01(1 - abs(t - 2)))

        color = red | green | blue

        if t > 3:
            t = 0.0

        pycom.rgbled(color)
        t += 0.01
        time.sleep(0.01)


if __name__ == "__main__":
    main()