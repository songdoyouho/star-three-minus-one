"""每隔幾秒自動截取遊戲視窗，存到 screenshots/，用來製作樣板圖

用法: python capture_screenshots.py [間隔秒數，預設 3]
按 Ctrl+C 結束
"""
import os
import sys
import time
from datetime import datetime

import cv2

from vision_observer.window_capture import WindowCapture

OUTPUT_DIR = 'screenshots'


def main():
    interval = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    wincap = WindowCapture()
    print(f"成功鎖定視窗: {wincap.window_name}")
    print(f"每 {interval} 秒存一張到 {os.path.abspath(OUTPUT_DIR)}，按 Ctrl+C 結束")

    count = 0
    try:
        while True:
            img = wincap.get_screenshot()
            if img is not None:
                path = os.path.join(OUTPUT_DIR, datetime.now().strftime('%Y%m%d_%H%M%S') + '.png')
                cv2.imwrite(path, img)
                count += 1
                print(f"[{count}] {path} ({img.shape[1]}x{img.shape[0]})")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n結束，共存了 {count} 張")


if __name__ == '__main__':
    main()
