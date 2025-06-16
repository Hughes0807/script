import pyautogui
import time
from PIL import Image

def select_region():
    """选择区域并返回坐标"""
    print("请将鼠标移动到区域的左上角位置，按回车键...")
    input()
    x1, y1 = pyautogui.position()
    print(f"已记录左上角坐标: ({x1}, {y1})")
    
    print("请将鼠标移动到区域的右下角位置，按回车键...")
    input()
    x2, y2 = pyautogui.position()
    print(f"已记录右下角坐标: ({x2}, {y2})")
    
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    
    region = (left, top, width, height)
    print(f"\n选中的区域坐标: ({left}, {top}, {width}, {height})" )
    
    return region

def capture_and_save(region, filename):
    """截图并保存"""
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save(filename)
    print(f"截图已保存为: {filename}")
    
    # 显示截图确认
    try:
        img = Image.open(filename)
        img.show()
    except Exception as e:
        print(f"无法显示图像: {e}")

def main():
    region = select_region()
    filename = "selected_region.png"
    capture_and_save(region, filename)

if __name__ == "__main__":
    main()
