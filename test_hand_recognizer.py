#!/usr/bin/env python3
"""測試手牌辨識：用 samples/ 的樣板合成遊戲畫面，再辨識回來"""
import os

import cv2
import numpy as np

import hand_recognizer as hr
from main_preview import analyze_frame


def load_color_template(label):
    path = os.path.join('samples', f'{label}.png')
    return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)


def make_frame(hand, drawn=None, raised_index=None):
    """把手牌貼到固定格子上（靠右對齊），回傳合成的畫面"""
    frame = np.full((hr.REF_H, hr.REF_W, 3), 60, dtype=np.uint8)
    first_slot = hr.NUM_SLOTS - len(hand)
    for i, label in enumerate(hand):
        k = hr.NUM_SLOTS - 1 - (first_slot + i)
        x = round(hr.LAST_SLOT_X - k * hr.SLOT_PITCH)
        y = hr.TILE_Y - (50 if i == raised_index else 0)
        frame[y:y + hr.TILE_H, x:x + hr.TILE_W] = load_color_template(label)
    if drawn:
        frame[hr.TILE_Y:hr.TILE_Y + hr.TILE_H, hr.DRAWN_X:hr.DRAWN_X + hr.TILE_W] = load_color_template(drawn)
    return frame


HAND_16 = ["1m", "1m", "2m", "3m", "4m", "5m", "6m", "7m",
           "1p", "1p", "2p", "2p", "3p", "3p", "4p", "5p"]


def check(cond, message):
    if not cond:
        raise AssertionError(message)
    print(f"✓ {message}")


def test_full_hand():
    r = hr.HandRecognizer()
    res = r.recognize(make_frame(HAND_16))
    check(res['hand'] == HAND_16, "16 張手牌全部辨識正確")
    check(res['drawn'] is None and res['unknown'] == 0, "沒有摸牌、沒有未知牌")


def test_drawn_and_raised():
    r = hr.HandRecognizer()
    res = r.recognize(make_frame(HAND_16, drawn="8m", raised_index=5))
    check(res['hand'] == HAND_16, "被選取（浮起）的牌也能辨識")
    check(res['drawn'] == "8m", "摸進的牌辨識為 8m")


def test_after_melds():
    r = hr.HandRecognizer()
    hand = ["east", "east", "white", "fa", "middle", "9s", "8s", "7s", "6p", "6p"]
    res = r.recognize(make_frame(hand, drawn="north"))
    check(res['hand'] == hand, "吃碰後只剩 10 張也能辨識（左邊空格不算）")
    check(res['drawn'] == "north", "摸進的牌辨識為 north")


def test_covered_tile_is_unknown():
    r = hr.HandRecognizer()
    frame = make_frame(HAND_16)
    x = round(hr.LAST_SLOT_X - 3 * hr.SLOT_PITCH)
    frame[hr.TILE_Y:hr.TILE_Y + hr.TILE_H, x:x + hr.TILE_W] = (0, 0, 200)  # 被擋住
    res = r.recognize(frame)
    check(res['unknown'] == 1 and len(res['hand']) == 15, "被擋住的牌標為未知，不硬猜")


def test_flower_not_in_hand():
    r = hr.HandRecognizer()
    res = r.recognize(make_frame(HAND_16, drawn="spring"))
    check(res['drawn'] is None and res['flowers'] == ["spring"], "摸到花牌不算進手牌")


def test_scaled_frame():
    r = hr.HandRecognizer()
    frame = cv2.resize(make_frame(HAND_16, drawn="9p"), (1920, 1037))
    res = r.recognize(frame)
    check(res['hand'] == HAND_16 and res['drawn'] == "9p", "視窗大小不同時縮放後仍能辨識")


def test_cache_does_not_return_stale_tiles():
    r = hr.HandRecognizer()
    r.recognize(make_frame(HAND_16))
    r.recognize(make_frame(HAND_16))  # 第二次會走快取
    changed = HAND_16[:3] + ["5m"] + HAND_16[4:]  # 3m → 5m（最像的一組牌）
    res = r.recognize(make_frame(changed, drawn="white"))
    check(res['hand'] == changed and res['drawn'] == "white", "同一格換成很像的牌時，快取不會沿用舊結果")
    res = r.recognize(make_frame(["east"] * 3 + ["9p"]))
    check(res['hand'] == ["east"] * 3 + ["9p"], "手牌變少（吃碰）後，空出來的格子不會殘留舊的牌")
    res = r.recognize(make_frame(HAND_16))
    check(res['hand'] == HAND_16, "空格重新出現牌時能再認出來")


def test_suggested_tile_is_marked():
    r = hr.HandRecognizer()
    dets, _ = analyze_frame(make_frame(HAND_16, drawn="8m"), r, {})
    marked = [d['label'] for d in dets if d.get('suggested')]
    check(len(marked) == 1, f"建議打的牌在畫面上有標記（{marked}）")


def test_analyze_frame_caches_suggestion():
    r = hr.HandRecognizer()
    cache = {}
    frame = make_frame(HAND_16, drawn="8m")
    _, lines = analyze_frame(frame, r, cache)
    check(any(l.startswith("Discard:") and "Shanten after: 0" in l for l in lines), "17 張時給出打牌建議（打完聽牌）")
    key = cache['key']
    _, lines2 = analyze_frame(frame, r, cache)
    check(cache['key'] is key and lines2 == lines, "手牌沒變時沿用上次結果")
    _, lines3 = analyze_frame(make_frame(HAND_16), r, cache)
    check(any(l == "Shanten: 0" for l in lines3), "16 張時顯示進聽數")


def main():
    tests = [test_full_hand, test_drawn_and_raised, test_after_melds, test_covered_tile_is_unknown,
             test_flower_not_in_hand, test_scaled_frame, test_cache_does_not_return_stale_tiles,
             test_suggested_tile_is_marked, test_analyze_frame_caches_suggestion]
    failed = 0
    for t in tests:
        print(f"\n=== {t.__name__} ===")
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"❌ 測試失敗: {e}")
    print(f"\n測試完成: 通過 {len(tests) - failed} 個，失敗 {failed} 個")
    return failed


if __name__ == '__main__':
    raise SystemExit(main())
