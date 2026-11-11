import cv2
import os
import sys
import numpy as np

# 建立樣本存放目錄
SAMPLE_DIR = 'samples'
if not os.path.exists(SAMPLE_DIR):
    os.makedirs(SAMPLE_DIR)

print(f"樣本將儲存於: {os.path.abspath(SAMPLE_DIR)}")
print("\n=== 操作說明 ===")
print("空白鍵: 暫停/播放")
print("左/右方向鍵: 後退/前進 10 幀")
print("A/D 鍵: 後退/前進 1 幀 (精細調整)")
print("按住滑鼠左鍵框選一張牌")
print("放開後按 's' 鍵儲存樣本")
print("按 'q' 離開程式")
print("================\n")

# 全域變數
drawing = False
ix, iy = -1, -1
rect = (0, 0, 0, 0)  # x, y, w, h (相對於顯示視窗的座標)
is_paused = True
current_frame = None
display_scale_x = 1.0  # 顯示圖片與原始圖片的縮放比例
display_scale_y = 1.0

def draw_rect(event, x, y, flags, param):
    global ix, iy, drawing, rect

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        rect = (ix, iy, 0, 0)

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            w = x - ix
            h = y - iy
            rect = (ix, iy, w, h)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        w = x - ix
        h = y - iy
        # 處理反向框選
        if w < 0:
            ix = x
            w = -w
        if h < 0:
            iy = y
            h = -h
        rect = (ix, iy, w, h)

def main():
    global is_paused, current_frame, rect, display_scale_x, display_scale_y
    
    # 檢查是否有提供影片路徑
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # 預設檔名，您可以改成您的影片檔名
        video_path = 'game_video.mp4'
        print(f"使用預設影片: {video_path}")
        print("或使用: python capture_samples_from_video.py <影片路徑>")
    
    if not os.path.exists(video_path):
        print(f"錯誤: 找不到影片檔案: {video_path}")
        return
    
    # 開啟影片
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"錯誤: 無法開啟影片: {video_path}")
        return
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"影片資訊: {total_frames} 幀, FPS: {fps:.2f}")
    
    # 建立可調整大小的視窗
    cv2.namedWindow('Capture Samples from Video', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('Capture Samples from Video', draw_rect)
    
    # 設定初始視窗大小（可選，如果不設定會使用預設大小）
    # 這裡設定為原始解析度的 80%，您也可以改成其他比例
    ret, first_frame = cap.read()
    if ret:
        original_height, original_width = first_frame.shape[:2]
        initial_width = int(original_width * 0.8)
        initial_height = int(original_height * 0.8)
        cv2.resizeWindow('Capture Samples from Video', initial_width, initial_height)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重置到第一幀
    
    frame_number = 0
    
    while True:
        if not is_paused:
            ret, frame = cap.read()
            if not ret:
                # 影片結束，暫停
                is_paused = True
                print("影片播放完畢")
            else:
                current_frame = frame.copy()
                frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        else:
            # 暫停狀態，使用當前幀
            if current_frame is None:
                ret, frame = cap.read()
                if ret:
                    current_frame = frame.copy()
                    frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                else:
                    print("無法讀取影片")
                    break
        
        # 繪製當前選取框
        original_height, original_width = current_frame.shape[:2]
        
        # 獲取視窗大小
        window_rect = cv2.getWindowImageRect('Capture Samples from Video')
        window_width = window_rect[2] if window_rect[2] > 0 else original_width
        window_height = window_rect[3] if window_rect[3] > 0 else original_height
        
        # 計算縮放比例（保持長寬比）
        scale_x = window_width / original_width
        scale_y = window_height / original_height
        actual_scale = min(scale_x, scale_y)
        
        # 計算實際顯示的圖片大小和偏移
        displayed_width = int(original_width * actual_scale)
        displayed_height = int(original_height * actual_scale)
        offset_x = (window_width - displayed_width) // 2
        offset_y = (window_height - displayed_height) // 2
        
        # 儲存縮放資訊供後續使用
        display_scale_x = actual_scale
        display_scale_y = actual_scale
        
        # 建立顯示用的圖片（縮放到視窗大小）
        display_img = cv2.resize(current_frame, (displayed_width, displayed_height))
        
        # 如果有偏移，在黑色背景上居中顯示
        if offset_x > 0 or offset_y > 0:
            full_display = np.zeros((window_height, window_width, 3), dtype=np.uint8)
            full_display[offset_y:offset_y+displayed_height, offset_x:offset_x+displayed_width] = display_img
            display_img = full_display
        
        # 繪製選取框（座標已經是顯示座標）
        if rect[2] > 0 and rect[3] > 0:
            x, y, w, h = rect
            cv2.rectangle(display_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # 顯示幀數資訊
        info_text = f"Frame: {frame_number}/{total_frames} | {'PAUSED' if is_paused else 'PLAYING'}"
        cv2.putText(display_img, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Capture Samples from Video', display_img)
        
        key = cv2.waitKey(30) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord(' '):  # 空白鍵：暫停/播放
            is_paused = not is_paused
            print(f"{'暫停' if is_paused else '播放'}")
        elif key == 81 or key == 2:  # 左方向鍵 (Linux/Windows)
            # 後退 10 幀
            new_frame = max(0, frame_number - 10)
            cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)
            ret, frame = cap.read()
            if ret:
                current_frame = frame.copy()
                frame_number = new_frame
                is_paused = True
        elif key == 83 or key == 3:  # 右方向鍵 (Linux/Windows)
            # 前進 10 幀
            new_frame = min(total_frames - 1, frame_number + 10)
            cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)
            ret, frame = cap.read()
            if ret:
                current_frame = frame.copy()
                frame_number = new_frame
                is_paused = True
        elif key == ord('a') or key == ord('A'):  # A 鍵：後退 1 幀
            new_frame = max(0, frame_number - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)
            ret, frame = cap.read()
            if ret:
                current_frame = frame.copy()
                frame_number = new_frame
                is_paused = True
        elif key == ord('d') or key == ord('D'):  # D 鍵：前進 1 幀
            new_frame = min(total_frames - 1, frame_number + 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)
            ret, frame = cap.read()
            if ret:
                current_frame = frame.copy()
                frame_number = new_frame
                is_paused = True
        elif key == ord('s'):
            # 儲存選取區域
            if rect[2] > 0 and rect[3] > 0:
                # 將顯示座標轉換回原始圖片座標
                x_display, y_display, w_display, h_display = rect
                
                # 重新計算縮放和偏移（與顯示時一致）
                original_height, original_width = current_frame.shape[:2]
                window_rect = cv2.getWindowImageRect('Capture Samples from Video')
                window_width = window_rect[2] if window_rect[2] > 0 else original_width
                window_height = window_rect[3] if window_rect[3] > 0 else original_height
                
                scale_x = window_width / original_width
                scale_y = window_height / original_height
                actual_scale = min(scale_x, scale_y)
                
                displayed_width = int(original_width * actual_scale)
                displayed_height = int(original_height * actual_scale)
                offset_x = (window_width - displayed_width) // 2
                offset_y = (window_height - displayed_height) // 2
                
                # 調整座標（減去黑邊偏移）
                x_display_adjusted = x_display - offset_x
                y_display_adjusted = y_display - offset_y
                
                # 轉換到原始圖片座標
                if actual_scale > 0:
                    x = max(0, int(x_display_adjusted / actual_scale))
                    y = max(0, int(y_display_adjusted / actual_scale))
                    w = max(1, int(w_display / actual_scale))
                    h = max(1, int(h_display / actual_scale))
                else:
                    x, y, w, h = max(0, x_display), max(0, y_display), max(1, w_display), max(1, h_display)
                
                # 確保座標不超出邊界
                x = min(x, original_width - 1)
                y = min(y, original_height - 1)
                w = min(w, original_width - x)
                h = min(h, original_height - y)
                
                # 調試資訊
                print(f"\n[Debug] 顯示座標: ({x_display}, {y_display}, {w_display}, {h_display})")
                print(f"[Debug] 偏移: ({offset_x}, {offset_y}), 縮放: {actual_scale:.4f}")
                print(f"[Debug] 原始座標: ({x}, {y}, {w}, {h})")
                print(f"[Debug] 原始圖片大小: {original_width}x{original_height}")
                
                if w > 0 and h > 0 and x >= 0 and y >= 0:
                    roi = current_frame[y:y+h, x:x+w].copy()
                    
                    if roi.size > 0 and roi.shape[0] > 0 and roi.shape[1] > 0:
                        # 顯示預覽（放大以便檢查）
                        preview = cv2.resize(roi, (0, 0), fx=3, fy=3)
                        cv2.imshow('Preview', preview)
                        print(f"[Frame {frame_number}] 選取區域: ({x}, {y}, {w}, {h})")
                        print("請輸入檔案名稱 (例如 1m=一萬, 2p=二筒, 3s=三條): ", end='')
                        
                        filename = input()
                        
                        if filename:
                            filepath = os.path.join(SAMPLE_DIR, f"{filename}.png")
                            success = cv2.imwrite(filepath, roi)
                            if success:
                                print(f"✓ 已儲存: {filepath} (大小: {w}x{h})")
                            else:
                                print(f"✗ 儲存失敗: {filepath}")
                        else:
                            print("取消儲存")
                        
                        cv2.destroyWindow('Preview')
                    else:
                        print(f"✗ ROI 無效: shape={roi.shape if hasattr(roi, 'shape') else 'N/A'}")
                else:
                    print(f"✗ 座標無效: x={x}, y={y}, w={w}, h={h}")
            else:
                print("請先框選區域")
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n程式結束")

if __name__ == '__main__':
    main()

