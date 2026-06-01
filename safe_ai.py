import cv2
import numpy as np
import requests
import time
import tensorflow as tf

# [설정]
BLYNK_AUTH = "hNvupXmIFZOKH4yEb4foPus56NKG1JpP"
SECRET_PASSWORD = ["Pose1", "Pose2", "Pose3"]
MODEL = tf.lite.Interpreter(model_path="model.tflite")
MODEL.allocate_tensors()
LABELS = [line.strip().split()[-1] for line in open("labels.txt", "r")]

def control_safe(action):
    """Blynk 서버로 금고 열림(1) 또는 닫힘(0) 명령 전송"""
    url = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH}&V4={action}"
    try:
        requests.get(url, timeout=3)
        print(f"✅ 서버 명령 성공: {action}")
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

# [초기화]
camera = cv2.VideoCapture(0)
input_idx = MODEL.get_input_details()[0]['index']
output_idx = MODEL.get_output_details()[0]['index']
seq = []
last_pose = ""

print("🔒 AI 금고 시작!")

while True:
    ret, frame = camera.read()
    if not ret: break

    # 1. 이미지 전처리
    img = cv2.resize(frame, (224, 224))
    img = np.expand_dims(img.astype(np.float32) / 127.5 - 1, axis=0)
    
    # 2. AI 예측
    MODEL.set_tensor(input_idx, img)
    MODEL.invoke()
    pred = MODEL.get_tensor(output_idx)[0]
    
    idx = np.argmax(pred)
    pose = "".join([c for c in LABELS[idx] if c.isalpha() or c.isdigit()])
    conf = pred[idx]

    # 3. 로직 처리 (정확도 80% 이상 & 새로운 포즈일 때)
    if conf > 0.8 and pose != last_pose and pose != "Idle":
        print(f"🎵 감지: {pose}")
        
        # 비밀번호 시퀀스 검사
        if pose in SECRET_PASSWORD:
            if pose == SECRET_PASSWORD[len(seq)]:
                seq.append(pose)
                if seq == SECRET_PASSWORD:
                    control_safe(1)
                    seq = [] # 초기화
            else:
                seq = [] # 틀리면 초기화
        
        # 닫기 포즈 인식 시
        elif pose == "close":
            control_safe(0)
            
        last_pose = pose
        time.sleep(0.5)

    cv2.imshow("Webcam", frame)
    if cv2.waitKey(1) == 27: break

camera.release()
cv2.destroyAllWindows()
