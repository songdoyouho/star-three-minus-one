import cv2
import time
import os
import sys
from window_capture import WindowCapture
from calculate_shanten import (suggest_discard, calculate_shanten, safest_discards, suggest_claim,
                               suggest_self_kan, is_winning)
from hand_recognizer import HandRecognizer
from table_recognizer import TableRecognizer
from claim_recognizer import ClaimRecognizer
from meld_recognizer import MeldRecognizer

def _claim_advice(hand, tile, buttons, visible):
    """別人打出 tile、出現吃碰按鈕時的建議，回傳 (顯示文字, 建議按的按鈕)"""
    s = suggest_claim(hand, tile, 'chi' in buttons, visible)
    best = s['best']
    print(f"別人打 {tile}，手牌 {' '.join(hand)} → {s['reason']}")
    if s['action'] == 'win':
        return f"Claim: HU! Win on {tile}", 'hu'
    if s['action'] == 'pass':
        return f"Claim: PASS on {tile} (shanten stays {best['shanten']})", 'cancel'
    text = f"Claim: {s['action'].upper()} {' '.join(best['meld'])}"
    if best['discard']:
        text += f", then discard {best['discard']}"
    return text + f" | Shanten {s['options'][0]['shanten']} -> {best['shanten']}", s['action']

def analyze_frame(frame, recognizer, cache, table=None, claim=None, meld=None):
    """辨識手牌（和桌上看得到的牌）並計算建議；都沒變就沿用上次的計算結果

    Args:
        table: TableRecognizer，給的話會辨識牌河，扣掉已出現的牌並給防守提示
        claim: ClaimRecognizer，給的話出現吃碰槓胡按鈕時會建議要按哪個
        meld: MeldRecognizer，給的話會辨識自己吃碰的牌（算進看得到的牌、判斷加槓）
    Returns:
        (detections, info_lines)
    """
    res = recognizer.recognize(frame)
    hand, drawn = res['hand'], res['drawn']
    lines = []
    if not hand:
        cache.clear()
        return res['detections'], lines

    # 吃碰槓胡按鈕和放大顯示的那張打出的牌
    claim_info = claim.recognize(frame) if claim is not None else None

    # 自己吃碰槓的牌（在第一張手牌左邊）
    visible, meld_dets, pons, meld_info = [], [], [], None
    if meld is not None:
        meld_info = meld.recognize(frame, min(d['x'] for d in res['detections']))
        visible += [t for t in meld_info['tiles'] if t != '?']
        pons = [g[0] for g in meld_info['melds'] if len(g) == 3 and len(set(g)) == 1 and g[0] != '?']
        meld_dets = meld_info['detections']
        for d in meld_dets:
            d['table'] = True

    # 桌上的牌（自己的手牌、吃碰的牌、放大的那張牌不掃，避免重複算到）
    table_dets = []
    if table is not None:
        exclude = [(d['x'], d['y'], d['w'], d['h']) for d in res['detections']]
        if claim_info and claim_info['tile_box']:
            exclude.append(claim_info['tile_box'])
        if meld_info:
            exclude.append(meld_info['area'])
        t = table.recognize(frame, exclude)
        visible += t['tiles']
        table_dets = t['detections']
        for d in table_dets:
            d['table'] = True

    # 手牌完整（沒有認不出來的牌、張數正確）才重新計算
    full = hand + ([drawn] if drawn else [])
    key = (tuple(full), tuple(sorted(visible)), tuple(pons))
    if res['unknown'] == 0 and len(hand) % 3 == 1 and key != cache.get('key'):
        cache['key'] = key
        cache['tile'] = None
        cache['defense'] = None
        cache['tsumo'] = False
        cache['kan'] = None
        try:
            if drawn and is_winning(full):
                cache['text'] = f"TSUMO! You win with {drawn} (press HU)"
                cache['tsumo'] = True
                print(f"手牌 {' '.join(full)} → 自摸！")
            elif drawn:
                s = suggest_discard(full, visible)
                best = s['best_options'][0]
                if s['shanten_after'] == 0:
                    detail = f"Waits: {' '.join(best['wait_tiles'])} ({best['wait_count']} left)"
                else:
                    detail = f"Improving: {best['improving_count']} tiles"
                cache['text'] = f"Discard: {s['tile']} | Shanten after: {s['shanten_after']} | {detail}"
                cache['tile'] = s['tile']
                if table is not None:
                    safe = safest_discards(full, visible)
                    seen = dict(safe)
                    cache['defense'] = (f"Defense: safest {safe[0][0]} ({safe[0][1]} seen)"
                                        f" | {s['tile']} has {seen[s['tile']]} seen")
                print(f"手牌 {' '.join(full)} → 建議打 {s['tile']}：{s['reason']}")
                k = suggest_self_kan(full, pons, visible)
                if k['action'] == 'kan':
                    kind = 'concealed' if k['best']['type'] == 'concealed' else 'added'
                    cache['kan'] = f"KAN: {k['best']['tile']} ({kind}) | Shanten stays {k['best']['shanten']}"
                if k['options']:
                    print(f"  槓：{k['reason']}")
            else:
                cache['text'] = f"Shanten: {calculate_shanten(hand)}"
        except Exception as e:
            cache['text'] = None
            print(f"建議計算失敗: {e}")

    # 出現吃碰槓胡按鈕：建議要不要吃碰（輪到別人出牌時手上是 3k+1 張、沒有摸牌）
    button = None
    if claim_info and claim_info['tile'] and not drawn and res['unknown'] == 0 and len(hand) % 3 == 1:
        ckey = (tuple(hand), claim_info['tile'], tuple(claim_info['buttons']), tuple(sorted(visible)))
        if ckey != cache.get('claim_key'):
            cache['claim_key'] = ckey
            try:
                cache['claim'] = _claim_advice(hand, claim_info['tile'], claim_info['buttons'], visible)
            except Exception as e:
                cache['claim'] = None
                print(f"吃碰建議計算失敗: {e}")
        if cache.get('claim'):
            lines.append(cache['claim'][0])
            button = cache['claim'][1]
    elif claim_info and cache.get('tsumo'):
        button = 'hu'
    elif claim_info and cache.get('kan') and drawn:
        button = 'kan'
    button_dets = []
    if button:
        x, y, w, h = claim_info['button_boxes'][button]
        button_dets.append({'x': x, 'y': y, 'w': w, 'h': h, 'label': button.upper(), 'confidence': 1.0,
                            'suggested': True, 'action': button.upper()})

    # 建議放第一行，並在畫面上標出要打的那張牌
    if cache.get('kan') and drawn:
        lines.append(cache['kan'])
    if cache.get('text'):
        lines.append(cache['text'])
    if cache.get('defense'):
        lines.append(cache['defense'])
    if cache.get('tile'):
        target = next((d for d in res['detections'] if d['label'] == cache['tile']), None)
        if target:
            target['suggested'] = True
    lines.append(f"Hand ({len(hand)}): {' '.join(hand)}" + (f" | Drawn: {drawn}" if drawn else ""))
    if meld_info and meld_info['melds']:
        lines.append("Melds: " + " | ".join(' '.join(g) for g in meld_info['melds']))
    if table is not None:
        lines.append(f"Seen on table: {len(visible)} tiles")
    if res['unknown']:
        lines.append(f"Unrecognized: {res['unknown']} tile(s) (covered or dimmed)")
    return res['detections'] + meld_dets + table_dets + button_dets, lines

def draw_detections(image, detections):
    """在圖片上繪製檢測結果"""
    result_img = image.copy()
    
    for det in detections:
        x, y, w, h = det['x'], det['y'], det['w'], det['h']
        label = det['label']
        confidence = det['confidence']

        # 桌上的牌：細的青色框，只標牌名
        if det.get('table'):
            cv2.rectangle(result_img, (x, y), (x + w, y + h), (255, 255, 0), 1)
            cv2.putText(result_img, label, (x, y + h + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            continue

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
            cv2.putText(result_img, det.get('action', 'DISCARD'), (x - 10, y - 30),
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
        table = TableRecognizer()
        claim = ClaimRecognizer()
        meld = MeldRecognizer()
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
                detections, analysis_lines = analyze_frame(current_frame, recognizer, cache, table, claim, meld)
            
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
        table = TableRecognizer()
        claim = ClaimRecognizer()
        meld = MeldRecognizer()
        print(f"\n共載入 {len(recognizer.templates)} 個樣板\n")
        cache = {}
        
        print("操作說明:")
        print("  Q 鍵: 退出")
        print("  T 鍵: 開關檢測功能")
        print("  S 鍵: 存下目前畫面（有牌認錯或認不出來時按）\n")

        loop_time = time.time()
        enable_detection = True  # 檢測開關

        while True:
            # 1. 獲取截圖
            screenshot = wincap.get_screenshot()

            # 辨識手牌並計算建議（如果啟用）
            detections, analysis_lines = [], []
            if enable_detection:
                detections, analysis_lines = analyze_frame(screenshot, recognizer, cache, table, claim, meld)
            
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
            elif key == ord('s') or key == ord('S'):  # S 鍵：存下原始畫面，給辨識錯誤時回報用
                os.makedirs('screenshots', exist_ok=True)
                path = os.path.join('screenshots', 'miss_' + time.strftime('%Y%m%d_%H%M%S') + '.png')
                cv2.imencode('.png', screenshot)[1].tofile(path)
                print(f"已存下畫面: {path}")

    cv2.destroyAllWindows()
    print("\n程式結束")

if __name__ == '__main__':
    main()

