import cv2
import time
import os
import sys
import numpy as np
from window_capture import WindowCapture

def load_wan_templates(samples_dir='samples'):
    """載入萬子模板 (1m-9m)"""
    templates = {}
    for i in range(1, 10):
        filename = f"{i}m.png"
        filepath = os.path.join(samples_dir, filename)
        if os.path.exists(filepath):
            template = cv2.imread(filepath, cv2.IMREAD_COLOR)
            if template is not None:
                templates[f"{i}m"] = template
                print(f"  載入: {i}m ({template.shape[1]}x{template.shape[0]})")
    return templates

def match_templates(image, templates, threshold=0.7, scale_factor=0.5):
    """
    在圖片中進行模板匹配（優化速度版本）
    :param image: 輸入圖片
    :param templates: 模板字典 {label: template_image}
    :param threshold: 匹配閾值
    :param scale_factor: 縮放因子（降低解析度以加速，0.5 表示縮小到一半）
    :return: 檢測結果列表 [(x, y, w, h, label, confidence), ...]
    """
    detections = []
    
    # 降低圖片解析度以加速匹配
    if scale_factor < 1.0:
        small_image = cv2.resize(image, (0, 0), fx=scale_factor, fy=scale_factor)
    else:
        small_image = image
        scale_factor = 1.0
    
    for label, template in templates.items():
        h, w = template.shape[:2]
        
        # 縮放模板以匹配縮小的圖片
        if scale_factor < 1.0:
            small_template = cv2.resize(template, (0, 0), fx=scale_factor, fy=scale_factor)
        else:
            small_template = template
        
        # 檢查模板是否大於圖片
        if small_template.shape[1] > small_image.shape[1] or small_template.shape[0] > small_image.shape[0]:
            continue
        
        # 模板匹配
        result = cv2.matchTemplate(small_image, small_template, cv2.TM_CCOEFF_NORMED)
        
        # 使用更高效的方法找多個匹配點
        # 方法：找前 N 個最佳匹配點（而不是所有超過閾值的點）
        max_matches_per_template = 20  # 每種牌最多找 20 個匹配點
        
        # 先找所有超過閾值的位置
        locations = np.where(result >= threshold)
        
        # 如果匹配點太多，只取前 N 個最佳匹配
        if len(locations[0]) > 0:
            # 取得所有匹配點的信心度
            confidences = result[locations]
            # 排序並取前 N 個
            top_indices = np.argsort(confidences)[-max_matches_per_template:][::-1]
            
            for idx in top_indices:
                pt_y, pt_x = locations[0][idx], locations[1][idx]
                confidence = confidences[idx]
                
                # 將座標轉換回原始圖片大小
                x = int(pt_x / scale_factor)
                y = int(pt_y / scale_factor)
                orig_w = w
                orig_h = h
                
                detections.append({
                    'x': x,
                    'y': y,
                    'w': orig_w,
                    'h': orig_h,
                    'label': label,
                    'confidence': float(confidence)
                })
    
    # 簡單的 NMS：移除重疊的檢測結果
    if len(detections) > 0:
        # 按信心度排序
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        filtered = []
        for det in detections:
            overlap = False
            for selected in filtered:
                # 計算重疊區域
                x1 = max(det['x'], selected['x'])
                y1 = max(det['y'], selected['y'])
                x2 = min(det['x'] + det['w'], selected['x'] + selected['w'])
                y2 = min(det['y'] + det['h'], selected['y'] + selected['h'])
                
                if x2 > x1 and y2 > y1:
                    intersection = (x2 - x1) * (y2 - y1)
                    area1 = det['w'] * det['h']
                    area2 = selected['w'] * selected['h']
                    iou = intersection / (area1 + area2 - intersection)
                    
                    if iou > 0.5:  # 重疊閾值
                        overlap = True
                        break
            
            if not overlap:
                filtered.append(det)
        
        detections = filtered
    
    return detections

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
    
    return result_img

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
        
        # 載入萬子模板
        print("\n正在載入萬子模板...")
        templates = load_wan_templates()
        if len(templates) == 0:
            print("警告: 找不到萬子模板，將不進行檢測")
        else:
            print(f"共載入 {len(templates)} 個萬子模板\n")
        
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
            
            # 進行模板匹配（如果啟用）
            detections = []
            if enable_detection and len(templates) > 0:
                try:
                    # 使用 0.5 縮放因子加速（可以調整：0.3-0.7，越小越快但可能降低準確度）
                    detections = match_templates(current_frame, templates, threshold=0.65, scale_factor=0.2)
                except Exception as e:
                    print(f"檢測錯誤: {e}")
                    detections = []
            
            # 繪製檢測結果
            display_img = draw_detections(current_frame, detections)
            
            # 顯示資訊
            detection_status = "ON" if enable_detection else "OFF"
            info_text = f"Frame: {frame_number}/{total_frames} | Detections: {len(detections)} [{detection_status}] | {'PAUSED' if is_paused else 'PLAYING'}"
            if not is_paused:
                actual_fps = 1.0 / (time.time() - loop_time) if (time.time() - loop_time) > 0 else 0
                info_text += f" | FPS: {actual_fps:.2f}"
            cv2.putText(display_img, info_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
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

