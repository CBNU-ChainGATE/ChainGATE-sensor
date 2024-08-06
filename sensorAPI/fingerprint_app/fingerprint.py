import time
import serial
import adafruit_fingerprint
from PIL import Image

class Fingerprint:
    def __init__(self, port="/dev/ttyS0", baudrate=57600, timeout=1):
        self.uart = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)

    def enroll_finger(self, location):
        """Take a 2 finger images and template it, then store in 'location'"""
        for fingerimg in range(1, 3):
            if fingerimg == 1:
                print("Place finger on sensor...", end="")
            else:
                print("Place same finger again...", end="")

            while True:
                i = self.finger.get_image()
                if i == adafruit_fingerprint.OK:
                    print("Image taken")
                    break
                if i == adafruit_fingerprint.NOFINGER:
                    print(".", end="")
                elif i == adafruit_fingerprint.IMAGEFAIL:
                    print("Imaging error")
                    return False
                else:
                    print("Other error")
                    return False

            print("Templating...", end="")
            i = self.finger.image_2_tz(fingerimg)
            if i == adafruit_fingerprint.OK:
                print("Templated")
            else:
                if i == adafruit_fingerprint.IMAGEMESS:
                    print("Image too messy")
                elif i == adafruit_fingerprint.FEATUREFAIL:
                    print("Could not identify features")
                elif i == adafruit_fingerprint.INVALIDIMAGE:
                    print("Image invalid")
                else:
                    print("Other error")
                return False

            if fingerimg == 1:
                print("Remove finger")
                time.sleep(1)
                while i != adafruit_fingerprint.NOFINGER:
                    i = self.finger.get_image()

        print("Creating model...", end="")
        i = self.finger.create_model()
        if i == adafruit_fingerprint.OK:
            print("Created")
        else:
            if i == adafruit_fingerprint.ENROLLMISMATCH:
                print("Prints did not match")
            else:
                print("Other error")
            return False

        print("Storing model #%d..." % location, end="")
        i = self.finger.store_model(location)
        if i == adafruit_fingerprint.OK:
            print("Stored")
        else:
            if i == adafruit_fingerprint.BADLOCATION:
                print("Bad storage location")
            elif i == adafruit_fingerprint.FLASHERR:
                print("Flash storage error")
            else:
                print("Other error")
            return False

        return True

    def find_finger(self):
        """Get a finger print image, template it, and see if it matches!"""
        print("Waiting for image...")
        while self.finger.get_image() != adafruit_fingerprint.OK:
            pass
        print("Templating...")
        if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
            return False
        print("Searching...")
        if self.finger.finger_search() != adafruit_fingerprint.OK:
            return False
        return True

    def delete_finger(self, location):
        """Delete the finger model from the given location"""
        if self.finger.delete_model(location) == adafruit_fingerprint.OK:
            return True
        return False

    def clear_library(self):
        """Clear the entire fingerprint library"""
        if self.finger.empty_library() == adafruit_fingerprint.OK:
            return True
        return False

    def save_fingerprint_image(self, filename):
        """Scan fingerprint then save image to filename."""
        while True:
            result = self.finger.get_image()
            if result == adafruit_fingerprint.OK:
                break
            elif result == adafruit_fingerprint.NOFINGER:
                time.sleep(0.1)  # 짧은 시간 동안 기다렸다가 다시 시도
            else:
                print("Error getting image:", result)
                return False

        img = Image.new("L", (256, 288), "white")
        pixeldata = img.load()
        mask = 0b00001111
        result = self.finger.get_fpdata(sensorbuffer="image")

        x = 0
        y = 0
        for i in range(len(result)):
            pixeldata[x, y] = (int(result[i]) >> 4) * 17
            x += 1
            pixeldata[x, y] = (int(result[i]) & mask) * 17
            if x == 255:
                x = 0
                y += 1
            else:
                x += 1

        if not img.save(filename):
            return True
        return False

    def get_num(self, max_number):
        """Use input() to get a valid number from 0 to the maximum size
        of the library. Retry till success!"""
        i = -1
        while (i > max_number - 1) or (i < 0):
            try:
                i = int(input("Enter ID # from 0-{}: ".format(max_number - 1)))
            except ValueError:
                pass
        return i

