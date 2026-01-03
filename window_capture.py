import numpy as np
import cv2
import mss
import platform
import time

# 根據平台匯入不同套件
IS_MAC = platform.system() == 'Darwin'

if IS_MAC:
    try:
        import Quartz
        import Quartz.CoreGraphics as CG
        from Cocoa import NSBitmapImageRep
        from Foundation import NSData
    except ImportError:
        print("警告: macOS 模式需要 pyobjc-framework-Quartz 和 pyobjc-framework-Cocoa")
else:
    # Windows 模式
    try:
        import pygetwindow as gw
    except ImportError:
        print("警告: Windows 模式需要 pygetwindow")

class WindowCapture:
    # 遊戲視窗可能的標題關鍵字
    TARGET_KEYWORDS = ["明星3缺1", "Star31", "Star 3 missing 1"]
    
    def __init__(self, window_name=None):
        self.window_name = window_name
        self.window_rect = None # (x, y, w, h)
        
        # Windows 專用屬性
        self.sct = None
        self.window = None
        
        # Mac 專用屬性
        self.window_id = None

        if IS_MAC:
            self._init_mac()
        else:
            self._init_windows()

    def _init_mac(self):
        if self.window_name is None:
            # 自動搜尋視窗
            self.window_id = self.find_window_id_mac()
            if not self.window_id:
                print("找不到遊戲視窗。列出目前所有視窗供參考：")
                self.list_window_names_mac()
                raise Exception(f"無法找到包含以下關鍵字的視窗: {self.TARGET_KEYWORDS}")
        else:
            # 指定名稱搜尋
            self.window_id = self.find_window_id_mac(specific_name=self.window_name)
            if not self.window_id:
                raise Exception(f"找不到視窗: {self.window_name}")

    def _init_windows(self):
        self.sct = mss.mss()
        if self.window_name is None:
            # 自動搜尋
            self.window_name = self.find_window_by_keyword_win(self.TARGET_KEYWORDS)
            if self.window_name is None:
                self.list_window_names_win()
                raise Exception(f"無法找到包含以下關鍵字的視窗: {self.TARGET_KEYWORDS}")
        
        # 獲取視窗物件
        try:
            self.window = gw.getWindowsWithTitle(self.window_name)[0]
        except IndexError:
            raise Exception(f"找不到視窗: {self.window_name}")
        
        # 初始視窗位置
        self.window_rect = (self.window.left, self.window.top, self.window.width, self.window.height)

    # ================= Windows Methods =================
    def find_window_by_keyword_win(self, keywords):
        windows = gw.getAllTitles()
        for win in windows:
            if win.strip() == "": continue
            for key in keywords:
                if key in win:
                    return win
        return None

    def list_window_names_win(self):
        windows = gw.getAllTitles()
        print("\n=== 目前開啟的視窗 (Windows) ===")
        for win in windows:
            if win.strip() != "":
                print(win)
        print("======================\n")

    def get_screenshot_win(self):
        # 每次都要重新獲取位置
        monitor = {
            "top": self.window.top,
            "left": self.window.left,
            "width": self.window.width,
            "height": self.window.height
        }
        
        try:
            img = np.array(self.sct.grab(monitor))
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
        except Exception as e:
            # print(f"Windows 截圖失敗: {e}")
            return None

    # ================= Mac Methods =================
    def find_window_id_mac(self, specific_name=None):
        options = CG.kCGWindowListOptionOnScreenOnly | CG.kCGWindowListExcludeDesktopElements
        window_list = CG.CGWindowListCopyWindowInfo(options, CG.kCGNullWindowID)

        for window in window_list:
            title = window.get('kCGWindowName', '')
            owner = window.get('kCGWindowOwnerName', '')
            win_id = window.get('kCGWindowNumber', 0)
            
            if not title and not owner:
                continue

            match = False
            if specific_name:
                if specific_name in title or specific_name in owner:
                    match = True
            else:
                for keyword in self.TARGET_KEYWORDS:
                    if (title and keyword in title) or (owner and keyword in owner):
                        match = True
                        print(f"找到目標視窗 ID: {win_id} | Title: {title} | Owner: {owner}")
                        if not self.window_name:
                            self.window_name = title if title else owner
                        break
            
            if match:
                bounds = window.get('kCGWindowBounds')
                self.window_rect = (
                    int(bounds['X']), 
                    int(bounds['Y']), 
                    int(bounds['Width']), 
                    int(bounds['Height'])
                )
                return win_id
        return None

    def list_window_names_mac(self):
        options = CG.kCGWindowListOptionOnScreenOnly | CG.kCGWindowListExcludeDesktopElements
        window_list = CG.CGWindowListCopyWindowInfo(options, CG.kCGNullWindowID)
        print("\n=== 目前開啟的視窗 (Mac) ===")
        for window in window_list:
            title = window.get('kCGWindowName', '[No Title]')
            owner = window.get('kCGWindowOwnerName', '[No Owner]')
            win_id = window.get('kCGWindowNumber', 0)
            print(f"ID: {win_id} | Owner: {owner} | Title: {title}")
        print("============================\n")

    def get_screenshot_mac(self):
        if not self.window_id:
            return None

        image_option = CG.kCGWindowListOptionIncludingWindow
        cg_image = CG.CGWindowListCreateImage(
            CG.CGRectNull,
            image_option,
            self.window_id,
            CG.kCGWindowImageBoundsIgnoreFraming | CG.kCGWindowImageNominalResolution
        )

        if not cg_image:
            return None

        width = CG.CGImageGetWidth(cg_image)
        height = CG.CGImageGetHeight(cg_image)
        
        if width == 0 or height == 0:
            return None

        prov = CG.CGImageGetDataProvider(cg_image)
        data = CG.CGDataProviderCopyData(prov)
        
        try:
            bytes_per_row = CG.CGImageGetBytesPerRow(cg_image)
            np_data = np.frombuffer(data, dtype=np.uint8)
            
            if len(np_data) < height * bytes_per_row:
                return None
                
            img_reshaped = np_data.reshape((height, bytes_per_row))
            img = img_reshaped[:, :width * 4]
            img = img.reshape((height, width, 4))
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img_bgr

        except Exception:
            return None

    # ================= Public Methods =================
    def get_screenshot(self):
        if IS_MAC:
            return self.get_screenshot_mac()
        else:
            return self.get_screenshot_win()

    def get_window_rect(self):
        if IS_MAC:
            # Mac 模式下如果需要即時更新位置，可能需要重抓，這裡先回傳初始位置
            return self.window_rect
        else:
            # Windows 模式下可以直接讀取當前屬性
            return (self.window.left, self.window.top, self.window.width, self.window.height)
