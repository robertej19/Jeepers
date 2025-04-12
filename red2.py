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
FREQ_MIN = 20
FREQ_MAX = 4000
FADE_DECAY = 0.5
MAX_BRIGHTNESS = 50

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

# === Generate log-spaced frequency band edges ===
def generate_log_freq_edges(f_min, f_max, num_bands):
    log_start = np.log2(f_min)
    log_end = np.log2(f_max)
    log_edges = np.linspace(log_start, log_end, num_bands + 1)
    freq_edges = 2 ** log_edges
    return freq_edges

# === LED update using log frequency bands ===
def update_leds_log_bands(magnitude, freqs):
    global led_levels

    num_leds = strip.numPixels()
    freq_edges = generate_log_freq_edges(FREQ_MIN, FREQ_MAX, num_leds)

    magnitude[0] = 0  # Remove DC
    if np.max(magnitude) == 0:
        return
    magnitude = magnitude / np.max(magnitude)

    # Compute intensity per LED band
    levels = np.zeros(num_leds)
    for i in range(num_leds):
        f_start = freq_edges[i]
        f_end = freq_edges[i + 1]
        band = magnitude[(freqs >= f_start) & (freqs < f_end)]
        levels[i] = np.mean(band) if len(band) else 0.0

    # Get top 5 bands
    top_indices = np.argpartition(levels, -5)[-5:]
    top_indices = top_indices[np.argsort(levels[top_indices])[::-1]]

    # Normalize relative to top level
    max_level = levels[top_indices[0]] if levels[top_indices[0]] > 0 else 1
    relative_levels = {i: levels[i] / max_level for i in top_indices}

    for i in range(num_leds):
        if i in relative_levels:
            target_level = relative_levels[i]
            led_levels[i] = max(led_levels[i], target_level)
        else:
            led_levels[i] *= FADE_DECAY
            if led_levels[i] < 0.01:
                led_levels[i] = 0.0

        base_color = wheel(int(i * 256 / num_leds))
        r = min(int(base_color[0] * led_levels[i]), MAX_BRIGHTNESS)
        g = min(int(base_color[1] * led_levels[i]), MAX_BRIGHTNESS)
        b = min(int(base_color[2] * led_levels[i]), MAX_BRIGHTNESS)

        strip.setPixelColor(i, Color(r, g, b))

    strip.show()

# === Audio Callback ===
def audio_callback(indata, frames, time, status):
    audio_data = indata[:, 0] * np.hanning(len(indata))
    fft_data = fftpack.fft(audio_data)
    fft_freq = fftpack.fftfreq(len(audio_data), 1.0 / samplerate)
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    freqs = fft_freq[:len(fft_freq)//2]

    update_leds_log_bands(magnitude, freqs)

# === Main Loop ===
def main():
    print(f"Top 5 LED bands (log spaced from {FREQ_MIN}–{FREQ_MAX} Hz). Ctrl+C to stop.")
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
