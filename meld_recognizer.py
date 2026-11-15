"""辨識明星3缺1（6.9.x 版）畫面左下角自己吃碰槓出去的牌

這些牌從最左邊開始一張接一張排（手牌往右移），每一格的位置和傾斜角度固定：
牌面是上緣往右偏的四邊形，越左邊偏越多。把每一格拉正成長方形後，
取牌面內非白色的部分當圖案，跟手牌樣板比對。
位置參數用已知答案的截圖找出來（39 張全對，最低分 0.5）。座標以 2566x1386 的視窗截圖為準。
"""
import cv2
import numpy as np

from hand_recognizer import REF_W, REF_H
from table_recognizer import white_mask, HandTemplateMatcher, PATCH

FACE_TOP, FACE_BOTTOM = 1048, 1146   # 牌面上緣、下緣
FIRST_X = 94                         # 第一格牌面下緣的左端
PITCH = 137.25                       # 每格間距
BOTTOM_W, TOP_W = 131, 134           # 牌面下緣、上緣寬度
TOP_OFFSET, TOP_OFFSET_STEP = 60, 8  # 上緣比下緣往右偏多少（第 i 格是 60 - 8i）
FACE_W, FACE_H = 130, 98             # 拉正後的大小
MARGIN_TOP, MARGIN_BOTTOM, MARGIN_SIDE = 3, 12, 6   # 萬子的數字很靠近上緣，上邊界不能太大
ACCEPT = 0.45                         # 這裡一定是牌（在第一張手牌左邊），門檻可以低一點
MAX_SLOTS = 16


def slot_quad(i):
    """第 i 格牌面的四個角（左上、右上、右下、左下）"""
    left = FIRST_X + PITCH * i
    off = TOP_OFFSET - TOP_OFFSET_STEP * i
    return np.float32([[left + off, FACE_TOP], [left + off + TOP_W, FACE_TOP],
                       [left + BOTTOM_W, FACE_BOTTOM], [left, FACE_BOTTOM]])


def group_melds(tiles):
    """把一排吃碰槓的牌分成一組一組：4 張一樣是槓、3 張一樣是碰、其他 3 張是吃"""
    melds, i = [], 0
    while i < len(tiles):
        if len(tiles) - i >= 4 and len(set(tiles[i:i + 4])) == 1:
            melds.append(tiles[i:i + 4])
            i += 4
        else:
            melds.append(tiles[i:i + 3])
            i += 3
    return melds


class MeldRecognizer:
    def __init__(self, samples_dir='samples'):
        self.matcher = HandTemplateMatcher(samples_dir)
        self._dst = np.float32([[0, 0], [FACE_W, 0], [FACE_W, FACE_H], [0, FACE_H]])

    def _classify(self, face):
        ink = 1 - white_mask(face)
        ink[:MARGIN_TOP] = 0
        ink[FACE_H - MARGIN_BOTTOM:] = 0
        ink[:, :MARGIN_SIDE] = 0
        ink[:, FACE_W - MARGIN_SIDE:] = 0
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        ys, xs = np.nonzero(ink)
        if len(xs) < 15:
            return None, 0.0
        patch = cv2.resize(face[ys.min():ys.max() + 1, xs.min():xs.max() + 1], (PATCH, PATCH),
                           interpolation=cv2.INTER_AREA)
        label, score = self.matcher.match(patch)
        return (label if score >= ACCEPT else None), score

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

        tiles, detections = [], []
        for i in range(MAX_SLOTS):
            quad = slot_quad(i)
            if quad[2][0] > hand_x:
                break
            face = cv2.warpPerspective(frame, cv2.getPerspectiveTransform(quad, self._dst), (FACE_W, FACE_H))
            label, score = self._classify(face)
            tiles.append(label or '?')
            x0, x1 = quad[:, 0].min(), quad[:, 0].max()
            detections.append({'x': int(x0 * scale), 'y': int(FACE_TOP * scale), 'w': int((x1 - x0) * scale),
                               'h': int((FACE_BOTTOM - FACE_TOP) * scale), 'label': label or '?',
                               'confidence': score})
        area = (0, int((FACE_TOP - 20) * scale), int(hand_x * scale), int(180 * scale))
        return {'tiles': tiles, 'melds': group_melds(tiles), 'detections': detections, 'area': area}
