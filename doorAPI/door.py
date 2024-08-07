from flask import Flask, request, jsonify
import board
from digitalio import DigitalInOut, Direction
from adafruit_character_lcd.character_lcd import Character_LCD_Mono
import pwmio
from pwmio import PWMOut
import time

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
PWN_PERCENT = 50

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
lcd.message = "Please verify your identity"


def control_led(value):
    if value:  # True일 경우 (1을 받았을 때)
        red_led.value = False  # 빨간 LED 끄기
        green_led.value = True  # 초록 LED 켜기
        lcd.message = "Open the door"
        time.sleep(2)
        red_led.value = True  # 빨간 LED 켜기
        green_led.value = False  # 초록 LED 끄기
    else:  # False일 경우 (0을 받았을 때)
        red_led.value = True  # 빨간 LED 켜기
        green_led.value = False  # 초록 LED 끄기
        lcd.message = "Entry denied"
        time.sleep(1)
    lcd.message = "Please verify your identity"


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
