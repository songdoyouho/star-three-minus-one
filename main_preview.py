import cv2
import time
import os
import sys
from window_capture import WindowCapture
from calculate_shanten import suggest_discard, calculate_shanten
from hand_recognizer import HandRecognizer

def analyze_frame(frame, recognizer, cache):
    """辨識手牌並計算建議；手牌沒變就沿用上次的計算結果

    Returns:
        (detections, info_lines)
    """
    res = recognizer.recognize(frame)
    hand, drawn = res['hand'], res['drawn']
    lines = []
    if not hand:
        cache.clear()
        return res['detections'], lines

    # 手牌完整（沒有認不出來的牌、張數正確）才重新計算
    full = hand + ([drawn] if drawn else [])
    if res['unknown'] == 0 and len(hand) % 3 == 1 and tuple(full) != cache.get('key'):
        cache['key'] = tuple(full)
        cache['tile'] = None
        try:
            if drawn:
                s = suggest_discard(full)
                best = s['best_options'][0]
                if s['shanten_after'] == 0:
                    detail = f"Waits: {' '.join(best['wait_tiles'])} ({best['wait_count']} left)"
                else:
                    detail = f"Improving: {best['improving_count']} tiles"
                cache['text'] = f"Discard: {s['tile']} | Shanten after: {s['shanten_after']} | {detail}"
                cache['tile'] = s['tile']
                print(f"手牌 {' '.join(full)} → 建議打 {s['tile']}：{s['reason']}")
            else:
                cache['text'] = f"Shanten: {calculate_shanten(hand)}"
        except Exception as e:
            cache['text'] = None
            print(f"建議計算失敗: {e}")

    # 建議放第一行，並在畫面上標出要打的那張牌
    if cache.get('text'):
        lines.append(cache['text'])
    if cache.get('tile'):
        target = next((d for d in res['detections'] if d['label'] == cache['tile']), None)
        if target:
            target['suggested'] = True
    lines.append(f"Hand ({len(hand)}): {' '.join(hand)}" + (f" | Drawn: {drawn}" if drawn else ""))
    if res['unknown']:
        lines.append(f"Unrecognized: {res['unknown']} tile(s) (covered or dimmed)")
    return res['detections'], lines

def draw_detections(image, detections):
    """在圖片上繪製檢測結果"""
    result_img = image.copy()
    
    for det in detections:
        x, y, w, h = det['x'], det['y'], det['w'], det['h']
        label = det['label']
        confidence = det['confidence']
        
        # 繪製邊框
        cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # 繪製標籤和信心度
        text = f"{label} ({confidence:.2f})"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        
        # 標籤背景
        cv2.rectangle(result_img, 
                    (x, y - text_size[1] - 5), 
                    (x + text_size[0], y), 
                    (0, 255, 0), -1)
        
        # 標籤文字
        cv2.putText(result_img, text, (x, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        # 建議打的牌：紅色粗框
        if det.get('suggested'):
            cv2.rectangle(result_img, (x - 4, y - 4), (x + w + 4, y + h + 4), (0, 0, 255), 10)
            cv2.putText(result_img, "DISCARD", (x - 10, y - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 4)

    return result_img

def draw_info_panel(image, lines):
    """在畫面左上角（標題列下方）畫黑底大字的資訊面板，第一行用黃色強調"""
    if not lines:
        return
    font, scale, thickness, line_h = cv2.FONT_HERSHEY_SIMPLEX, 1.3, 3, 50
    width = max(cv2.getTextSize(l, font, scale, thickness)[0][0] for l in lines) + 40
    top = 40
    cv2.rectangle(image, (0, top), (width, top + line_h * len(lines) + 20), (0, 0, 0), -1)
    for i, line in enumerate(lines):
        color = (0, 255, 255) if i == 0 else (255, 255, 255)
        cv2.putText(image, line, (20, top + 45 + i * line_h), font, scale, color, thickness)

def main():
    # 檢查是否有提供影片路徑
    use_video = False
    video_path = None
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        if os.path.exists(video_path):
            use_video = True
        else:
            print(f"警告: 找不到影片檔案: {video_path}")
            print("將使用視窗截取模式...\n")
    
    if use_video:
        # 影片模式
        print(f"使用影片模式: {video_path}")
        
        # 載入手牌樣板
        recognizer = HandRecognizer()
        print(f"\n共載入 {len(recognizer.templates)} 個樣板\n")
        cache = {}
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"錯誤: 無法開啟影片: {video_path}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"影片資訊: {total_frames} 幀, FPS: {fps:.2f}\n")
        
        is_paused = True
        frame_number = 0
        current_frame = None
        enable_detection = True  # 檢測開關
        
        # 先讀取第一幀
        ret, current_frame = cap.read()
        if not ret:
            print("錯誤: 無法讀取影片的第一幀")
            cap.release()
            return
        frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        print("操作說明:")
        print("  空白鍵: 暫停/播放")
        print("  T 鍵: 開關檢測功能")
        print("  Q 鍵: 退出\n")
        
        # 先顯示第一幀，確保視窗出現
        display_img = cv2.resize(current_frame, (0, 0), fx=0.6, fy=0.6)
        cv2.imshow('Video Preview', display_img)
        cv2.waitKey(100)
        
        loop_time = time.time()
        
        while True:
            if not is_paused:
                ret, frame = cap.read()
                if not ret:
                    is_paused = True
                    print("影片播放完畢")
                else:
                    current_frame = frame.copy()
                    frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            
            if current_frame is None:
                print("錯誤: 沒有可顯示的畫面")
                break
            
            # 辨識手牌並計算建議（如果啟用）
            detections, analysis_lines = [], []
            if enable_detection:
                detections, analysis_lines = analyze_frame(current_frame, recognizer, cache)
            
            # 繪製檢測結果
            display_img = draw_detections(current_frame, detections)
            
            # 顯示資訊
            detection_status = "ON" if enable_detection else "OFF"
            info_lines = [
                f"Frame: {frame_number}/{total_frames} | Detections: {len(detections)} [{detection_status}] | {'PAUSED' if is_paused else 'PLAYING'}"
            ]
            
            if not is_paused:
                actual_fps = 1.0 / (time.time() - loop_time) if (time.time() - loop_time) > 0 else 0
                info_lines[0] += f" | FPS: {actual_fps:.2f}"
            
            # 建議放最上面，狀態列放最後
            draw_info_panel(display_img, analysis_lines + info_lines)

            # 縮小顯示
            display_img = cv2.resize(display_img, (0, 0), fx=0.6, fy=0.6)
            cv2.imshow('Video Preview', display_img)
            
            if not is_paused:
                loop_time = time.time()
            
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):  # 空白鍵：暫停/播放
                is_paused = not is_paused
                if is_paused:
                    print("暫停")
                else:
                    print("播放")
            elif key == ord('t') or key == ord('T'):  # T 鍵：開關檢測
                enable_detection = not enable_detection
                print(f"檢測功能: {'開啟' if enable_detection else '關閉'}")
        
        cap.release()
    else:
        # 視窗截取模式
        try:
            # 初始化視窗擷取
            # 如果程式找不到視窗，它會列出所有視窗標題並拋出錯誤
            wincap = WindowCapture()
            print(f"成功鎖定視窗: {wincap.window_name}")
        except Exception as e:
            print(f"錯誤: {e}")
            print("請確認遊戲已開啟，或使用影片模式: python main_preview.py <影片路徑>")
            return

        # 載入手牌樣板
        recognizer = HandRecognizer()
        print(f"\n共載入 {len(recognizer.templates)} 個樣板\n")
        cache = {}
        
        print("操作說明:")
        print("  Q 鍵: 退出")
        print("  T 鍵: 開關檢測功能\n")

        loop_time = time.time()
        enable_detection = True  # 檢測開關

        while True:
            # 1. 獲取截圖
            screenshot = wincap.get_screenshot()

            # 辨識手牌並計算建議（如果啟用）
            detections, analysis_lines = [], []
            if enable_detection:
                detections, analysis_lines = analyze_frame(screenshot, recognizer, cache)
            
            # 3. 繪製檢測結果
            display_img = draw_detections(screenshot, detections)
            
            # 4. 顯示資訊
            detection_status = "ON" if enable_detection else "OFF"
            actual_fps = 1.0 / (time.time() - loop_time) if (time.time() - loop_time) > 0 else 0
            info_lines = [
                f"Detection: {detection_status} | Found {len(detections)} tiles | FPS: {actual_fps:.2f}",
            ]

            # 建議放最上面，狀態列放最後
            draw_info_panel(display_img, analysis_lines + info_lines)

            # 縮小一點顯示，避免擋住整個螢幕
            display_img = cv2.resize(display_img, (0, 0), fx=0.5, fy=0.5)
            cv2.imshow('Computer Vision', display_img)
            
            loop_time = time.time()

            # 按鍵處理
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('t') or key == ord('T'):  # T 鍵：開關檢測
                enable_detection = not enable_detection
                print(f"檢測功能: {'開啟' if enable_detection else '關閉'}")

    cv2.destroyAllWindows()
    print("\n程式結束")

if __name__ == '__main__':
    main()

