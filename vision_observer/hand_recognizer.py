"""辨識明星3缺1（6.9.x 版）畫面上的手牌

手牌是正面、大小固定的牌，靠右對齊排在固定格子上，摸進的牌在最右邊另一格。
所以不用在整個畫面上找，直接對每一格做樣板比對即可。
座標以 2566x1386 的視窗截圖為準，其他大小的畫面會先縮放到這個大小。
"""
import os

import cv2
import numpy as np

REF_W, REF_H = 2566, 1386          # 量測座標時的視窗截圖大小
TILE_W, TILE_H = 130, 188          # 手牌大小
TILE_Y = 1014                      # 手牌上緣（沒被選取時）
LAST_SLOT_X = 2150                 # 最右邊一張手牌的左緣
SLOT_PITCH = (2150 - 115) / 15     # 手牌間距（16 張從 x=115 排到 x=2150）
DRAWN_X = 2325                     # 摸進那張牌的左緣
NUM_SLOTS = 16
SEARCH_X = 8                       # 左右容許誤差
SEARCH_UP = 70                     # 被選取的牌會往上浮
SEARCH_DOWN = 6
THRESHOLD = 0.8                    # 低於這個分數視為認不出來
MATCH_SCALE = 0.5                  # 比對前縮小，速度快一倍以上，結果與原尺寸相同
QUICK_ACCEPT = 0.93                # 同一格跟上次同一張牌的分數超過這個值就直接採用
                                   # （不同牌之間最像的是 3m/5m，約 0.87）
EMPTY_DIFF = 4                     # 空格的縮圖平均差異小於這個值，視為沒變
FLOWERS = {'spring', 'summer', 'autumn', 'winter', 'plum', 'orchid', 'bamboo', 'chrysanthemum'}


def _imread(path, flags=cv2.IMREAD_GRAYSCALE):
    """cv2.imread 不支援含中文的路徑，改用 imdecode"""
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), flags)


class HandRecognizer:
    def __init__(self, samples_dir='samples'):
        self.templates = {}
        for name in os.listdir(samples_dir):
            if name.endswith('.png'):
                tmpl = _imread(os.path.join(samples_dir, name))
                self.templates[name[:-4]] = cv2.resize(tmpl, None, fx=MATCH_SCALE, fy=MATCH_SCALE,
                                                       interpolation=cv2.INTER_AREA)
        if not self.templates:
            raise ValueError(f"在 {samples_dir} 找不到任何樣板")
        self._last_labels = {}  # 格子 x 座標 → 上次認出的牌
        self._empty_slots = {}  # 格子 x 座標 → (縮圖, 比對結果)，上次沒認出牌的格子

    def _match_window(self, gray, x, y_top, y_bottom, labels):
        """在上緣 y_top～y_bottom 的範圍內比對指定樣板，回傳 (標籤, 分數, 左上角座標)"""
        x0 = max(0, x - SEARCH_X)
        window = gray[y_top:y_bottom + TILE_H, x0:x + TILE_W + SEARCH_X]
        window = cv2.resize(window, None, fx=MATCH_SCALE, fy=MATCH_SCALE, interpolation=cv2.INTER_AREA)
        best = (None, -1.0, (x, TILE_Y))
        for label in labels:
            res = cv2.matchTemplate(window, self.templates[label], cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(res)
            if score > best[1]:
                best = (label, score, (x0 + round(loc[0] / MATCH_SCALE), y_top + round(loc[1] / MATCH_SCALE)))
        return best

    def _match_labels(self, gray, x, labels, accept):
        """先在原本高度比對；分數不到 accept 再往上找（被選取的牌會浮起來）"""
        best = self._match_window(gray, x, TILE_Y - SEARCH_DOWN, TILE_Y + SEARCH_DOWN, labels)
        if best[1] < accept:
            raised = self._match_window(gray, x, TILE_Y - SEARCH_UP, TILE_Y - SEARCH_DOWN, labels)
            if raised[1] > best[1]:
                best = raised
        return best

    def _match_slot(self, gray, x):
        # 手牌大多沒變：先只跟這格上次的牌比，夠像就不用比全部樣板
        prev = self._last_labels.get(x)
        if prev:
            best = self._match_labels(gray, x, [prev], QUICK_ACCEPT)
            if best[1] >= QUICK_ACCEPT:
                return best
        # 上次是空格（吃碰區、沒有牌）且畫面幾乎沒變：沿用上次結果
        thumb = cv2.resize(gray[TILE_Y - SEARCH_UP:TILE_Y + TILE_H, x:x + TILE_W], (16, 32),
                           interpolation=cv2.INTER_AREA).astype(np.int16)
        empty = self._empty_slots.get(x)
        if empty is not None and np.abs(thumb - empty[0]).mean() < EMPTY_DIFF:
            return empty[1]

        best = self._match_labels(gray, x, self.templates, THRESHOLD)
        if best[1] >= THRESHOLD:
            self._last_labels[x] = best[0]
            self._empty_slots.pop(x, None)
        else:
            self._last_labels.pop(x, None)
            self._empty_slots[x] = (thumb, best)
        return best

    def recognize(self, frame):
        """辨識手牌

        Returns:
            dict:
                'hand': 手牌（由左到右，不含摸進的牌、花牌、認不出來的牌）
                'drawn': 摸進的牌，沒有則為 None
                'flowers': 手牌格中出現的花牌
                'unknown': 夾在手牌中間、認不出來的格子數（被遮住、變暗等）
                'detections': [{'x','y','w','h','label','confidence'}]，座標對應輸入畫面
        """
        scale = 1.0
        if frame.shape[1] != REF_W or frame.shape[0] != REF_H:
            scale = frame.shape[1] / REF_W
            frame = cv2.resize(frame, (REF_W, REF_H))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 由右往左比對 16 個手牌格
        slots = []
        for k in range(NUM_SLOTS):
            x = round(LAST_SLOT_X - k * SLOT_PITCH)
            slots.append(self._match_slot(gray, x))
        slots.reverse()  # 改成由左到右

        # 最左邊一段認不出來的格子是吃碰區或空位；之後的低分格才算未知牌
        first = next((i for i, s in enumerate(slots) if s[1] >= THRESHOLD), len(slots))
        hand_slots = slots[first:]

        drawn_slot = self._match_slot(gray, DRAWN_X)
        if drawn_slot[1] < THRESHOLD:
            drawn_slot = None

        hand, flowers, detections, unknown = [], [], [], 0
        for slot in hand_slots + ([drawn_slot] if drawn_slot else []):
            label, score, (x, y) = slot
            if score < THRESHOLD:
                unknown += 1
                label = '?'
            elif label in FLOWERS:
                flowers.append(label)
            elif slot is not drawn_slot:
                hand.append(label)
            detections.append({
                'x': int(x * scale), 'y': int(y * scale),
                'w': int(TILE_W * scale), 'h': int(TILE_H * scale),
                'label': label, 'confidence': float(score),
            })

        drawn = None
        if drawn_slot and drawn_slot[0] not in FLOWERS:
            drawn = drawn_slot[0]

        return {'hand': hand, 'drawn': drawn, 'flowers': flowers,
                'unknown': unknown, 'detections': detections}
