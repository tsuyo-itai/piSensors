import RPi.GPIO as GPIO
from picamera import PiCamera
import signal
from datetime import datetime
import time

ObstaclePin = 14
BuzzerPin = 17

# 意図的に発生させる例外クラス
class CallException(Exception):
    def __init__(self, message="Call exception occurred."):
        self.message = message
        super().__init__(self.message)

class DetectController:
    def __init__(self):
        # カメラの初期化
        try:
            self.camera = PiCamera()
            # 解像度
            self.camera.resolution = (1024, 768)
            # self.camera.resolution = (680, 480)

        except Exception as e:
            print(f"[WARNING] Camera module not connected: {e}")
            self.camera = None

        # 連続でカメラ撮影を行わないよう状態を管理
        self.last_shot_ut = 0
        self.detected = False

        # 初期化
        self.setup()

    def setup(self):
        GPIO.setmode(GPIO.BCM)
        # 赤外線障害物センサーの初期化
        GPIO.setup(ObstaclePin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # ブザーの初期化
        GPIO.setup(BuzzerPin, GPIO.OUT)
        GPIO.output(BuzzerPin, GPIO.LOW)

        # カメラのウォームアップを行う
        if self.camera is not None:
            self.camera_warmup()

        # シグナルハンドラの設定
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def camera_warmup(self):
        # カメラのウォームアップを行う
        self.camera.start_preview()
        time.sleep(2)
        self.camera.stop_preview()

    def signal_handler(self, sig, frame):
        raise CallException(f"Signal handler called. signal={sig}")

    def camera_shot(self):
        now_ut = int(time.time())
        if self.is_detected() is not True and self.last_shot_ut <= now_ut - 300:
            self.camera.capture('./detected.jpg')
            self.last_shot_ut = now_ut
            print(f'[INFO] camera shot. ({datetime.fromtimestamp(now_ut).strftime("%Y/%m/%d %H:%M:%S")})')

    def set_detected(self, value):
        """Setter method to set the detected attribute."""
        self.detected = value
    
    def is_detected(self):
        return self.detected

    def loop(self):
        print("[INFO] Monitoring Start.")
        while True:
            if (0 != GPIO.input(ObstaclePin)):
                GPIO.output(BuzzerPin, GPIO.HIGH)
                # カメラで撮影する
                if self.camera is not None:
                    self.camera_shot()
                self.set_detected(True)
            else:
                GPIO.output(BuzzerPin, GPIO.LOW)
                self.set_detected(False)

            time.sleep(0.1)

    def destroy(self):
        GPIO.cleanup()

if __name__ == '__main__':
    detect_controller = DetectController()

    try:
        detect_controller.loop()
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
    finally:
        detect_controller.destroy()