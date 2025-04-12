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

# LED state buffer for fading
led_state = [(0, 0, 0)] * LED_COUNT

# === Helper: Color Wheel ===
def wheel(pos):
    pos = 255 - pos
    if pos < 85:
        return (255 - pos * 3, 0, pos * 3)
    if pos < 170:
        pos -= 85
        return (0, pos * 3, 255 - pos * 3)
    pos -= 170
    return (pos * 3, 255 - pos * 3, 0)

# === Update LEDs ===
def update_leds_top3(magnitude, freqs):
    global led_state

    num_leds = strip.numPixels()
    max_freq = 2000  # NEW: Reduced max frequency
    max_brightness = 100  # NEW: Cap RGB brightness

    # Ignore DC (0 Hz) component
    magnitude[0] = 0

    if np.max(magnitude) == 0:
        return
    magnitude = magnitude / np.max(magnitude)

    # Get top 3 peak bins
    top_indices = np.argpartition(magnitude, -3)[-3:]
    top_indices = top_indices[np.argsort(magnitude[top_indices])[::-1]]

    # Fade all LEDs
    fade_factor = 0.85
    led_state = [(int(r * fade_factor), int(g * fade_factor), int(b * fade_factor)) for r, g, b in led_state]

    for idx in top_indices:
        freq = freqs[idx]
        intensity = magnitude[idx]

        # Map to LED index
        led_idx = int((freq / max_freq) * num_leds)
        if led_idx < 0 or led_idx >= num_leds:
            continue

        base_color = wheel(int(led_idx * 256 / num_leds))
        scale = intensity ** 0.5

        scaled_color = tuple(min(max_brightness, int(c * scale)) for c in base_color)

        # Add scaled color to current state
        r = min(max_brightness, led_state[led_idx][0] + scaled_color[0])
        g = min(max_brightness, led_state[led_idx][1] + scaled_color[1])
        b = min(max_brightness, led_state[led_idx][2] + scaled_color[2])
        led_state[led_idx] = (r, g, b)

    for i, (r, g, b) in enumerate(led_state):
        strip.setPixelColor(i, Color(r, g, b))
    strip.show()

# === Audio Callback ===
def audio_callback(indata, frames, time, status):
    audio_data = indata[:, 0] * np.hanning(len(indata))
    fft_data = fftpack.fft(audio_data)
    fft_freq = fftpack.fftfreq(len(audio_data), 1.0 / samplerate)
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    freqs = fft_freq[:len(fft_freq)//2]

    update_leds_top3(magnitude, freqs)

# === Main Loop ===
def main():
    print("LED visualizer (Top 3 with trail, capped brightness, 0–2kHz). Ctrl+C to stop.")
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
