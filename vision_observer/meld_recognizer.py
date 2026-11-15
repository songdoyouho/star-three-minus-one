"""辨識明星3缺1（6.9.x 版）畫面左下角自己吃碰槓出去的牌

這些牌從最左邊開始一張接一張排（手牌往右移），每一格的位置和傾斜角度固定：
牌面是上緣往右偏的四邊形，越左邊偏越多。把每一格拉正成長方形後，
取牌面內非白色的部分當圖案，先比 samples_meld/ 裡從實際吃碰區截下來的樣板，
不夠像再跟手牌樣板比對（碰出去的 1 筒外圈較淡，跟手牌樣板比不像）。
每組吃碰槓都佔 3 格；槓是在中間那格上面再疊一張（暗槓時下面 3 張是蓋著的牌背）。
位置參數用已知答案的截圖找出來（39 張全對，最低分 0.5）。座標以 2566x1386 的視窗截圖為準。
"""
import os

import cv2
import numpy as np

from vision_observer.hand_recognizer import REF_W, REF_H, _imread
from vision_observer.table_recognizer import white_mask, HandTemplateMatcher, PATCH, _features

FACE_TOP, FACE_BOTTOM = 1048, 1146   # 牌面上緣、下緣
FIRST_X = 94                         # 第一格牌面下緣的左端
PITCH = 137.25                       # 每格間距
BOTTOM_W, TOP_W = 131, 134           # 牌面下緣、上緣寬度
TOP_OFFSET, TOP_OFFSET_STEP = 60, 8  # 上緣比下緣往右偏多少（第 i 格是 60 - 8i）
FACE_W, FACE_H = 130, 98             # 拉正後的大小
MARGIN_TOP, MARGIN_BOTTOM, MARGIN_SIDE = 3, 12, 6   # 萬子的數字很靠近上緣，上邊界不能太大
ACCEPT = 0.45                         # 這裡一定是牌（在第一張手牌左邊），門檻可以低一點
MAX_SLOTS = 15
STACK_DX, STACK_DY = -3, 58          # 槓的第 4 張疊在中間那格上面：往左、往上偏移
STACK_ACCEPT = 0.5                   # 疊在上面的牌要夠像才算槓（白板線條細，分數較低，約 0.58）
CONCEALED_ACCEPT = 0.2               # 暗槓上面那張一定是牌，只要排得出最像的就好
BACK_RATIO = 0.5                    # 藍綠色超過這個比例就是蓋著的牌背
MELD_ACCEPT = 0.8                    # 跟 samples_meld/ 的樣板這麼像就直接採用
HAND_GAP = 6                         # 手牌左緣往左這麼多以右不看（最後一格右邊會帶到手牌的邊）


def slot_quad(i):
    """第 i 格牌面的四個角（左上、右上、右下、左下）"""
    left = FIRST_X + PITCH * i
    off = TOP_OFFSET - TOP_OFFSET_STEP * i
    return np.float32([[left + off, FACE_TOP], [left + off + TOP_W, FACE_TOP],
                       [left + BOTTOM_W, FACE_BOTTOM], [left, FACE_BOTTOM]])


def _is_back(face):
    hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)
    teal = (hsv[..., 0] > 85) & (hsv[..., 0] < 110) & (hsv[..., 1] > 120)
    return teal.mean() > BACK_RATIO


class MeldRecognizer:
    def __init__(self, samples_dir='samples', meld_dir='samples_meld'):
        self.matcher = HandTemplateMatcher(samples_dir)
        names = sorted(n for n in os.listdir(meld_dir) if n.endswith('.png'))
        self.meld_labels = [n.rsplit('_', 1)[0] for n in names]
        self.meld_feats = _features([_imread(os.path.join(meld_dir, n), cv2.IMREAD_COLOR) for n in names])
        self._dst = np.float32([[0, 0], [FACE_W, 0], [FACE_W, FACE_H], [0, FACE_H]])

    def _patch(self, face):
        """拉正後的牌面 → 圖案縮放後的小圖，沒有圖案時回傳 None"""
        ink = 1 - white_mask(face)
        ink[:MARGIN_TOP] = 0
        ink[FACE_H - MARGIN_BOTTOM:] = 0
        ink[:, :MARGIN_SIDE] = 0
        ink[:, FACE_W - MARGIN_SIDE:] = 0
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        ys, xs = np.nonzero(ink)
        if len(xs) < 15:
            return None
        return cv2.resize(face[ys.min():ys.max() + 1, xs.min():xs.max() + 1], (PATCH, PATCH),
                          interpolation=cv2.INTER_AREA)

    def _classify(self, face, accept=ACCEPT):
        patch = self._patch(face)
        if patch is None:
            return None, 0.0
        scores = self.meld_feats @ _features([patch])[0]
        k = int(np.argmax(scores))
        if scores[k] >= MELD_ACCEPT:
            return self.meld_labels[k], float(scores[k])
        label, score = self.matcher.match(patch)
        return (label if score >= accept else None), score

    def recognize(self, frame, hand_x):
        """辨識自己吃碰槓的牌

        Args:
            hand_x: 第一張手牌的左緣（輸入畫面座標），吃碰的牌都在它左邊
        Returns:
            dict: 'tiles' 由左到右的牌（認不出來是 '?'）、'melds' 分組後的牌、
                  'detections' 標示用 [{'x','y','w','h','label','confidence'}]、
                  'area' 吃碰區範圍 (x, y, w, h)，座標對應輸入畫面
        """
        scale = 1.0
        if frame.shape[1] != REF_W or frame.shape[0] != REF_H:
            scale = frame.shape[1] / REF_W
            frame = cv2.resize(frame, (REF_W, REF_H))
        hand_x = hand_x / scale
        frame = frame[:, :int(hand_x) - HAND_GAP]  # 右邊是手牌，拉正時超出的部分補白色

        melds, detections = [], []
        for g in range(MAX_SLOTS // 3):
            if slot_quad(3 * g + 2)[2][0] > hand_x:
                break
            labels, backs = [], []
            for i in range(3 * g, 3 * g + 3):
                face = self._warp(frame, slot_quad(i))
                backs.append(_is_back(face))
                label, score = (None, 0.0) if backs[-1] else self._classify(face)
                labels.append(label)
                detections.append(self._detection(slot_quad(i), label, score, scale))
            # 槓：中間那格上面疊了一張。暗槓（兩側是牌背）上面一定是牌，取最像的那張就好
            stack = slot_quad(3 * g + 1) + np.float32([STACK_DX, -STACK_DY])
            concealed = backs[0] and backs[2]
            top, score = self._classify(self._warp(frame, stack), CONCEALED_ACCEPT if concealed else STACK_ACCEPT)
            if top and all(l in (None, top) for l in labels):
                melds.append([top] * 4)
                detections.append(self._detection(stack, top, score, scale))
            else:
                melds.append([l or '?' for l in labels])
        area = (0, int((FACE_TOP - STACK_DY - 20) * scale), int(hand_x * scale), int((180 + STACK_DY) * scale))
        tiles = [t for m in melds for t in m]
        return {'tiles': tiles, 'melds': melds, 'detections': detections, 'area': area}

    def _warp(self, frame, quad):
        return cv2.warpPerspective(frame, cv2.getPerspectiveTransform(quad, self._dst), (FACE_W, FACE_H),
                                   borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

    @staticmethod
    def _detection(quad, label, score, scale):
        x0, x1 = quad[:, 0].min(), quad[:, 0].max()
        y0, y1 = quad[:, 1].min(), quad[:, 1].max()
        return {'x': int(x0 * scale), 'y': int(y0 * scale), 'w': int((x1 - x0) * scale),
                'h': int((y1 - y0) * scale), 'label': label or '?', 'confidence': score}
