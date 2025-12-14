from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit

import threading    # 同時作業用
import time
import requests     # 直接控制網頁用

import cv2
import mediapipe as mp  # 僅支援至 python 3.12
import math

global run_loop

# Hand gesture code
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

# 根據兩點的座標，計算角度
def vector_2d_angle(v1, v2):
    v1_x = v1[0]
    v1_y = v1[1]
    v2_x = v2[0]
    v2_y = v2[1]
    try:
        angle_= math.degrees(math.acos((v1_x*v2_x+v1_y*v2_y)/(((v1_x**2+v1_y**2)**0.5)*((v2_x**2+v2_y**2)**0.5))))
    except:
        angle_ = 180
    return angle_

# 根據傳入的 21 個節點座標，得到該手指的角度
def hand_angle(hand_):
    angle_list = []
    # thumb 大拇指角度
    angle_ = vector_2d_angle(
        ((int(hand_[0][0])- int(hand_[2][0])),(int(hand_[0][1])-int(hand_[2][1]))),
        ((int(hand_[3][0])- int(hand_[4][0])),(int(hand_[3][1])- int(hand_[4][1])))
        )
    angle_list.append(angle_)
    # index 食指角度
    angle_ = vector_2d_angle(
        ((int(hand_[0][0])-int(hand_[6][0])),(int(hand_[0][1])- int(hand_[6][1]))),
        ((int(hand_[7][0])- int(hand_[8][0])),(int(hand_[7][1])- int(hand_[8][1])))
        )
    angle_list.append(angle_)
    # middle 中指角度
    angle_ = vector_2d_angle(
        ((int(hand_[0][0])- int(hand_[10][0])),(int(hand_[0][1])- int(hand_[10][1]))),
        ((int(hand_[11][0])- int(hand_[12][0])),(int(hand_[11][1])- int(hand_[12][1])))
        )
    angle_list.append(angle_)
    # ring 無名指角度
    angle_ = vector_2d_angle(
        ((int(hand_[0][0])- int(hand_[14][0])),(int(hand_[0][1])- int(hand_[14][1]))),
        ((int(hand_[15][0])- int(hand_[16][0])),(int(hand_[15][1])- int(hand_[16][1])))
        )
    angle_list.append(angle_)
    # pink 小拇指角度
    angle_ = vector_2d_angle(
        ((int(hand_[0][0])- int(hand_[18][0])),(int(hand_[0][1])- int(hand_[18][1]))),
        ((int(hand_[19][0])- int(hand_[20][0])),(int(hand_[19][1])- int(hand_[20][1])))
        )
    angle_list.append(angle_)
    return angle_list

# WebSocket發送功能
def ws_send_key(key):
    socketio.emit('key_event', {'key': key}, namespace='/')
    socketio.emit('key_event', {'key': key})
    print(f"Sent key: {key}")

# 根據手指角度的串列內容，返回對應的手勢名稱
def hand_pos(finger_angle):
    f1 = finger_angle[0]   # 大拇指角度
    f2 = finger_angle[1]   # 食指角度
    f3 = finger_angle[2]   # 中指角度
    f4 = finger_angle[3]   # 無名指角度
    f5 = finger_angle[4]   # 小拇指角度
    
    key = None      # key to pass
    
    if f1>=50 and f2>=50 and f3>=50 and f4>=50 and f5>=50:
        key = '0'
        ws_send_key(key)
        requests.get(f"http://127.0.0.1:5000/test/{key}")
        # test_key(key)
        # send_key_press(key)
        return '0'
    elif f1>=50 and f2<50 and f3>=50 and f4>=50 and f5>=50:
        key = '1'
        ws_send_key(key)
        # test_key(key)
        requests.get(f"http://127.0.0.1:5000/test/{key}")
        # send_key_press(key)
        return '1'
    elif f1>=50 and f2<50 and f3<50 and f4>=50 and f5>=50:
        key = '2'
        ws_send_key(key)
        # test_key(key)
        requests.get(f"http://127.0.0.1:5000/test/{key}")
        # send_key_press(key)
        return '2'
    elif f1>=50 and f2<50 and f3<50 and f4<50 and f5>50:
        key = '3'
        ws_send_key(key)
        # test_key(key)
        requests.get(f"http://127.0.0.1:5000/test/{key}")
        # send_key_press(key)
        return '3'
    elif f1>=50 and f2<50 and f3<50 and f4<50 and f5<50:
        key = '4'
        ws_send_key(key)
        # test_key(key)
        requests.get(f"http://127.0.0.1:5000/test/{key}")
        # send_key_press(key)
        return '4'
    elif f1<50 and f2<50 and f3<50 and f4<50 and f5<50:
        # send_key_press('5')
        key = '5'
        ws_send_key(key)
        # test_key(key)
        requests.get(f"http://127.0.0.1:5000/test/{key}")
        # send_key_press(key)
        return '5'
    else:
        return ''

def continuous_task():
    run_loop = True

    cap = cv2.VideoCapture(0)            # 讀取攝影機
    fontFace = cv2.FONT_HERSHEY_SIMPLEX  # 印出文字的字型
    lineType = cv2.LINE_AA               # 印出文字的邊框

    # mediapipe 啟用偵測手掌
    with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:

        if not cap.isOpened():
            print("Cannot open camera")
            exit()
        w, h = 540, 310                                  # 影像尺寸
        while run_loop:
            ret, img = cap.read()
            img = cv2.resize(img, (w,h))                 # 縮小尺寸，加快處理效率
            if not ret:
                print("Cannot receive frame")
                break
            img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 轉換成 RGB 色彩
            results = hands.process(img2)                # 偵測手勢
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    finger_points = []                   # 記錄手指節點座標的串列
                    for i in hand_landmarks.landmark:
                        # 將 21 個節點換算成座標，記錄到 finger_points
                        x = i.x*w
                        y = i.y*h
                        finger_points.append((x,y))
                    if finger_points:
                        finger_angle = hand_angle(finger_points) # 計算手指角度，回傳長度為 5 的串列
                        #print(finger_angle)                     # 印出角度 ( 有需要就開啟註解 )
                        text = hand_pos(finger_angle)            # 取得手勢所回傳的內容
                        cv2.putText(img, text, (30,120), fontFace, 5, (255,255,255), 10, lineType) # 印出文字

            cv2.imshow('oxxostudio', img)
            if cv2.waitKey(5) == ord('q'):
                break
            # Detection rate
            time.sleep(0.2) # 避免 CPU 100%
    cap.release()
    cv2.destroyAllWindows()

# Flask code

# Adjust static_folder and template_folder to point to Unity build directory
app = Flask(__name__, static_folder="./WebGL_Build/Build", template_folder="./WebGL_Build")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")



def ws_send(key):
    socketio.emit("unity_event", key, namespace="/")
    print("Sent to Unity:", key)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/test/<key>")
def test_key(key):
    ws_send_key(key)
    return f"sent key: {key}"

@app.route("/stop")
def stop_loop():
    global run_loop
    run_loop = False
    return "Stopped"


if __name__ == '__main__':
    # Start the continuous task in a separate thread
    thread = threading.Thread(target=continuous_task, daemon=True) # Daemon ensures thread exits with main program
    thread.start()
    socketio.run(app, debug=True)   # 這樣才會執行 emit