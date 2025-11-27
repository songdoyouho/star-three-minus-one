import numpy as np
import cv2
import mss
import pygetwindow as gw

class WindowCapture:
    # 明星三缺一的視窗標題通常包含這些關鍵字
    DEFAULT_WINDOW_TITLE = "明星3缺1"

    def __init__(self, window_name=None):
        self.sct = mss.mss()
        
        if window_name is None:
            # 嘗試自動尋找
            self.window_name = self.find_window_by_keyword(self.DEFAULT_WINDOW_TITLE)
            if self.window_name is None:
                print(f"找不到包含 '{self.DEFAULT_WINDOW_TITLE}' 的視窗。")
                self.list_window_names()
                raise Exception(f"無法找到遊戲視窗: {self.DEFAULT_WINDOW_TITLE}")
        else:
            self.window_name = window_name

        # 獲取視窗物件
        try:
            self.window = gw.getWindowsWithTitle(self.window_name)[0]
        except IndexError:
            raise Exception(f"找不到視窗: {self.window_name}")

    def find_window_by_keyword(self, keyword):
        """尋找包含特定關鍵字的視窗標題"""
        windows = gw.getAllTitles()
        for win in windows:
            if keyword in win and win.strip() != "":
                return win
        return None

    def list_window_names(self):
        """列出所有視窗標題"""
        windows = gw.getAllTitles()
        print("\n=== 目前開啟的視窗 ===")
        for win in windows:
            if win.strip() != "":
                print(win)
        print("======================\n")

    def get_screenshot(self):
        """
        截取視窗畫面
        回傳: numpy array (OpenCV BGR 格式)
        """
        # 每次都要重新獲取位置，因為視窗可能會被移動
        # 注意：pygetwindow 的座標可能包含邊框
        monitor = {
            "top": self.window.top,
            "left": self.window.left,
            "width": self.window.width,
            "height": self.window.height
        }

        # 使用 mss 截圖
        img = np.array(self.sct.grab(monitor))

        # mss 回傳的是 BGRA，OpenCV 需要 BGR (或 BGRA 也可以，但通常轉 BGR 處理比較單純)
        # 這裡我們先轉成 BGR，去除 Alpha 通道
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        return img

    def get_window_rect(self):
        return (self.window.left, self.window.top, self.window.width, self.window.height)

