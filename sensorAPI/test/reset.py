import pymysql
import serial
import adafruit_fingerprint

uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)


def clear_specific_tables():
    """특정 테이블에서 모든 데이터를 삭제합니다."""
    try:
        # 데이터베이스 연결 설정
        conn = pymysql.connect(
            host='localhost',
            user='raspi',
            password='raspi',
            database='Fingerprint'
        )
        cursor = conn.cursor()

        # 삭제할 테이블 목록
        tables = ['available_locations', 'fingerprints']

        # 각 테이블에서 데이터 삭제
        for table in tables:
            print(f"Clearing data from table: {table}")
            cursor.execute(f"DELETE FROM {table}")

        # 변경사항 커밋
        conn.commit()
        print("Data from specified tables have been cleared.")

        if finger.empty_library() == adafruit_fingerprint.OK:
            print("Library empty!")

    except Exception as e:
        print(f"Error clearing tables: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    clear_specific_tables()
