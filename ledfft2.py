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

# === Helper Functions ===
def wheel(pos):
    pos = 255 - pos
    if pos < 85:
        return Color(255 - pos * 3, 0, pos * 3)
    if pos < 170:
        pos -= 85
        return Color(0, pos * 3, 255 - pos * 3)
    pos -= 170
    return Color(pos * 3, 255 - pos * 3, 0)

def update_leds(magnitude, freqs):
    num_leds = strip.numPixels()
    max_freq = 4000  # Most audio is below 4kHz
    freq_step = max_freq / num_leds

    # Normalize magnitude
    magnitude = magnitude / np.max(magnitude)

    for i in range(num_leds):
        freq_start = i * freq_step
        freq_end = (i + 1) * freq_step
        
        band = magnitude[(freqs >= freq_start) & (freqs < freq_end)]
        intensity = np.mean(band) if len(band) else 0
        
        # Adjust sensitivity here (raise to power to enhance lower sounds)
        intensity = np.clip(intensity ** 0.5, 0, 1)
        scaled_intensity = int(intensity * 255)
        
        # Skip lighting up very faint signals
        if scaled_intensity < 10:
            scaled_intensity = 0

        color = wheel(int(i * 256 / num_leds))
        
        scaled_color = Color(
            int(((color >> 16) & 0xff) * scaled_intensity / 255),
            int(((color >> 8) & 0xff) * scaled_intensity / 255),
            int((color & 0xff) * scaled_intensity / 255)
        )
        
        strip.setPixelColor(i, scaled_color)
    
    strip.show()

def audio_callback(indata, frames, time, status):
    audio_data = indata[:, 0] * np.hanning(len(indata))  # Hanning window reduces FFT artifacts
    
    fft_data = fftpack.fft(audio_data)
    fft_freq = fftpack.fftfreq(len(audio_data), 1.0 / samplerate)
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    freqs = fft_freq[:len(fft_freq)//2]

    update_leds(magnitude, freqs)

def main():
    print("Enhanced Audio-LED visualizer running. Press Ctrl+C to stop.")
    try:
        with sd.InputStream(device=0,
                            channels=1,
                            samplerate=samplerate,
                            blocksize=blocksize,
                            callback=audio_callback):
            while True:
                sd.sleep(1000)
    except KeyboardInterrupt:
        print("\nStopping visualization...")
    finally:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

if __name__ == "__main__":
    main()
