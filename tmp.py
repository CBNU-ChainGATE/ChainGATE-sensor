from flask import Flask, request, jsonify
import board
from digitalio import DigitalInOut, Direction
from adafruit_character_lcd.character_lcd import Character_LCD_Mono
import pwmio
from pwmio import PWMOut
import time
import pymysql
import adafruit_fingerprint
import serial

app = Flask(__name__)

############## Initialize ##############
"""LED"""
RED_LED_PIN = board.D17
GREEN_LED_PIN = board.D27
red_led = DigitalInOut(RED_LED_PIN)
green_led = DigitalInOut(GREEN_LED_PIN)

red_led.direction = Direction.OUTPUT
green_led.direction = Direction.OUTPUT

# 초기 상태 설정: 빨간 LED 켜기
red_led.value = True
green_led.value = False

"""LCD"""
lcd_columns = 16
lcd_rows = 2
PWN_PERCENT = 30

lcd_rs = DigitalInOut(board.D7)
lcd_en = DigitalInOut(board.D8)
lcd_d4 = DigitalInOut(board.D9)
lcd_d5 = DigitalInOut(board.D10)
lcd_d6 = DigitalInOut(board.D11)
lcd_d7 = DigitalInOut(board.D12)

lcd = Character_LCD_Mono(
    lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)

# Initialize PWM for contrast control
pwm_pin = board.D18  # Select a suitable PWM pin
pwm = PWMOut(pwm_pin, frequency=1000, duty_cycle=0)  # 1 kHz PWM

pwm.duty_cycle = PWN_PERCENT * 65535 / 100
lcd.message = "Please verify\nyour identity"

# 전역 변수
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)


def error_to_lcd(error_message):
    write_to_lcd(error_message)
    time.sleep(2)
    write_to_lcd("Please verify\nyour identity")


def write_to_lcd(message):
    lcd.clear()
    lcd.message = message


def control_led(red_status, green_status):
    red_led.value = red_status
    green_led.value = green_status


def control_door(value):
    if value:  # True일 경우 (1을 받았을 때)
        write_to_lcd("Open the door")
        control_led(False, True)  # 빨:off 초:on
        time.sleep(2)
        control_led(True, False)  # 빨:on 초:off
    else:  # False일 경우 (0을 받았을 때)
        write_to_lcd("Entry denied")
        control_led(True, False)  # 빨:on 초:off
        time.sleep(0.3)
        for _ in range(2):
            control_led(False, False)  # 빨:off 초:off
            time.sleep(0.3)
            control_led(True, False)  # 빨:on 초:off
            time.sleep(0.3)
        time.sleep(0.5)
    write_to_lcd("Please verify\nyour identity")


def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='raspi',
        password='raspi',
        database='Fingerprint',
    )


def get_next_available_location():
    """빈 location을 찾거나 가장 높은 location + 1을 반환합니다."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT location FROM fingerprints")
            used_locations = {row[0] for row in cursor.fetchall()}

            cursor.execute("SELECT location FROM available_locations")
            available_locations = {row[0] for row in cursor.fetchall()}

            if available_locations:
                return min(available_locations)
            else:
                max_location = max(used_locations, default=0)
                return max_location + 1

    except Exception as e:
        error_to_lcd("Database error!")
        print(f"Database error: {e}")
    finally:
        conn.close()
    return None


def add_available_location(location):
    """빈 location을 데이터베이스에 추가합니다."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO available_locations (location) VALUES (%s)"
            cursor.execute(sql, (location,))
        conn.commit()
    except Exception as e:
        error_to_lcd("Database error!")
        print(f"Database error: {e}")
    finally:
        conn.close()


def remove_available_location(location):
    """빈 location을 데이터베이스에서 제거합니다."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "DELETE FROM available_locations WHERE location = %s"
            cursor.execute(sql, (location,))
        conn.commit()
    except Exception as e:
        error_to_lcd("Database error!")
        print(f"Database error: {e}")
    finally:
        conn.close()


def enroll_finger(finger, employee_id):
    """지문을 등록하고 데이터베이스에 저장합니다."""
    location = get_next_available_location()
    if location is None:
        return {"success": False, "message": "No available locations."}

    for fingerimg in range(1, 3):
        if fingerimg == 1:
            write_to_lcd("Place finger\non sensor...")
            print("Place finger on sensor...", end="")
        else:
            write_to_lcd("Place finger\nagain...")
            print("Place same finger again...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                break
            if i == adafruit_fingerprint.NOFINGER:
                continue
            elif i == adafruit_fingerprint.IMAGEFAIL:
                error_to_lcd("Imaging error!")
                return {"success": False, "message": "Imaging error"}
            else:
                error_to_lcd("Other error!")
                return {"success": False, "message": "Other error"}

        i = finger.image_2_tz(fingerimg)
        if i != adafruit_fingerprint.OK:
            error_to_lcd("Templating\nerror!")
            return {"success": False, "message": "Templating error"}

        if fingerimg == 1:
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    i = finger.create_model()
    if i != adafruit_fingerprint.OK:
        error_to_lcd("Other error!")
        return {"success": False, "message": "Model creation error"}

    i = finger.store_model(location)
    if i != adafruit_fingerprint.OK:
        error_to_lcd("Storing model\nerror!")
        return {"success": False, "message": "Storing model error"}

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO fingerprints (location, employee_id) VALUES (%s, %s)"
            cursor.execute(sql, (location, employee_id))
        conn.commit()
    except Exception as e:
        error_to_lcd("Database error!")
        return {"success": False, "message": f"Database error: {e}"}
    finally:
        conn.close()

    remove_available_location(location)
    write_to_lcd("Enrolled\nsuccessfully")
    time.sleep(2)
    write_to_lcd("Please verify\nyour identity")
    return {"success": True, "message": "Fingerprint enrolled successfully."}


def delete_finger(finger, employee_id):
    """지문을 사번으로 삭제하고 빈 location으로 추가합니다."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT location FROM fingerprints WHERE employee_id = %s"
            cursor.execute(sql, (employee_id,))
            result = cursor.fetchone()
            if result:
                location = result[0]
                sql = "DELETE FROM fingerprints WHERE employee_id = %s"
                cursor.execute(sql, (employee_id,))
                conn.commit()

                i = finger.delete_model(location)
                if i == adafruit_fingerprint.OK:
                    add_available_location(location)
                    write_to_lcd("Deleted\nsuccessfully")
                    time.sleep(2)
                    write_to_lcd("Please verify\nyour identity")
                    return {"success": True, "message": "Fingerprint deleted successfully."}
                else:
                    error_to_lcd("Sensor deletion\nerror!")
                    return {"success": False, "message": "Sensor deletion error"}
            else:
                error_to_lcd("No found\nFingerprint!")
                return {"success": False, "message": "No matching fingerprint found for the given employee ID."}
    except Exception as e:
        error_to_lcd("Database error!")
        return {"success": False, "message": f"Database error: {e}"}
    finally:
        conn.close()


def search_finger(finger):
    """지문을 스캔하여 데이터베이스에서 일치하는 정보를 조회합니다."""
    write_to_lcd("Place finger\non sensor...")
    print("Place finger on sensor...", end="")
    while True:
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            break
        if i == adafruit_fingerprint.NOFINGER:
            continue
        elif i == adafruit_fingerprint.IMAGEFAIL:
            error_to_lcd("Imaging error!")
            return {"success": False, "message": "Imaging error"}
        else:
            error_to_lcd("Other error!")
            return {"success": False, "message": "Other error"}

    i = finger.image_2_tz(1)
    if i != adafruit_fingerprint.OK:
        error_to_lcd("Templating\nerror!")
        return {"success": False, "message": "Templating error"}

    i = finger.finger_search()
    print("finger: ", end='')
    print(finger.finger_id)
    if i == adafruit_fingerprint.OK:
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = "SELECT employee_id FROM fingerprints WHERE location = %s"
                cursor.execute(sql, (finger.finger_id,))
                result = cursor.fetchone()
                if result:
                    employee_id = result[0]
                    return {"success": True, "employee_id": employee_id}
                else:
                    # error_to_lcd("No found\nEmployee_ID!")
                    return {"success": False, "message": "No matching employee_ID found."}
        except Exception as e:
            error_to_lcd("Database error!")
            return {"success": False, "message": f"Database error: {e}"}
        finally:
            conn.close()
    else:
        if i == adafruit_fingerprint.NOTFOUND:
            # error_to_lcd("No found\nFingerprint!")
            return {"success": False, "message": "No matching Fingerprint found"}
        elif i == adafruit_fingerprint.PACKAGESENDERR:
            error_to_lcd("Communication\nerror!")
            return {"success": False, "message": "Communication error"}
        else:
            error_to_lcd("Other\nerror!")
            return {"success": False, "message": "Other error"}


@app.route('/door', methods=['POST'])
def door_control():
    data = request.get_json()
    value = data.get('value')

    if value is None or value not in [0, 1]:
        return jsonify({'error': 'Invalid value, must be 0 or 1'}), 400

    control_door(value)
    return jsonify({'status': 'success'}), 200


@app.route('/finger/enroll', methods=['POST'])
def enroll():
    """지문 등록 API"""
    data = request.json
    employee_id = data.get('employee_id')

    if not employee_id:
        return jsonify({"success": False, "message": "Employee ID is required."}), 400

    result = enroll_finger(finger, employee_id)
    return jsonify(result)


@app.route('/finger/delete', methods=['POST'])
def delete():
    """지문 삭제 API"""
    data = request.json
    employee_id = data.get('employee_id')

    if not employee_id:
        return jsonify({"success": False, "message": "Employee ID is required."}), 400

    result = delete_finger(finger, employee_id)
    return jsonify(result)


@app.route('/finger/search', methods=['GET'])
def search():
    """지문 조회 API"""
    result = search_finger(finger)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
