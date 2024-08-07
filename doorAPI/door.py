from flask import Flask, request, jsonify
import board
from digitalio import DigitalInOut, Direction
import time

app = Flask(__name__)

# GPIO 핀 번호 설정
RED_LED_PIN = board.D17
GREEN_LED_PIN = board.D27

# GPIO 설정
red_led = DigitalInOut(RED_LED_PIN)
red_led.direction = Direction.OUTPUT

green_led = DigitalInOut(GREEN_LED_PIN)
green_led.direction = Direction.OUTPUT

# 초기 상태 설정: 빨간 LED 켜기
red_led.value = True
green_led.value = False


def control_led(value):
    if value:  # True일 경우 (1을 받았을 때)
        red_led.value = False  # 빨간 LED 끄기
        green_led.value = True  # 초록 LED 켜기
        time.sleep(2)
        red_led.value = True  # 빨간 LED 켜기
        green_led.value = False  # 초록 LED 끄기
    else:  # False일 경우 (0을 받았을 때)
        red_led.value = True  # 빨간 LED 켜기
        green_led.value = False  # 초록 LED 끄기


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
