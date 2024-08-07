import pymysql

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='raspi',
        password='raspi',
        database='Fingerprint',
    )

def print_all_table_contents():
    """두 테이블의 모든 내용을 출력합니다."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # available_locations 테이블의 모든 행을 조회합니다.
            cursor.execute("SELECT * FROM available_locations")
            available_locations = cursor.fetchall()
            print("\nContents of available_locations table:")
            if available_locations:
                for row in available_locations:
                    print(row)
            else:
                print("No data found in available_locations table.")

            # fingerprints 테이블의 모든 행을 조회합니다.
            cursor.execute("SELECT * FROM fingerprints")
            fingerprints = cursor.fetchall()
            print("\nContents of fingerprints table:")
            if fingerprints:
                for row in fingerprints:
                    print(row)
            else:
                print("No data found in fingerprints table.")
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def main():
    print_all_table_contents()

if __name__ == "__main__":
    main()

