import sounddevice as sd
import numpy as np
import scipy.fftpack as fftpack
from rpi_ws281x import Adafruit_NeoPixel, Color

# === LED Configuration ===
LED_COUNT = 32
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 80
LED_INVERT = False

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ,
                          LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# === Audio Configuration ===
samplerate = 44100
block_duration = 0.05
blocksize = int(samplerate * block_duration)

# === LED State: list of (R, G, B) tuples ===
led_state = [(0, 0, 0)] * LED_COUNT

# === Helper: rainbow color wheel ===
def wheel(pos):
    pos = 255 - pos
    if pos < 85:
        return (255 - pos * 3, 0, pos * 3)
    if pos < 170:
        pos -= 85
        return (0, pos * 3, 255 - pos * 3)
    pos -= 170
    return (pos * 3, 255 - pos * 3, 0)

# === LED Update: top 3 frequencies + fade ===
def update_leds_top3(magnitude, freqs):
    global led_state

    num_leds = strip.numPixels()
    max_freq = 4000

    if np.max(magnitude) == 0:
        return
    magnitude = magnitude / np.max(magnitude)

    # Find top 3 peak frequency indices
    top_indices = np.argpartition(magnitude, -3)[-3:]
    top_indices = top_indices[np.argsort(magnitude[top_indices])[::-1]]  # Sorted descending

    # Decay all LEDs (fade out trail)
    fade_factor = 0.9
    led_state = [(int(r * fade_factor), int(g * fade_factor), int(b * fade_factor)) for r, g, b in led_state]

    for idx in top_indices:
        freq = freqs[idx]
        intensity = magnitude[idx]

        # Map to LED
        led_idx = int((freq / max_freq) * num_leds)
        led_idx = min(max(led_idx, 0), num_leds - 1)

        # Get color from wheel based on position
        base_color = wheel(int(led_idx * 256 / num_leds))
        scaled_color = tuple(int(c * (intensity ** 0.5)) for c in base_color)

        # Add (boost) color to current state (limit to 255)
        r = min(255, led_state[led_idx][0] + scaled_color[0])
        g = min(255, led_state[led_idx][1] + scaled_color[1])
        b = min(255, led_state[led_idx][2] + scaled_color[2])
        led_state[led_idx] = (r, g, b)

    # Update strip
    for i in range(num_leds):
        r, g, b = led_state[i]
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
    print("LED visualizer (top 3 frequencies + fade trail) running. Ctrl+C to stop.")
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
