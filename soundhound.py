import sounddevice as sd
import numpy as np

def print_sound_level(indata, frames, time, status):
    # Calculate RMS (Root Mean Square) for the input audio buffer
    volume_norm = np.linalg.norm(indata) * 10
    # Print intensity bar to console
    bar = "#" * int(volume_norm)
    print(f"\rIntensity: [{bar:<50}] {volume_norm:.2f}", end='')

def main():
    # Audio settings
    samplerate = 44100  # Standard audio sampling rate
    block_duration = 0.1  # Duration (seconds) per read block

    # Replace 'device' with your mic's ID if necessary:
    device = 0
    #device = None  # Default input device

    try:
        with sd.InputStream(callback=print_sound_level,
                            channels=1,
                            samplerate=samplerate,
                            blocksize=int(samplerate * block_duration),
                            device=device):
            print("Listening to microphone... Press Ctrl+C to stop.")
            while True:
                sd.sleep(1000)  # Keep program running
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(str(e))

if __name__ == "__main__":
    main()
