import cv2
import time
from window_capture import WindowCapture

def main():
    try:
        # 初始化視窗擷取
        # 如果程式找不到視窗，它會列出所有視窗標題並拋出錯誤
        wincap = WindowCapture()
        print(f"成功鎖定視窗: {wincap.window_name}")
    except Exception as e:
        print(f"錯誤: {e}")
        print("請確認遊戲已開啟，或修改程式碼中的視窗標題關鍵字。")
        return

    loop_time = time.time()
    
    print("按下 'q' 鍵退出預覽...")

    while True:
        # 1. 獲取截圖
        screenshot = wincap.get_screenshot()

        # 2. 這裡可以加入影像處理邏輯 (例如辨識手牌)
        # 目前先不做處理，直接顯示

        # 3. 顯示結果
        # 縮小一點顯示，避免擋住整個螢幕
        display_img = cv2.resize(screenshot, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('Computer Vision', display_img)

        # 計算並顯示 FPS
        print(f'FPS: {1 / (time.time() - loop_time):.2f}', end='\r')
        loop_time = time.time()

        # 按 'q' 退出
        if cv2.waitKey(1) == ord('q'):
            break

    cv2.destroyAllWindows()
    print("\n程式結束")

if __name__ == '__main__':
    main()

