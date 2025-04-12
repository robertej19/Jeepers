import sounddevice as sd
import numpy as np
import scipy.fftpack as fftpack
from rpi_ws281x import Adafruit_NeoPixel, Color

# === LED Setup ===
LED_COUNT = 32          # Number of LED pixels
LED_PIN = 18            # GPIO pin (PWM supported)
LED_FREQ_HZ = 800000    # Frequency (usually 800kHz)
LED_DMA = 10            # DMA channel
LED_BRIGHTNESS = 50     # LED brightness
LED_INVERT = False      # Signal inversion

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ,
                          LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()

# === Audio Setup ===
samplerate = 44100
block_duration = 0.05  # Smaller for more responsive LEDs
blocksize = int(samplerate * block_duration)

# === Color Wheel (rainbow spectrum) ===
def wheel(pos):
    pos = 255 - pos
    if pos < 85:
        return Color(255 - pos * 3, 0, pos * 3)
    if pos < 170:
        pos -= 85
        return Color(0, pos * 3, 255 - pos * 3)
    pos -= 170
    return Color(pos * 3, 255 - pos * 3, 0)

# === LED update from FFT ===
def update_leds(magnitude, freqs):
    num_leds = strip.numPixels()
    # Define frequency range (0 - 5000Hz)
    max_freq = 5000  
    freq_step = max_freq / num_leds
    
    for i in range(num_leds):
        # Find frequency band for each LED
        freq_start = i * freq_step
        freq_end = (i + 1) * freq_step
        
        # Find corresponding magnitudes
        band = magnitude[(freqs >= freq_start) & (freqs < freq_end)]
        
        # Calculate intensity (mean magnitude) for the band
        intensity = np.mean(band) if len(band) else 0
        
        # Normalize intensity to [0, 255]
        intensity = min(int(intensity / 5), 255)
        
        # Set LED color based on frequency position (rainbow)
        color = wheel(int(i * 256 / num_leds))
        
        # Scale brightness based on intensity
        scaled_color = Color(
            int((color >> 16 & 0xff) * intensity / 255),
            int((color >> 8 & 0xff) * intensity / 255),
            int((color & 0xff) * intensity / 255)
        )
        strip.setPixelColor(i, scaled_color)
    
    strip.show()

# === Audio callback ===
def audio_callback(indata, frames, time, status):
    audio_data = indata[:, 0]

    # FFT analysis
    fft_data = fftpack.fft(audio_data)
    fft_freq = fftpack.fftfreq(len(audio_data), 1.0 / samplerate)
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    freqs = fft_freq[:len(fft_freq)//2]

    # Update LEDs based on FFT
    update_leds(magnitude, freqs)

def main():
    print("Audio-activated LED visualization running. Press Ctrl+C to stop.")
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
        # Clear LEDs when finished
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

if __name__ == "__main__":
    main()
