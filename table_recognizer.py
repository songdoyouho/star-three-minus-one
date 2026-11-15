"""辨識明星3缺1（6.9.x 版）桌面上看得到的牌：牌河（打出去的牌）和吃碰槓的牌

桌上的牌大小、角度都不固定（越遠越小、兩側會斜，別家吃碰的牌是轉過的），
所以不用固定格子，而是：
1. 找出白色牌面的區塊（牌與牌之間有深色縫隙，會自然分開）
2. 牌面上的圖案（白色以外的部分）取外框、縮放成固定大小，跟樣板比對
   - 先比 samples_river/ 裡從實際牌河截下來的樣板，很像（>= RIVER_ACCEPT）就採用
   - 否則比 samples/ 手牌樣板的圖案，分數 >= HAND_ACCEPT 才採用，不夠像就不算
3. 吃碰的牌會連成一塊，依牌的寬度切開；轉過的牌就把圖案轉回來再比
座標以 2566x1386 的視窗截圖為準。
"""
import os

import cv2
import numpy as np

from hand_recognizer import REF_W, REF_H, FLOWERS, _imread

PATCH = 40                 # 圖案縮放後的大小
TABLE_TOP = 440            # 掃描範圍（上緣以上是頭像、跑馬燈）
TABLE_BOTTOM = 1210        # 下緣（含自己吃碰的牌）
MIN_AREA = 500             # 太小的白色區塊不是牌
MIN_SIDE = 25
RIVER_ACCEPT = 0.8
HAND_ACCEPT = 0.45
MARKER_MIN_PX = 150        # 橘色超過這麼多像素才當成「最新打出」的標記（一索、九索本身也有少量橘色）
OTHER_ACCEPT = 0.6        # 牌河以外（轉過、連在一起）的牌比較容易誤認，門檻較高


def white_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return ((hsv[..., 1] < 50) & (hsv[..., 2] > 185)).astype(np.uint8)


def ink_patch(img, comp, hull=False):
    """img: 一張牌的彩色截圖；comp: 同範圍內白色牌面的 mask。回傳圖案外框縮放後的小圖

    hull: 用凸包當牌面範圍。大字（西、南…）頂到牌面邊緣時，圖案會跟牌外連在一起而被漏掉，
          這時改用凸包；但凸包會把牌身的陰影也框進來，所以只在一般方法認不出來時才用。
    """
    # 最新打出的牌上面有橘色錐形標記，蓋住的地方當成白色牌面，不算圖案
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    marker = ((hsv[..., 0] >= 4) & (hsv[..., 0] <= 25) & (hsv[..., 1] > 100) & (hsv[..., 2] > 120)).astype(np.uint8)
    if marker.sum() >= MARKER_MIN_PX:
        marker = cv2.dilate(marker, np.ones((5, 5), np.uint8))
        img = img.copy()
        img[marker > 0] = 245
        comp = comp | marker
    face = np.zeros_like(comp)
    if hull:
        cv2.fillConvexPoly(face, cv2.convexHull(cv2.findNonZero(comp)), 1)
    else:
        cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(face, cnts, -1, 1, -1)
    ink = cv2.morphologyEx(face & (1 - comp), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    ys, xs = np.nonzero(ink)
    if len(xs) < 15:
        return None
    patch = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return cv2.resize(patch, (PATCH, PATCH), interpolation=cv2.INTER_AREA)


def hand_ink_patch(img):
    """手牌樣板的圖案（樣板本身就是整張牌面，去掉邊框後非白色的部分就是圖案）"""
    ink = 1 - white_mask(img)
    ink[:10] = 0
    ink[-10:] = 0
    ink[:, :8] = 0
    ink[:, -8:] = 0
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    ys, xs = np.nonzero(ink)
    patch = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return cv2.resize(patch, (PATCH, PATCH), interpolation=cv2.INTER_AREA)


def _features(patches):
    x = np.stack(patches).reshape(len(patches), -1).astype(np.float32)
    x -= x.mean(axis=1, keepdims=True)
    return x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-6)


MAN_NUMERAL_ROWS = 15      # 萬子圖案上面這幾列（共 PATCH 列）是數字


class HandTemplateMatcher:
    """用手牌樣板的圖案比對大張的牌（放大顯示的牌、自己吃碰的牌）

    萬子的數字只佔圖案上面一小塊，整體比對容易被下面的「萬」字主導，
    所以認出是萬子後，再只比上面數字的部分。
    """
    def __init__(self, samples_dir='samples'):
        names = sorted(n for n in os.listdir(samples_dir) if n.endswith('.png'))
        self.labels = [n[:-4] for n in names]
        patches = [hand_ink_patch(_imread(os.path.join(samples_dir, n), cv2.IMREAD_COLOR)) for n in names]
        self.feats = _features(patches)
        self.man_labels = [l for l in self.labels if l.endswith('m')]
        self.man_feats = _features([p[:MAN_NUMERAL_ROWS] for p, l in zip(patches, self.labels) if l.endswith('m')])

    def match(self, patch):
        """回傳 (標籤, 分數)，分數是整體比對的分數"""
        scores = self.feats @ _features([patch])[0]
        k = int(np.argmax(scores))
        label = self.labels[k]
        if label in self.man_labels:
            numeral = self.man_feats @ _features([patch[:MAN_NUMERAL_ROWS]])[0]
            label = self.man_labels[int(np.argmax(numeral))]
        return label, float(scores[k])


class TableRecognizer:
    def __init__(self, samples_dir='samples', river_dir='samples_river'):
        names = sorted(n for n in os.listdir(samples_dir) if n.endswith('.png'))
        self.hand_labels = [n[:-4] for n in names]
        self.hand_feats = _features([hand_ink_patch(_imread(os.path.join(samples_dir, n), cv2.IMREAD_COLOR))
                                     for n in names])
        names = sorted(n for n in os.listdir(river_dir) if n.endswith('.png'))
        self.river_labels = [n.rsplit('_', 1)[0] for n in names]
        self.river_feats = _features([_imread(os.path.join(river_dir, n), cv2.IMREAD_COLOR) for n in names])
        self._cache = {}  # 牌面截圖 → 結果；畫面沒變的牌不用重算

    def classify(self, patch, hand_accept=HAND_ACCEPT):
        """回傳 (標籤, 分數)，認不出來時標籤為 None"""
        f = _features([patch])[0]
        river = self.river_feats @ f
        i = int(np.argmax(river))
        if river[i] >= RIVER_ACCEPT:
            return self.river_labels[i], float(river[i])
        hand = self.hand_feats @ f
        i = int(np.argmax(hand))
        if hand[i] >= hand_accept:
            return self.hand_labels[i], float(hand[i])
        return None, float(max(river.max(), hand[i]))

    def _classify_piece(self, img, comp, rotations, hand_accept=HAND_ACCEPT, hull=False):
        patch = ink_patch(img, comp, hull)
        if patch is None:
            return None, 0.0
        best = (None, 0.0)
        for k in rotations:
            label, score = self.classify(np.rot90(patch, k) if k else patch, hand_accept)
            if label and score > best[1]:
                best = (label, score)
        return best

    def _classify_blob(self, img, comp):
        """一個白色區塊可能是一張牌，或是連在一起的幾張吃碰牌。回傳 [(標籤, 分數, (x, y, w, h))]"""
        h, w = comp.shape
        if 40 <= w <= 100 and 35 <= h <= 85 and 0.9 <= w / h <= 1.6:
            # 牌河的牌：正向
            label, score = self._classify_piece(img, comp, (0,))
            if not label:
                label, score = self._classify_piece(img, comp, (0,), hull=True)
            return [(label, score, (0, 0, w, h))] if label else []
        # 其他：可能轉過、可能連在一起，沿長邊切成 1～4 張，取平均分數最高的切法
        best, best_score = [], 0.0
        for n in range(1, 5):
            long_side = max(w, h) / n
            if long_side < MIN_SIDE or min(w, h) < MIN_SIDE:
                break
            pieces = []
            for k in range(n):
                if w >= h:
                    x0, x1, y0, y1 = round(k * w / n), round((k + 1) * w / n), 0, h
                else:
                    x0, x1, y0, y1 = 0, w, round(k * h / n), round((k + 1) * h / n)
                label, score = self._classify_piece(img[y0:y1, x0:x1], comp[y0:y1, x0:x1],
                                                           (0, 1, 2, 3), OTHER_ACCEPT)
                if not label:
                    break
                pieces.append((label, score, (x0, y0, x1 - x0, y1 - y0)))
            if len(pieces) == n:
                mean = sum(p[1] for p in pieces) / n
                if mean > best_score:
                    best, best_score = pieces, mean
        return best

    def recognize(self, frame, exclude_boxes=()):
        """辨識桌上看得到的牌

        Args:
            frame: 遊戲畫面
            exclude_boxes: 不要掃描的範圍 [(x, y, w, h)]，座標對應輸入畫面（例如自己的手牌）
        Returns:
            dict:
                'tiles': 看得到的牌（不含花牌）
                'flowers': 看得到的花牌
                'detections': [{'x','y','w','h','label','confidence'}]，座標對應輸入畫面
        """
        scale = 1.0
        if frame.shape[1] != REF_W or frame.shape[0] != REF_H:
            scale = frame.shape[1] / REF_W
            frame = cv2.resize(frame, (REF_W, REF_H))
        frame = frame[TABLE_TOP:TABLE_BOTTOM]
        mask = white_mask(frame)
        for x, y, w, h in exclude_boxes:
            x, y, w, h = (round(v / scale) for v in (x, y, w, h))
            y -= TABLE_TOP
            mask[max(0, y - 10):max(0, y + h + 10), max(0, x - 10):x + w + 10] = 0

        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
        tiles, flowers, detections = [], [], []
        cache = {}
        for i in np.nonzero(stats[1:, cv2.CC_STAT_AREA] >= MIN_AREA)[0] + 1:
            x, y, w, h, _ = stats[i]
            img = frame[y:y + h, x:x + w]
            # 同一塊畫面（位置、大小、像素都一樣）結果一定一樣，不用重算；像素隔一個取一個就夠分辨
            key = (int(x), int(y), int(w), int(h), img[::2, ::2].tobytes())
            result = self._cache.get(key)
            if result is None:
                comp = (labels[y:y + h, x:x + w] == i).astype(np.uint8)
                result = self._classify_blob(img, comp)
            cache[key] = result
            for label, score, (px, py, pw, ph) in result:
                (flowers if label in FLOWERS else tiles).append(label)
                detections.append({
                    'x': int((x + px) * scale), 'y': int((y + TABLE_TOP + py) * scale),
                    'w': int(pw * scale), 'h': int(ph * scale),
                    'label': label, 'confidence': score,
                })
        self._cache = cache
        return {'tiles': tiles, 'flowers': flowers, 'detections': detections}
