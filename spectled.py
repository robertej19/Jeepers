import sounddevice as sd
import numpy as np
import scipy.fftpack as fftpack
from rpi_ws281x import Adafruit_NeoPixel, Color

# === LED Configuration ===
LED_COUNT = 32
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 50
LED_INVERT = False

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ,
                          LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# === Audio Configuration ===
samplerate = 44100
block_duration = 0.05
blocksize = int(samplerate * block_duration)

# === Visualization Parameters ===
MAX_FREQ = 2000          # Top frequency mapped to last LED
FADE_DECAY = 0.8         # Decay factor per frame
INTENSITY_SCALE = 3.0    # Adjust sensitivity to sound level
MAX_BRIGHTNESS = 100     # Limit per-channel RGB value

# Track per-LED brightness (linear 0–1 scale)
led_levels = [0.0] * LED_COUNT

# === Color helper: rainbow mapping ===
def wheel(pos):
    pos = 255 - pos
    if pos < 85:
        return (255 - pos * 3, 0, pos * 3)
    if pos < 170:
        pos -= 85
        return (0, pos * 3, 255 - pos * 3)
    pos -= 170
    return (pos * 3, 255 - pos * 3, 0)

# === Update LEDs based on full spectrum ===
def update_leds_spectrum(magnitude, freqs):
    global led_levels

    num_leds = strip.numPixels()
    freq_step = MAX_FREQ / num_leds

    # Ignore DC offset
    magnitude[0] = 0
    if np.max(magnitude) == 0:
        return

    magnitude = magnitude / np.max(magnitude)

    for i in range(num_leds):
        # Frequency range for this LED
        f_start = i * freq_step
        f_end = (i + 1) * freq_step
        band = magnitude[(freqs >= f_start) & (freqs < f_end)]

        # Mean intensity in this band
        level = np.mean(band) if len(band) else 0.0
        level = level ** 0.5  # Adjust scaling
        level *= INTENSITY_SCALE

        # Clamp between 0 and 1
        level = max(0.0, min(level, 1.0))

        # Fade down if lower than previous, otherwise update
        if level < led_levels[i]:
            led_levels[i] *= FADE_DECAY
        else:
            led_levels[i] = level

        # Map to color
        base_color = wheel(int(i * 256 / num_leds))
        r = int(base_color[0] * led_levels[i])
        g = int(base_color[1] * led_levels[i])
        b = int(base_color[2] * led_levels[i])

        # Cap max brightness
        r = min(r, MAX_BRIGHTNESS)
        g = min(g, MAX_BRIGHTNESS)
        b = min(b, MAX_BRIGHTNESS)

        strip.setPixelColor(i, Color(r, g, b))

    strip.show()

# === Audio Callback ===
def audio_callback(indata, frames, time, status):
    audio_data = indata[:, 0] * np.hanning(len(indata))
    fft_data = fftpack.fft(audio_data)
    fft_freq = fftpack.fftfreq(len(audio_data), 1.0 / samplerate)
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    freqs = fft_freq[:len(fft_freq)//2]

    update_leds_spectrum(magnitude, freqs)

# === Main Loop ===
def main():
    print("Real-time LED Spectrum Visualizer (0–2000 Hz). Ctrl+C to stop.")
    try:
        with sd.InputStream(device=0,
                            channels=1,
                            samplerate=samplerate,
                            blocksize=blocksize,
                            callback=audio_callback):
            while True:
                sd.sleep(1000)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

if __name__ == "__main__":
    main()
