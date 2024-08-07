from flask import Flask, request, jsonify
import RPi.GPIO as GPIO
import time

app = Flask(__name__)

# GPIO 핀 번호 설정
RED_LED_PIN = 17
GREEN_LED_PIN = 27

# GPIO 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_LED_PIN, GPIO.OUT)
GPIO.setup(GREEN_LED_PIN, GPIO.OUT)

# 초기 상태 설정: 빨간 LED 켜기
GPIO.output(RED_LED_PIN, GPIO.HIGH)
GPIO.output(GREEN_LED_PIN, GPIO.LOW)

def control_led(value):
    if value:  # True일 경우 (1을 받았을 때)
        GPIO.output(RED_LED_PIN, GPIO.LOW)  # 빨간 LED 끄기
        GPIO.output(GREEN_LED_PIN, GPIO.HIGH)  # 초록 LED 켜기
        time.sleep(2)
        GPIO.output(RED_LED_PIN, GPIO.HIGH)  # 빨간 LED 켜기
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)  # 초록 LED 끄기

    else:  # False일 경우 (0을 받았을 때)
        GPIO.output(RED_LED_PIN, GPIO.HIGH)  # 빨간 LED 켜기
        GPIO.output(GREEN_LED_PIN, GPIO.LOW)  # 초록 LED 끄기

@app.route('/door', methods=['POST'])
def led_control():
    data = request.get_json()
    value = data.get('value')
    
    if value is None or value not in [0, 1]:
        return jsonify({'error': 'Invalid value, must be 0 or 1'}), 400
    
    control_led(value)
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("Server interrupted")
    finally:
        GPIO.cleanup()  # GPIO 상태 초기화

