#!/usr/bin/env python3
"""
Rainbow Cascade Pattern for the Waveshare RGB LED Hat.

This script uses the rpi_ws281x library to display a continuous,
slow cascade effect that cycles through the rainbow colors across all 32 LEDs.

Ensure that you have properly installed the rpi_ws281x package and that the
LED configuration (GPIO, frequency, etc.) matches your hardware.
"""

import time
from rpi_ws281x import Adafruit_NeoPixel, Color

# LED strip configuration:
LED_COUNT      = 32      # Total number of LED pixels (4 x 8)
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM)
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800kHz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 5 or 10)
LED_BRIGHTNESS = 5      # Brightness (0 to 255)
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Create NeoPixel object with the above configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()  # This should be called once at startup.

def wheel(pos):
    """Generate rainbow colors across 0-255 positions.
    
    The input pos is between 0 and 255. Returns a Color object.
    """
    if pos < 0 or pos > 255:
        return Color(0, 0, 0)
    if pos < 85:
        # From red to green.
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        # From green to blue.
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        # From blue back to red.
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow_cascade(wait_ms=100):
    """Display a continuous rainbow cascade effect.
    
    Each iteration shifts the color phases across the LED strip.
    The wait_ms parameter controls the speed of the cascade.
    """
    offset = 0
    num_pixels = strip.numPixels()
    while True:
        # Loop through each pixel and assign a color based on its position 
        # and the global offset. This produces a phased gradient.
        for i in range(num_pixels):
            # Compute a color index for each pixel such that adjacent pixels 
            # show a slight difference. The global offset slowly increases so the
            # entire pattern appears to cascade.
            color_index = ((i * 256 // num_pixels) + offset) % 256
            strip.setPixelColor(i, wheel(color_index))
        strip.show()
        
        # Increment the offset to slowly move the colors along the strip.
        offset = (offset + 1) % 256
        
        # Wait a short time before updating.
        time.sleep(wait_ms / 1000.0)

if __name__ == '__main__':
    try:
        rainbow_cascade(wait_ms=100)  # Adjust wait_ms (in milliseconds) for speed.
    except KeyboardInterrupt:
        # When interrupted, turn off all pixels.
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
