"""
NAVSENSE Object Detection Program

Created by:
Jack Ryan, Daniel Okazaki, Michael Dallow

Advisor:
Professor Behnam Dezfouli

In association with:
Andalo
Santa Clara University
Frugal Innovation Hub

For use with the Coral Accelerator and the Raspberry Pi 3B+

Example:
	python3 obj_detection.py
"""


from edgetpu.detection.engine import DetectionEngine
from threading import Thread, Lock
from picamera import PiCamera
import RPi.GPIO as GPIO
from PIL import Image
import collections
import subprocess
import platform
import pyttsx3
import tfmini3
import serial
import time
import io
import os


# Global Variables
ser = serial.Serial("/dev/ttyAMA0", 115200)
speech = pyttsx3.init()
buttonMutex = Lock()
speakingSpeed = 150 #goes up to 250
interrupt = 0
waitTime = 5
volume = 0.5 # goes up to 1
end = 0


# Function to read labels from text files.
def read_label_file(file_path):
	with open(file_path, 'r') as f:
		lines = f.readlines()

	ret = {}

	for line in lines:
		pair = line.strip().split(maxsplit=1)
		ret[int(pair[0])] = pair[1].strip()

	return ret


# Text to speech functions
def text_to_speech(result, labels):
	string = constructString(labels, result)
	if speech.isBusy():
		speech.stop()
	speech.say(string)
	speech.runAndWait()


def constructString(dictionary, objs):
	string = 'There is '
	left, center, right = parse_objects(objs)
	lStr = ''
	rStr = ''
	cStr = ''

	if left:
		lStr = count_items(dictionary, left) + 'to your left. '
	if center:
		cStr = count_items(dictionary, center) + 'straight ahead. '
	# cStr = count_items(dictionary, center) + 'straight ahead' + dist_str
	if right:
		rStr = count_items(dictionary, right) + 'to your right.'
	# left and right
	# center and right
	if (lStr or cStr) and rStr:
		string += lStr + cStr + 'And ' + rStr
	# left and center
	elif lStr and cStr:
		string += lStr + 'And ' + cStr
	# right and left
	elif rStr and lStr:
		string += rStr + 'And ' + lStr
	else:
		if lStr:
			string += lStr
		elif rStr:
			string += rStr
		else:
			string += cStr

	return string


def parse_objects(obs):
	left = []
	center = []
	right = []

	# Parse Objects
	for o in obs:
		box = o.bounding_box.flatten().tolist()
		print(str(o.label_id) + ':')
		print(box)
		if box[0] < 640.0 and box[2] < 640.0:
			left.append(o.label_id)
		elif box[0] > 1280.0 and box[2] < 1920.0:
			right.append(o.label_id)
		else:
			center.append(o.label_id)

	return left, center, right


def count_items(dictionary, arr):
	counter = collections.Counter(arr)
	c = dict(counter)
	str = multiples(dictionary, c)

	return str


def multiples(dictionary, arr):
	st = ''
	if len(arr) != 0:
		for key, value in arr.items():
			if value == 1:
				st += 'one ' + dictionary[key] + ', '
			if value <= 5 and value > 1:
				st += str(value) + ' '
				if key != 1:
					st += dictionary[key] + 's, '
				else:
					st += 'people, '
			if value > 5:
				st += 'several '
				if key != 1:
					st += dictionary[key] + 's, '
				else:
					st += 'people, '
	# else:
		# st = 'Nothing '

	return st


# Button interrupt function
def hardware_interrupt(channel):
	global interrupt
	global buttonMutex

	GPIO.remove_event_detect(channel)

	print("inference button was pressed")
	buttonMutex.acquire()
	interrupt = 1
	buttonMutex.release()
	GPIO.add_event_detect(channel, GPIO.FALLING,
						  callback=hardware_interrupt, bouncetime=300)

	print("end of interrupt")


def button_up(channel):
	global speakingSpeed
	global volume
	global speech

	GPIO.remove_event_detect(channel)

	print("UP")
	if speech.isBusy():
		speech.stop()
	if GPIO.input(35):
		print("Volume up")
		if volume < 1.0:
			volume = volume + 0.1
			set_volume()
		else:
			speech.say("Max Volume")
			speech.runAndWait()

	else:
		print("speaking speed up")
		if speakingSpeed < 249:
			speakingSpeed = speakingSpeed + 2
			set_speaking_speed()
		else:
			speech.say("Max Speaking Speed")
			speech.runAndWait()
	time.sleep(0.25)
	GPIO.add_event_detect(channel, GPIO.FALLING,
						  callback=button_up, bouncetime=300)


def button_down(channel):
	global speakingSpeed
	global volume
	global speech

	GPIO.remove_event_detect(channel)

	print("DOWN")
	if speech.isBusy():
		speech.stop()
	if GPIO.input(35):
		print("Volume Down")
		if volume > 0:
			volume = volume - 0.1
			set_volume()
	else:
		print("speaking speed down")
		if speakingSpeed > 1:
			speakingSpeed = speakingSpeed - 2
			set_speaking_speed()
	time.sleep(0.25)
	GPIO.add_event_detect(channel, GPIO.FALLING,
						  callback=button_down, bouncetime=300)


def power_off(channel):
	global end
	
	end = 1


# Helper functions
def set_speaking_speed():
	global speakingSpeed
	speech.setProperty('rate', speakingSpeed)


def set_volume():
	global volume
	speech.setProperty('volume', volume)


# Read device settings from file
def parse_settings():
	global speakingSpeed
	global volume

	exists = os.path.exists('settings.txt')

	if not exists:
		file = open('settings.txt', 'w')
		file.write(str(150) + '\n')
		file.write(str(1.0))
		file.close()
		speakingSpeed = 150
		volume = 1
	else:
		file = open("settings.txt", 'r')
		speakingSpeed = int(file.readline())
		volume = float(file.readline())
		file.close()
		print('_______________________________________')
		print('Speaking Speed:')
		print(speakingSpeed)
		print('Volume:')
		print(volume)
		print('_______________________________________')


def save_settings():
	global speakingSpeed
	global volume

	file = open('settings.txt', 'w')
	file.write(str(speakingSpeed) + '\n')
	file.write(str(volume))
	file.close()


def main():
	global speakingSpeed
	global volume
	global interrupt
	global waitTime
	global ser
	global speech

	# Models and label path directories
	model = 'Models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'
	label = 'Models/coco_labels.txt'

	# Retrieve speaking speed and volume settings from file
	parse_settings()

	# set speaking speed and volume
	set_speaking_speed()
	set_volume()

	speech.say('Welcome to NavSense')
	speech.runAndWait()

	# Initialize engine.
	speech.say('Loading Object Recognition Models')
	speech.runAndWait()
	engine = DetectionEngine(model)
	labels = read_label_file(label)
	result = None

	# Initialize Camera
	camera = PiCamera()
	camera.rotation = 180

	# Initialize GPIO
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(29, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(32, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(35, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

	speech.say("Device Is Ready To Use")
	speech.runAndWait()

	# Start of button interrupt
	GPIO.add_event_detect(
		3, GPIO.FALLING, callback=hardware_interrupt, bouncetime=300)
	# Button up
	GPIO.add_event_detect(
		11, GPIO.FALLING, callback=button_up, bouncetime=300)
	# Button down
	GPIO.add_event_detect(
		29, GPIO.FALLING, callback=button_down, bouncetime=300)
	# Power off
	GPIO.add_event_detect(
		32, GPIO.FALLING, callback=power_off, bouncetime=300)
	# Switch: 35

	while not end:
		camera.capture('image.jpg')
		image = Image.open('image.jpg')
		# image.show()

		result = engine.DetectWithImage(
			image, threshold=0.25, keep_aspect_ratio=True, relative_coord=False, top_k=10)
		if result and ser.is_open and not end:
			distance = tfmini3.getTFminiData(ser)

			if distance != None:
				if distance < 7000:
					if speech.isBusy():
						speech.stop()
					speech.say('The nearest object in front of you is ')
					dist_str = ''

					if distance > 100:
						dist_str += "approximately " + \
							str(distance / 100) + " meters ahead. "
					else:
						dist_str += "approximately " + \
							str(distance) + " centimeters ahead. "
					if speech.isBusy():
						speech.stop()
					speech.say(dist_str)
					speech.runAndWait()

			# Start thread to run text to speech, when done, quit thread
			text_to_speech(result, labels)
		else:
			if speech.isBusy():
				speech.stop()
			speech.say("No object detected")
			speech.runAndWait()

		# Sleep and check for hardware interrupt code
		start_ms = time.time()

		while not end:
			print('wait')
			time.sleep(0.25)
			buttonMutex.acquire()

			if interrupt == 1:
				interrupt = 0
				buttonMutex.release()
				print("overriding loop")
				break

			buttonMutex.release()
			elapsed_ms = time.time() - start_ms

			# Wait time in between inferencee
			if elapsed_ms > waitTime:
				break

	print("OFF")
	print("shutting down device")
	GPIO.cleanup()
	save_settings()
	if os.path.exists('image.jpg'):
		os.remove("image.jpg")
	if speech.isBusy():
		speech.stop()
	ser.close()
	speech.say("Device Turning Off")
	speech.runAndWait()
	os.system("sudo shutdown -h now")


if __name__ == '__main__':
	try:
		if ser.is_open == False:
			ser.open()

	except KeyboardInterrupt:
		if ser != None:
			ser.close()

	main()
