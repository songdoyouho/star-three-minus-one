"""用實際錄影截下來的畫面測試吃碰區與放大的牌（tests/fixtures/，檔名結尾是貼回畫面的 y_x 座標）"""
import os

import cv2
import numpy as np
import pytest

from vision_observer.hand_recognizer import REF_W, REF_H, _imread
from vision_observer.meld_recognizer import MeldRecognizer
from vision_observer.claim_recognizer import ClaimRecognizer

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_frame(name):
    """把截圖貼回完整大小的畫面（其他地方是黑色）"""
    y, x = (int(v) for v in name[:-4].rsplit('_', 2)[1:])
    crop = _imread(os.path.join(FIXTURES, name), cv2.IMREAD_COLOR)
    frame = np.zeros((REF_H, REF_W, 3), np.uint8)
    frame[y:y + crop.shape[0], x:x + crop.shape[1]] = crop
    return frame


@pytest.mark.parametrize('name, hand_x, melds', [
    # 第 3 格右邊緊接著手牌，手牌的邊緣不能被當成圖案
    ('meld_3s3s3s_hand522_960_0.png', 522, [['3s', '3s', '3s']]),
    ('meld_6m7m8m_hand524_960_0.png', 524, [['6m', '7m', '8m']]),
    # 碰出去的 1 筒外圈較淡，跟手牌樣板比不像
    ('meld_3m3m3m1p1p1p_hand933_960_0.png', 933, [['3m', '3m', '3m'], ['1p', '1p', '1p']]),
])
def test_meld_from_recording(name, hand_x, melds):
    assert MeldRecognizer().recognize(load_frame(name), hand_x)['melds'] == melds


@pytest.mark.parametrize('name, tile', [
    ('claim_1p_430_880.png', '1p'),    # 1 筒外圈貼到牌邊，牌面被切成上下兩塊
    ('claim_1p_410_1200.png', '1p'),   # 1 筒圖案很大，白色面積不到一半
    ('claim_fa_430_880.png', 'fa'),    # 發的筆畫超出牌面
])
def test_claim_tile_from_recording(name, tile):
    label, box = ClaimRecognizer()._enlarged_tile(load_frame(name))
    assert label == tile
    assert box is not None
