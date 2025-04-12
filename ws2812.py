#encoding:utf-8
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
import time
import random
from rpi_ws281x import Adafruit_NeoPixel, Color


# LED strip configuration:
LED_COUNT      = 32      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 10    # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
# Intialize the library (must be called once before other functions).
while 1:
	strip.begin()
	#order
	for i in range(0,strip.numPixels()):
		strip.setPixelColor(i, Color(0,0,255))	
		strip.setPixelColor(i-1, Color(0,0,200))
		strip.setPixelColor(i-2, Color(0,0,150))
		strip.setPixelColor(i-3, Color(0,0,100))
		strip.setPixelColor(i-4, Color(0,0,0))
		strip.show()
		time.sleep(0.1)
	#Reverse order	
	for i in range(0,strip.numPixels()):
		strip.setPixelColor(strip.numPixels()-i, Color(0,255,0))	
		strip.show()
		time.sleep(0.05)
	#Turn around
	for i in range(0,strip.numPixels()//4):
		strip.setPixelColor(i, Color(255,0,0))
		strip.show()
		time.sleep(0.05)
	for i in range(0,strip.numPixels()//8-1):
		strip.setPixelColor(7+8*i, Color(255,0,0))	
		strip.show()
		time.sleep(0.05)
	for i in range(0,strip.numPixels()//4+1):
		strip.setPixelColor(strip.numPixels()-i, Color(255,0,0))
		strip.show()
		time.sleep(0.05)
	for i in range(0,strip.numPixels()//8-1):
		strip.setPixelColor(16-8*i, Color(255,0,0))	
		strip.show()
		time.sleep(0.05)	
	for i in range(0,strip.numPixels()//4-1):
		strip.setPixelColor(i+8, Color(255,0,0))	
		strip.show()
		time.sleep(0.05)		
	for i in range(0,strip.numPixels()//4-1):
		strip.setPixelColor(strip.numPixels()-9-i, Color(255,0,0))	
		strip.show()
		time.sleep(0.05)	
	
	#Middle to both sides, both sides to the middle
	for i in range(0,strip.numPixels()//4-1):
		for y in range(0,strip.numPixels()//8):
			strip.setPixelColor(4+y*8+i, Color(0,255,255))
			strip.setPixelColor(3+y*8-i, Color(0,255,255))
		strip.show()
		time.sleep(0.1)
	for i in range(0,strip.numPixels()//4-1):
		for y in range(0,strip.numPixels()//8):
			strip.setPixelColor(7+y*8-i, Color(255,255,0))
			strip.setPixelColor(y*8+i, Color(255,255,0))
		strip.show()
		time.sleep(0.1)
	#random color
	for x in range(0,5):
		for i in range(0,strip.numPixels()):
			strip.setPixelColor(i, Color(random.randint(0, 255),random.randint(0, 255),random.randint(0, 255)))	
			strip.show()
		time.sleep(0.5)
		
			
			


