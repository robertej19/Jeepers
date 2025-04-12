import sounddevice as sd
import numpy as np
import scipy.fftpack as fftpack
from rpi_ws281x import Adafruit_NeoPixel, Color

# === LED Setup ===
LED_COUNT = 32
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 80
LED_INVERT = False

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ,
                          LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# === Audio Setup ===
samplerate = 44100
block_duration = 0.05
blocksize = int(samplerate * block_duration)

# === Color helper ===
def wheel(pos):
    pos = 255 - pos
    if pos < 85:
        return Color(255 - pos * 3, 0, pos * 3)
    if pos < 170:
        pos -= 85
        return Color(0, pos * 3, 255 - pos * 3)
    pos -= 170
    return Color(pos * 3, 255 - pos * 3, 0)

# === LED update: only dominant frequency ===
def update_led_dominant(magnitude, freqs):
    num_leds = strip.numPixels()
    max_freq = 2000  # Hz, top frequency mapped to last LED

    # Normalize
    if np.max(magnitude) == 0:
        return
    magnitude /= np.max(magnitude)

    # Find peak frequency and its intensity
    peak_idx = np.argmax(magnitude)
    peak_freq = freqs[peak_idx]
    intensity = magnitude[peak_idx]

    # Map frequency to LED index
    led_idx = int((peak_freq / max_freq) * num_leds)
    led_idx = min(max(led_idx, 0), num_leds - 1)

    # Brightness scaling
    brightness = int(np.clip(intensity ** 0.5, 0, 1) * 255)

    # Get color from wheel
    color = wheel(int(led_idx * 256 / num_leds))
    scaled_color = Color(
        int(((color >> 16) & 0xff) * brightness / 255),
        int(((color >> 8) & 0xff) * brightness / 255),
        int((color & 0xff) * brightness / 255)
    )

    # Clear strip, light only 1 LED
    for i in range(num_leds):
        strip.setPixelColor(i, scaled_color if i == led_idx else Color(0, 0, 0))
    strip.show()

# === Audio Callback ===
def audio_callback(indata, frames, time, status):
    audio_data = indata[:, 0] * np.hanning(len(indata))
    fft_data = fftpack.fft(audio_data)
    fft_freq = fftpack.fftfreq(len(audio_data), 1.0 / samplerate)
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    freqs = fft_freq[:len(fft_freq)//2]

    update_led_dominant(magnitude, freqs)

# === Main ===
def main():
    print("Single-frequency LED visualizer active. Ctrl+C to stop.")
    try:
        with sd.InputStream(device=0,
                            channels=1,
                            samplerate=samplerate,
                            blocksize=blocksize,
                            callback=audio_callback):
            while True:
                sd.sleep(1000)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

if __name__ == "__main__":
    main()
