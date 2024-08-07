
import time
import pymysql
import adafruit_fingerprint
import serial


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
            # 사용 중인 location을 가져옵니다.
            cursor.execute("SELECT location FROM fingerprints")
            used_locations = {row[0] for row in cursor.fetchall()}

            # 빈 location을 찾습니다.
            cursor.execute("SELECT location FROM available_locations")
            available_locations = {row[0] for row in cursor.fetchall()}

            # 빈 location을 반환하거나 새로운 location을 생성합니다.
            if available_locations:
                return min(available_locations)
            else:
                # 가장 높은 location + 1을 반환합니다.
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
        print("No available locations.")
        return False

    print("Enroll new finger")

    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="")
        else:
            print("Place same finger again...", end="")

        while True:
            i = finger.get_image()
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
        i = finger.image_2_tz(fingerimg)
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
                i = finger.get_image()

    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print(f"Storing model #{location}...", end="")
    i = finger.store_model(location)
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

    # 데이터베이스에 지문 정보 저장
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO fingerprints (location, employee_id) VALUES (%s, %s)"
            cursor.execute(sql, (location, employee_id))
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

    # 빈 location 목록에서 location 제거
    remove_available_location(location)

    return True


def delete_finger(finger, employee_id):
    """지문을 사번으로 삭제하고 빈 location으로 추가합니다."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 사번으로 location을 찾습니다.
            sql = "SELECT location FROM fingerprints WHERE employee_id = %s"
            cursor.execute(sql, (employee_id,))
            result = cursor.fetchone()
            if result:
                location = result[0]
                print(f"Deleting fingerprint with employee ID #{employee_id} and location #{location}...", end="")

                # 데이터베이스에서 지문 정보 삭제
                sql = "DELETE FROM fingerprints WHERE employee_id = %s"
                cursor.execute(sql, (employee_id,))
                conn.commit()
                print("Deleted from database")

                # 센서에서 지문 삭제
                print("Removing fingerprint from sensor...", end="")
                i = finger.delete_model(location)
                if i == adafruit_fingerprint.OK:
                    print("Deleted from sensor")
                    # 빈 location 목록에 추가
                    add_available_location(location)
                else:
                    if i == adafruit_fingerprint.BADLOCATION:
                        print("Bad storage location")
                    elif i == adafruit_fingerprint.FLASHERR:
                        print("Flash storage error")
                    else:
                        print("Other error")
                    return False
                return True
            else:
                print("No matching fingerprint found for the given employee ID.")
                return False

    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()


def search_finger(finger):
    """지문을 스캔하여 데이터베이스에서 일치하는 정보를 조회합니다."""
    print("Place finger on sensor...")

    while True:
        # 지문 이미지를 스캔합니다.
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            print("Image taken")
            break
        if i == adafruit_fingerprint.NOFINGER:
            print(".", end="")
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
            return None
        else:
            print("Other error")
            return None

    # 지문 이미지를 특성으로 변환합니다.
    print("Templating...", end="")
    i = finger.image_2_tz(1)
    if i != adafruit_fingerprint.OK:
        print("Templating error")
        return None

    # 데이터베이스에서 지문 검색을 시작합니다.
    print("Searching...", end="")
    i = finger.finger_search()
    if i == adafruit_fingerprint.OK:
        print("Search completed")
        # 검색 결과는 finger.finger_id에 저장됩니다.
        print(f"Found fingerprint with ID: {finger.finger_id}")

        # 데이터베이스에서 직원 정보를 조회합니다.
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = "SELECT employee_id FROM fingerprints WHERE location = %s"
                cursor.execute(sql, (finger.finger_id,))
                result = cursor.fetchone()
                if result:
                    employee_id = result[0]
                    print(f"Employee ID: {employee_id}")
                else:
                    print("No matching employee ID found.")
        except Exception as e:
            print(f"Database error: {e}")
        finally:
            conn.close()
    else:
        if i == adafruit_fingerprint.NOTFOUND:
            print("No match found")
        elif i == adafruit_fingerprint.PACKAGESENDERR:
            print("Communication error")
        else:
            print("Other error")


def main():
    uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
    finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

    while True:
        print("\nFingerprint Management System")
        print("1. Enroll Finger")
        print("2. Delete Finger by Employee ID")
        print("3. Search Finger")
        print("4. Exit")

        choice = input("Enter your choice (1/2/3/4): ")

        if choice == '1':
            employee_id = input("Enter employee ID: ")
            if enroll_finger(finger, employee_id):
                print("Fingerprint enrolled successfully.")
            else:
                print("Failed to enroll fingerprint.")
        elif choice == '2':
            employee_id = input(
                "Enter the employee ID of the fingerprint to delete: ")
            if delete_finger(finger, employee_id):
                print("Fingerprint deleted successfully.")
            else:
                print("Failed to delete fingerprint.")
        elif choice == '3':
            search_finger(finger)
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()

