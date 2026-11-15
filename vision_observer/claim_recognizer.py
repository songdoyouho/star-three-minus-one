"""辨識明星3缺1（6.9.x 版）的吃碰槓胡按鈕，以及被放大顯示的那張打出的牌

可以吃碰槓胡時，畫面中下方會出現一排按鈕（吃、碰、槓、聽、胡、取消），
能按的按鈕底色是白的，不能按的是半透明灰色；剛打出的那張牌會放大顯示在深色圓圈裡。
座標以 2566x1386 的視窗截圖為準。
"""
import os

import cv2
import numpy as np

from vision_observer.hand_recognizer import REF_W, REF_H, _imread
from vision_observer.table_recognizer import white_mask, ink_patch, HandTemplateMatcher

BUTTONS = {'chi': (705, 863), 'pon': (935, 863), 'kan': (1165, 863), 'ting': (1392, 863), 'hu': (1618, 863)}
CANCEL = (1880, 875)
CANCEL_ACCEPT = 0.8
RING = (60, 72)            # 取按鈕外圈這一圈的像素判斷亮不亮（避開中間的字）
LIT_RATIO = 0.5            # 外圈有一半以上是白色就算亮
TILE_AREA = (300, 1000)    # 放大的牌出現的高度範圍
TILE_ACCEPT = 0.6

_yy, _xx = np.mgrid[-RING[1]:RING[1] + 1, -RING[1]:RING[1] + 1]
_RING_MASK = (np.hypot(_yy, _xx) >= RING[0]) & (np.hypot(_yy, _xx) <= RING[1])


class ClaimRecognizer:
    def __init__(self, samples_dir='samples', ui_dir='samples_ui'):
        self.cancel = _imread(os.path.join(ui_dir, 'cancel.png'), cv2.IMREAD_COLOR)
        self.matcher = HandTemplateMatcher(samples_dir)

    def recognize(self, frame):
        """沒有按鈕列時回傳 None；有的話回傳
        {'buttons': 亮著的按鈕 ['chi', 'pon', ...], 'tile': 放大的牌（認不出來是 None）,
         'tile_box': 放大的牌的位置 (x, y, w, h), 'button_boxes': {按鈕: (x, y, w, h)}}，座標對應輸入畫面
        """
        scale = 1.0
        if frame.shape[1] != REF_W or frame.shape[0] != REF_H:
            scale = frame.shape[1] / REF_W
            frame = cv2.resize(frame, (REF_W, REF_H))

        cx, cy = CANCEL
        h, w = self.cancel.shape[:2]
        window = frame[cy - h // 2 - 20:cy + h // 2 + 20, cx - w // 2 - 20:cx + w // 2 + 20]
        if cv2.matchTemplate(window, self.cancel, cv2.TM_CCOEFF_NORMED).max() < CANCEL_ACCEPT:
            return None

        hsv = cv2.cvtColor(frame[cy - 100:cy + 100], cv2.COLOR_BGR2HSV)
        lit = []
        r = RING[1]
        for name, (x, y) in BUTTONS.items():
            ring = hsv[y - (cy - 100) - r:y - (cy - 100) + r + 1, x - r:x + r + 1][_RING_MASK]
            if ((ring[:, 1] < 50) & (ring[:, 2] > 200)).mean() >= LIT_RATIO:
                lit.append(name)

        boxes = {name: (int((x - 80) * scale), int((y - 80) * scale), int(160 * scale), int(160 * scale))
                 for name, (x, y) in list(BUTTONS.items()) + [('cancel', CANCEL)]}
        tile, box = self._enlarged_tile(frame)
        if box:
            box = tuple(int(v * scale) for v in box)
        return {'buttons': lit, 'tile': tile, 'tile_box': box, 'button_boxes': boxes}

    def _enlarged_tile(self, frame):
        top, bottom = TILE_AREA
        roi = frame[top:bottom]
        n, labels, stats, _ = cv2.connectedComponentsWithStats(white_mask(roi))
        best = (None, TILE_ACCEPT, None)
        for i in range(1, n):
            x, y, w, h, area = stats[i]
            if not (80 <= w <= 150 and 110 <= h <= 210 and 1.2 <= h / w <= 1.7 and area > 0.5 * w * h):
                continue
            patch = ink_patch(roi[y:y + h, x:x + w], (labels[y:y + h, x:x + w] == i).astype(np.uint8))
            if patch is None:
                continue
            label, score = self.matcher.match(patch)
            if score > best[1]:
                best = (label, score, (int(x), int(y + top), int(w), int(h)))
        return best[0], best[2]
