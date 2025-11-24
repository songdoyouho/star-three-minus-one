import cv2
import time
from datetime import datetime
from window_capture import WindowCapture

def main():
    try:
        wincap = WindowCapture()
        print(f"成功鎖定視窗: {wincap.window_name}")
    except Exception as e:
        print(f"錯誤: {e}")
        return

    print("\n=== 錄影控制 ===")
    print("按 'r' 鍵開始/停止錄影")
    print("按 'q' 鍵退出程式")
    print("================\n")

    recording = False
    video_writer = None
    fps = 30.0  # 錄影 FPS
    output_filename = None

    loop_time = time.time()
    frame_time = 1.0 / fps

    while True:
        # 獲取截圖
        screenshot = wincap.get_screenshot()
        height, width = screenshot.shape[:2]

        # 如果正在錄影，寫入影片
        if recording:
            if video_writer is None:
                # 初始化 VideoWriter
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"recorded_video\game_recording_{timestamp}.mp4"
                
                # 使用 MP4V codec (四字符代碼)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(
                    output_filename, 
                    fourcc, 
                    fps, 
                    (width, height)
                )
                print(f"開始錄影: {output_filename}")

            video_writer.write(screenshot)
        else:
            # 停止錄影時關閉 writer
            if video_writer is not None:
                video_writer.release()
                video_writer = None
                print(f"錄影已停止並儲存: {output_filename}")

        # 顯示狀態
        display_img = screenshot.copy()
        status_text = "RECORDING" if recording else "STANDBY"
        status_color = (0, 0, 255) if recording else (0, 255, 0)
        
        # 在畫面上顯示錄影狀態
        cv2.putText(display_img, status_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        
        # 如果正在錄影，顯示紅色圓點
        if recording:
            cv2.circle(display_img, (width - 30, 30), 15, (0, 0, 255), -1)

        # 縮小顯示
        display_img = cv2.resize(display_img, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('Game Recorder', display_img)

        # 控制 FPS
        elapsed = time.time() - loop_time
        if elapsed < frame_time:
            time.sleep(frame_time - elapsed)
        
        # 計算並顯示實際 FPS
        actual_fps = 1.0 / (time.time() - loop_time)
        print(f'FPS: {actual_fps:.2f} | {status_text}', end='\r')
        loop_time = time.time()

        # 按鍵控制
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            # 如果還在錄影，先停止
            if recording and video_writer is not None:
                video_writer.release()
                print(f"\n錄影已儲存: {output_filename}")
            break
        elif key == ord('r'):
            recording = not recording

    cv2.destroyAllWindows()
    print("\n程式結束")

if __name__ == '__main__':
    main()

