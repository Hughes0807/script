import pyautogui
import time

print("5秒后开始获取鼠标位置，请将鼠标移动到目标区域...")
time.sleep(1)

try:
    while True:
        x, y = pyautogui.position()
        print(f"当前坐标：({x}, {y})", end="\r")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n坐标获取已停止。")
