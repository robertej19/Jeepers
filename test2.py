import sounddevice as sd
import numpy as np
import scipy.fftpack as fftpack
from rpi_ws281x import Adafruit_NeoPixel, Color
from collections import deque

# === LED Setup ===
LED_COUNT = 32
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 99
LED_INVERT = False

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ,
                          LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# === Audio Setup ===
samplerate = 44100
block_duration = 0.05
blocksize = int(samplerate * block_duration)

# === Frequency Filter Setting ===
FREQ_MIN = 800  # Hz, frequencies below this value will be ignored

# === Beat Detection Parameters ===
SENSITIVITY = 1  # Instantaneous energy must exceed average energy by this factor to register a beat
energy_history = deque(maxlen=2)  # Store energy values for the last few blocks

# === Color Helper ===
def wheel(pos):
    pos = 255 - pos
    if pos < 85:
        return Color(255 - pos * 3, 0, pos * 3)
    if pos < 170:
        pos -= 85
        return Color(0, pos * 3, 255 - pos * 3)
    pos -= 170
    return Color(pos * 3, 255 - pos * 3, 0)

# === LED Update: Only Dominant Frequency ===
def update_led_dominant(magnitude, freqs):
    num_leds = strip.numPixels()
    max_freq = 3000  # Hz, top frequency mapped to last LED

    # Normalize the magnitude to prevent division by zero
    if np.max(magnitude) == 0:
        return
    magnitude = magnitude / np.max(magnitude)

    # Filter out frequencies below the minimum threshold
    mask = freqs >= FREQ_MIN
    if not np.any(mask):
        return  # Nothing to display if all frequencies are filtered out

    # Apply the mask to get filtered arrays
    mag_filtered = magnitude[mask]
    freqs_filtered = freqs[mask]

    # Find the peak frequency within the filtered range and its intensity
    peak_idx = np.argmax(mag_filtered)
    peak_freq = freqs_filtered[peak_idx]
    intensity = mag_filtered[peak_idx]

    # Map frequency to LED index
    led_idx = int((peak_freq / max_freq) * num_leds)
    led_idx = min(max(led_idx, 0), num_leds - 1)

    # Scale brightness based on intensity (using square-root for smoother response)
    brightness = int(np.clip(intensity ** 0.5, 0, 1) * 255)

    # Get color from wheel and scale by brightness
    color = wheel(int(led_idx * 256 / num_leds))
    scaled_color = Color(
        int(((color >> 16) & 0xff) * brightness / 255),
        int(((color >> 8) & 0xff) * brightness / 255),
        int((color & 0xff) * brightness / 255)
    )

    # Clear strip and light only the LED corresponding to the peak frequency
    for i in range(num_leds):
        strip.setPixelColor(i, scaled_color if i == led_idx else Color(0, 0, 0))
    strip.show()

# === Audio Callback with Energy-Based Beat Detection ===
def audio_callback(indata, frames, time, status):
    global energy_history

    # Apply a Hanning window to the current audio block
    audio_data = indata[:, 0] * np.hanning(len(indata))
    
    # Compute instantaneous energy (mean square)
    instant_energy = np.sum(audio_data ** 2) / len(audio_data)
    energy_history.append(instant_energy)
    avg_energy = np.mean(energy_history) if energy_history else instant_energy

    # Check for a beat: only proceed if the energy exceeds threshold
    if instant_energy > SENSITIVITY * avg_energy:
        fft_data = fftpack.fft(audio_data)
        fft_freq = fftpack.fftfreq(len(audio_data), 1.0 / samplerate)
        magnitude = np.abs(fft_data[:len(fft_data) // 2])
        freqs = fft_freq[:len(fft_freq) // 2]
        update_led_dominant(magnitude, freqs)
    else:
        # Optionally, you could fade the LEDs here instead of doing nothing
        pass

# === Main Program ===
def main():
    print("Energy-based beat detection LED visualizer active. Ctrl+C to stop.")
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
        # Turn off all LEDs on exit
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

if __name__ == "__main__":
    main()
