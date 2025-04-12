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

# === Visualizer Parameters ===
MAX_FREQ = 2000          # Top frequency mapped to last LED
FADE_DECAY = 0.8         # Trail fade (0.8 = fast decay)
INTENSITY_SCALE = 3.0    # Boost perceived volume
MAX_BRIGHTNESS = 100     # Cap brightness per channel
MIN_DB_THRESHOLD = 0.05  # NEW: minimum band energy to light an LED

led_levels = [0.0] * LED_COUNT

def wheel(pos):
    pos = 255 - pos
    if pos < 85:
        return (255 - pos * 3, 0, pos * 3)
    if pos < 170:
        pos -= 85
        return (0, pos * 3, 255 - pos * 3)
    pos -= 170
    return (pos * 3, 255 - pos * 3, 0)

def update_leds_spectrum(magnitude, freqs):
    global led_levels

    num_leds = strip.numPixels()
    freq_step = MAX_FREQ / num_leds

    # Ignore DC component
    magnitude[0] = 0

    # Normalize
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
        level = level ** 0.5  # Adjust perception
        level *= INTENSITY_SCALE

        # Apply threshold
        if level < MIN_DB_THRESHOLD:
            level = 0.0
        else:
            level = min(level, 1.0)

        # Fade-down logic
        if level < led_levels[i]:
            led_levels[i] *= FADE_DECAY
        else:
            led_levels[i] = level

        # Map color and brightness
        base_color = wheel(int(i * 256 / num_leds))
        r = min(int(base_color[0] * led_levels[i]), MAX_BRIGHTNESS)
        g = min(int(base_color[1] * led_levels[i]), MAX_BRIGHTNESS)
        b = min(int(base_color[2] * led_levels[i]), MAX_BRIGHTNESS)

        strip.setPixelColor(i, Color(r, g, b))

    strip.show()

def audio_callback(indata, frames, time, status):
    audio_data = indata[:, 0] * np.hanning(len(indata))
    fft_data = fftpack.fft(audio_data)
    fft_freq = fftpack.fftfreq(len(audio_data), 1.0 / samplerate)
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    freqs = fft_freq[:len(fft_freq)//2]

    update_leds_spectrum(magnitude, freqs)

def main():
    print("Spectrum visualizer with thresholding and fade. Ctrl+C to exit.")
    try:
        with sd.InputStream(device=0,
                            channels=1,
                            samplerate=samplerate,
                            blocksize=blocksize,
                            callback=audio_callback):
            while True:
                sd.sleep(1000)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

if __name__ == "__main__":
    main()
