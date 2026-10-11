#!/usr/bin/env python3

# run script and use these keys within the terminal to test motor function:
# w = forward, s = reverse, a = turn left, d = turn right, x = stop, q = quit

import cv2                              #OpenCV for camera capture and display
import time                             #delay and time use                       
from adafruit_pca9685 import PCA9685    #PWM driver for Victor 888
import Jetson.GPIO as GPIO              #GPIO library for the nano
import board                            #Blinka board pins
import busio                            #Blinka I2C bus

#Config params

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
MOTOR_NEUTRAL = 0
MOTOR_MIN = -254                        #Max reverse
MOTOR_MAX = 254                         #Max forward
BASE_SPEED = 100  # Hopefully slow enough

PCA9685_ADDRESS = 0x40                  #I2C address
PCA9685_FREQ_HZ = 200                   #PWM freq for victor
LEFT_MOTOR_CHANNEL = 0
RIGHT_MOTOR_CHANNEL = 1

VICTOR_REVERSE_PULSE_US = 1000 # pulse widths in microseconds
VICTOR_NEUTRAL_PULSE_US = 1500
VICTOR_FORWARD_PULSE_US = 2000

#Initialisation
i2c = busio.I2C(board.SCL, board.SDA)   
pca = PCA9685(i2c, address=PCA9685_ADDRESS)
pca.frequency = PCA9685_FREQ_HZ

#GPIO setup
GPIO.setmode(GPIO.BOARD)

#Motor controls
def pulse_width_to_duty_cycle(pulse_width_us):
    period_us = 1_000_000.0 / pca.frequency
    duty_cycle = int((pulse_width_us / period_us) * 65535)
    return max(0, min(65535, duty_cycle))


def set_motor_speed(channel, speed):
    speed = max(MOTOR_MIN, min(MOTOR_MAX, float(speed)))

    if speed < 0:
        fraction = abs(speed) / abs(MOTOR_MIN)
        pulse_width_us = (
            VICTOR_NEUTRAL_PULSE_US
            - fraction * (VICTOR_NEUTRAL_PULSE_US - VICTOR_REVERSE_PULSE_US)
        )
    else:
        fraction = speed / MOTOR_MAX
        pulse_width_us = (
            VICTOR_NEUTRAL_PULSE_US
            + fraction * (VICTOR_FORWARD_PULSE_US - VICTOR_NEUTRAL_PULSE_US)
        )

    pca.channels[channel].duty_cycle = pulse_width_to_duty_cycle(pulse_width_us)


def stop_motors():  # Neutral
    set_motor_speed(LEFT_MOTOR_CHANNEL, MOTOR_NEUTRAL)
    set_motor_speed(RIGHT_MOTOR_CHANNEL, MOTOR_NEUTRAL)

def main():
    print("Starting Tennis Court Line Drying Vehicle")
    print("Controls:")
    print("  w = forward")
    print("  s = reverse")
    print("  a = turn left")
    print("  d = turn right")
    print("  x = stop")
    print("  q = quit")
    print("Press Ctrl+C to stop")

    stop_motors()

    #IMX219 8MP 160 FOV Cam
    pipeline = (
        "nvarguscamerasrc sensor-id=0 "
        "sensor-mode=2 "
        "wbmode=0 "
        "aeantibandingfreq=60 "
        "! 'video/x-raw(memory:NVMM), format=NV12, width=640, height=480, framerate=30/1' "
        "! nvvidconv "
        "! videoconvert "
        "! video/x-raw, format=BGR "
        "! appsink"
    )

    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print("Error: Could not open IMX219 camera")
        stop_motors()
        return

    try:
        while True:
            #Camera frame
            ret, frame = cap.read()
            if not ret:
                print("Camera frame unavailable")
                stop_motors()
                continue

            #Show feed
            cv2.imshow("IMX219 Camera", frame)

            #Keyboard controls
            key = cv2.waitKey(1) & 0xFF

            if key == ord('w'):
                print("Forward")
                set_motor_speed(LEFT_MOTOR_CHANNEL, BASE_SPEED)
                set_motor_speed(RIGHT_MOTOR_CHANNEL, BASE_SPEED)

            elif key == ord('s'):
                print("Reverse")
                set_motor_speed(LEFT_MOTOR_CHANNEL, -BASE_SPEED)
                set_motor_speed(RIGHT_MOTOR_CHANNEL, -BASE_SPEED)

            elif key == ord('a'):
                print("Turn Left")
                set_motor_speed(LEFT_MOTOR_CHANNEL, -BASE_SPEED)
                set_motor_speed(RIGHT_MOTOR_CHANNEL, BASE_SPEED)

            elif key == ord('d'):
                print("Turn Right")
                set_motor_speed(LEFT_MOTOR_CHANNEL, BASE_SPEED)
                set_motor_speed(RIGHT_MOTOR_CHANNEL, -BASE_SPEED)

            elif key == ord('x'):
                print("Stop")
                stop_motors()

            elif key == ord('q'):
                print("Quitting...")
                break

            # Small delay
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        print("Stopping motors...")
        stop_motors()
        time.sleep(0.2)
        pca.channels[LEFT_MOTOR_CHANNEL].duty_cycle = 0
        pca.channels[RIGHT_MOTOR_CHANNEL].duty_cycle = 0
        pca.deinit()
        cap.release()
        cv2.destroyAllWindows()

        GPIO.cleanup()

        print("Cleanup complete")


if __name__ == "__main__":
    main()