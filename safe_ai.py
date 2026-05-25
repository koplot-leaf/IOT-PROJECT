import cv2
import numpy as np
import requests
import time
import tensorflow as tf

# 💡 이제 h5 파일 대신 tflite 파일을 씁니다.
MODEL_PATH = "model.tflite"  
LABELS_PATH = "labels.txt"  
BLYNK_AUTH = "hNvupXmIFZOKH4yEb4foPus56NKG1JpP" 
SECRET_PASSWORD = ["Pose1", "Pose2", "Pose3"]

def send_to_blynk(value):
    # 서버 주소를 더 범용적인 blynk.cloud로 수정
    url = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH}&V4={value}"
    try:
        # 3초 동안 응답이 없으면 포기하도록 설정
        response = requests.get(url, timeout=3)
        print(f"📡 서버 응답 코드: {response.status_code}") 
        if response.status_code == 200:
            print(f"✅ [성공] Blynk 서버로 {value} 신호 전송 완료!")
        else:
            print(f"⚠️ [주의] 서버 응답이 이상합니다: {response.status_code}")
    except Exception as e:
        print(f"❌ [전송 에러 발생] : {e}")
        print("💡 팁: 지금 컴퓨터가 인터넷에 연결되어 있는지, 혹은 방화벽(학교/회사)에 막혀있지 않은지 확인하세요!")

# TFLite 모델 로드
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
class_names = [line.strip() for line in open(LABELS_PATH, "r").readlines()]

camera = cv2.VideoCapture(0)
current_sequence = []
last_detected_pose = "Idle"
safe_opened = False  

print("🔒 AI 금고 가동 중... (ESC로 종료)")

while True:
    ret, image = camera.read()
    if not ret: break

    img_data = cv2.resize(image, (224, 224))
    img_data = np.expand_dims(img_data, axis=0).astype(np.float32) / 127.5 - 1
    
    interpreter.set_tensor(input_details[0]['index'], img_data)
    interpreter.invoke()
    prediction = interpreter.get_tensor(output_details[0]['index'])[0]

    index = np.argmax(prediction)
    # 💡 라벨명에서 숫자/공백 제거 (예: "2 Pose2" -> "Pose2")
    class_name = "".join([c for c in class_names[index].split()[-1] if c.isalpha() or c.isdigit()])
    confidence = prediction[index]

    if confidence > 0.8:
        if class_name != last_detected_pose and class_name != "Idle":
            print(f"🎵 감지됨: {class_name}")
            if not safe_opened and class_name in SECRET_PASSWORD:
                if class_name == SECRET_PASSWORD[len(current_sequence)]:
                    current_sequence.append(class_name)
                    if current_sequence == SECRET_PASSWORD:
                        send_to_blynk(1)
                        safe_opened = True
                        current_sequence = []
                else:
                    current_sequence = []
            elif safe_opened and class_name == "close":
                send_to_blynk(0)
                safe_opened = False
            last_detected_pose = class_name
            time.sleep(0.5)

    cv2.imshow("Webcam", image)
    if cv2.waitKey(1) == 27: break

camera.release()
cv2.destroyAllWindows()
