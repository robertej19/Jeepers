import sounddevice as sd
import numpy as np
import scipy.fftpack as fftpack

def audio_callback(indata, frames, time, status):
    # Flatten input data (mono)
    audio_data = indata[:, 0]

    # Compute RMS (volume level)
    volume_norm = np.linalg.norm(audio_data) * 10
    bar = "#" * min(int(volume_norm), 50)

    # Perform FFT
    fft_data = fftpack.fft(audio_data)
    fft_freq = fftpack.fftfreq(len(audio_data), 1.0 / samplerate)
    
    # Take the magnitude of FFT and select positive frequencies
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    freqs = fft_freq[:len(fft_freq)//2]

    # Find peak frequency
    peak_freq = freqs[np.argmax(magnitude)]

    # Print intensity and dominant frequency
    print(f"\rIntensity: [{bar:<50}] {volume_norm:.2f} | Peak Frequency: {peak_freq:6.1f} Hz", end='')

def main():
    global samplerate
    samplerate = 44100  # Hz
    block_duration = 0.1  # Seconds per block
    blocksize = int(samplerate * block_duration)
    
    try:
        with sd.InputStream(device=0,  # Your mic device
                            channels=1,
                            samplerate=samplerate,
                            blocksize=blocksize,
                            callback=audio_callback):
            print("Listening to microphone with FFT analysis... Press Ctrl+C to stop.")
            while True:
                sd.sleep(1000)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
