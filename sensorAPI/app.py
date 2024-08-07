from flask import Flask, request, jsonify
import pymysql
import adafruit_fingerprint
import serial
import time

app = Flask(__name__)

# 전역 변수
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

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
            print("Place finger on sensor...", end="")
        else:
            print("Place same finger again...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                break
            if i == adafruit_fingerprint.NOFINGER:
                continue
            elif i == adafruit_fingerprint.IMAGEFAIL:
                return {"success": False, "message": "Imaging error"}
            else:
                return {"success": False, "message": "Other error"}

        i = finger.image_2_tz(fingerimg)
        if i != adafruit_fingerprint.OK:
            return {"success": False, "message": "Templating error"}

        if fingerimg == 1:
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    i = finger.create_model()
    if i != adafruit_fingerprint.OK:
        return {"success": False, "message": "Model creation error"}

    i = finger.store_model(location)
    if i != adafruit_fingerprint.OK:
        return {"success": False, "message": "Storing model error"}

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO fingerprints (location, employee_id) VALUES (%s, %s)"
            cursor.execute(sql, (location, employee_id))
        conn.commit()
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}
    finally:
        conn.close()

    remove_available_location(location)
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
                    return {"success": True, "message": "Fingerprint deleted successfully."}
                else:
                    return {"success": False, "message": "Sensor deletion error"}
            else:
                return {"success": False, "message": "No matching fingerprint found for the given employee ID."}
    except Exception as e:
        return {"success": False, "message": f"Database error: {e}"}
    finally:
        conn.close()

def search_finger(finger):
    """지문을 스캔하여 데이터베이스에서 일치하는 정보를 조회합니다."""
    while True:
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            break
        if i == adafruit_fingerprint.NOFINGER:
            continue
        elif i == adafruit_fingerprint.IMAGEFAIL:
            return {"success": False, "message": "Imaging error"}
        else:
            return {"success": False, "message": "Other error"}

    i = finger.image_2_tz(1)
    if i != adafruit_fingerprint.OK:
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
                    return {"success": False, "message": "No matching employee ID found."}
        except Exception as e:
            return {"success": False, "message": f"Database error: {e}"}
        finally:
            conn.close()
    else:
        if i == adafruit_fingerprint.NOTFOUND:
            return {"success": False, "message": "No match found"}
        elif i == adafruit_fingerprint.PACKAGESENDERR:
            return {"success": False, "message": "Communication error"}
        else:
            return {"success": False, "message": "Other error"}

@app.route('/enroll', methods=['POST'])
def enroll():
    """지문 등록 API"""
    data = request.json
    employee_id = data.get('employee_id')

    if not employee_id:
        return jsonify({"success": False, "message": "Employee ID is required."}), 400

    result = enroll_finger(finger, employee_id)
    return jsonify(result)

@app.route('/delete', methods=['POST'])
def delete():
    """지문 삭제 API"""
    data = request.json
    employee_id = data.get('employee_id')

    if not employee_id:
        return jsonify({"success": False, "message": "Employee ID is required."}), 400

    result = delete_finger(finger, employee_id)
    return jsonify(result)

@app.route('/search', methods=['GET'])
def search():
    """지문 조회 API"""
    result = search_finger(finger)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

