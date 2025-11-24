import cv2
import os
import sys

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
rect = (0, 0, 0, 0)  # x, y, w, h
is_paused = True
current_frame = None

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
    global is_paused, current_frame, rect
    
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
    
    cv2.namedWindow('Capture Samples from Video')
    cv2.setMouseCallback('Capture Samples from Video', draw_rect)
    
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
        display_img = current_frame.copy()
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
                x, y, w, h = rect
                # 確保座標不超出邊界
                x = max(0, x)
                y = max(0, y)
                w = min(w, current_frame.shape[1] - x)
                h = min(h, current_frame.shape[0] - y)
                
                if w > 0 and h > 0:
                    roi = current_frame[y:y+h, x:x+w]
                    cv2.imshow('Preview', roi)
                    print(f"\n[Frame {frame_number}] 請輸入檔案名稱 (例如 1m=一萬, 2p=二筒, 3s=三條): ", end='')
                    
                    filename = input()
                    
                    if filename:
                        filepath = os.path.join(SAMPLE_DIR, f"{filename}.png")
                        cv2.imwrite(filepath, roi)
                        print(f"已儲存: {filepath}")
                    else:
                        print("取消儲存")
                    
                    cv2.destroyWindow('Preview')
                else:
                    print("選取區域無效")
            else:
                print("請先框選區域")
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n程式結束")

if __name__ == '__main__':
    main()

