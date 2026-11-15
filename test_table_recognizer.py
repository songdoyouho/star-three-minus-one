#!/usr/bin/env python3
"""測試桌面（牌河）辨識：用 samples_river/ 的圖案做出牌河的牌，貼到合成畫面上再辨識回來

實際截圖的辨識率另外用錄下來的截圖驗證過，這裡測的是整個流程（找牌、排除手牌、快取、扣張數）。
"""
import os
from collections import Counter

import cv2
import numpy as np

import table_recognizer as tr
from hand_recognizer import HandRecognizer
from main_preview import analyze_frame
from test_hand_recognizer import make_frame, check

RIVER_W, RIVER_H = 75, 58  # 牌河的牌：比手牌小、被壓扁（斜看桌面）


def river_tile(label):
    """白色牌面中間放上這張牌的圖案"""
    path = os.path.join('samples_river', f'{label}_0.png')
    patch = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    tile = np.full((RIVER_H, RIVER_W, 3), 245, dtype=np.uint8)
    tile[9:49, 10:65] = cv2.resize(patch, (55, 40), interpolation=cv2.INTER_AREA)
    return tile


def put_river(frame, tiles, x=900, y=700):
    """在桌面中間排一排牌河，牌與牌之間留縫"""
    for i, label in enumerate(tiles):
        tile = river_tile(label)
        x0 = x + i * (RIVER_W + 6)
        frame[y:y + RIVER_H, x0:x0 + RIVER_W] = tile
    return frame


HAND_16 = ["1m", "2m", "3m", "4p", "5p", "6p", "7s", "8s", "9s",
           "2p", "3p", "4p", "5s", "5s", "6m", "7m"]
RIVER = ["east", "8m", "9p", "fa", "8m", "1s", "south", "north"]


def test_river_tiles():
    t = tr.TableRecognizer()
    res = t.recognize(put_river(make_frame([]), RIVER))
    check(Counter(res['tiles']) == Counter(RIVER), f"牌河的牌全部辨識正確（{res['tiles']}）")


def test_hand_not_counted():
    h, t = HandRecognizer(), tr.TableRecognizer()
    frame = put_river(make_frame(HAND_16, drawn="east"), RIVER)
    boxes = [(d['x'], d['y'], d['w'], d['h']) for d in h.recognize(frame)['detections']]
    res = t.recognize(frame, boxes)
    check(Counter(res['tiles']) == Counter(RIVER), "排除手牌範圍後，手牌不會被算成桌上的牌")


def test_cache_follows_changes():
    t = tr.TableRecognizer()
    t.recognize(put_river(make_frame([]), RIVER))
    res = t.recognize(put_river(make_frame([]), RIVER[:3] + ["7m"]))
    check(Counter(res['tiles']) == Counter(RIVER[:3] + ["7m"]), "牌河改變時不會沿用舊結果")


def test_visible_tiles_reduce_waits():
    h, t = HandRecognizer(), tr.TableRecognizer()
    # 打掉 east 聽 5m/8m，牌河有兩張 8m → 剩 4 + 2 = 6 張
    frame = put_river(make_frame(HAND_16, drawn="east"), RIVER)
    _, lines = analyze_frame(frame, h, {}, t)
    check(any("Waits: 5m 8m (6 left)" in l for l in lines), f"等待張數扣掉牌河的牌（{lines[0]}）")
    check(any(l.startswith("Defense: safest east (1 seen)") for l in lines), f"顯示防守提示（{lines[1]}）")


def main():
    tests = [test_river_tiles, test_hand_not_counted, test_cache_follows_changes, test_visible_tiles_reduce_waits]
    failed = 0
    for test in tests:
        print(f"\n=== {test.__name__} ===")
        try:
            test()
        except AssertionError as e:
            failed += 1
            print(f"❌ 測試失敗: {e}")
    print(f"\n測試完成: 通過 {len(tests) - failed} 個，失敗 {failed} 個")
    return failed


if __name__ == '__main__':
    raise SystemExit(main())
