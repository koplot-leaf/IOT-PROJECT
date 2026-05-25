from machine import Pin, PWM
from neopixel import NeoPixel
import BlynkLib
import network
import utime

# ========================================================
# ⚙️ [서보모터 튜닝 설정] (기존 설정값 유지)
# ========================================================
STOP_VAL = 77     
OPEN_SPEED = 40    
CLOSE_SPEED = 115  
RUN_TIME = 1.0     

# 하드웨어 핀 설정
servo = PWM(Pin(13), freq=50)
np = NeoPixel(Pin(14), 12)

# Blynk 및 Wi-Fi 정보
BLYNK_AUTH = "hNvupXmIFZOKH4yEb4foPus56NKG1JpP"
WIFI_SSID = "IOT"
WIFI_PASS = "12345678"

# Wi-Fi 연결
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASS)
while not wlan.isconnected():
    utime.sleep(0.5)

blynk = BlynkLib.Blynk(BLYNK_AUTH, insecure=True)

# 금고 제어 함수
def open_safe():
    print("🔓 금고를 엽니다!")
    blynk.virtual_write(5, 1) # 앱 LED 켜기
    np.fill((0, 30, 0))       # 초록불
    np.write()
    servo.duty(OPEN_SPEED)
    utime.sleep(RUN_TIME)
    servo.duty(STOP_VAL)

def close_safe():
    print("🔒 금고를 잠급니다.")
    blynk.virtual_write(5, 0) # 앱 LED 끄기
    np.fill((30, 0, 0))       # 빨간불
    np.write()
    servo.duty(CLOSE_SPEED)
    utime.sleep(RUN_TIME)
    servo.duty(STOP_VAL)

# 앱 버튼 제어
@blynk.on("V4")
def v4_handler(value):
    if int(value[0]) == 1:
        open_safe()
    else:
        close_safe()

# 초기 상태 세팅
servo.duty(STOP_VAL)
np.fill((30, 0, 0))
np.write()

print("시스템 준비 완료!")

# 메인 루프
while True:
    blynk.run()
    
    # 💡 [여기에 카메라 포즈 인식 코드를 넣으세요]
    # 예시:
    # pose = get_pose_from_camera()
    # if pose == 1:
    #     open_safe()
