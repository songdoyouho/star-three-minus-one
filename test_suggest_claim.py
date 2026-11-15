#!/usr/bin/env python3
"""測試吃碰槓胡的建議"""
from calculate_shanten import suggest_claim, suggest_self_kan, is_winning
from hand_recognizer import HandRecognizer
from main_preview import analyze_frame
from test_hand_recognizer import make_frame

MELDS_9 = ["1m", "2m", "3m", "4p", "5p", "6p", "7s", "8s", "9s"]


def check(cond, message):
    if not cond:
        raise AssertionError(message)
    print(f"✓ {message}")


def test_win():
    hand = MELDS_9 + ["2p", "3p", "4p", "east", "east", "5s", "6s"]  # 聽 4s/7s
    r = suggest_claim(hand, "7s")
    check(r['action'] == 'win', f"打出的牌能胡時建議胡（{r['reason']}）")
    check(is_winning(hand + ["4s"]) and not is_winning(hand + ["east"]), "自摸判斷正確")


def test_pon_when_it_helps():
    hand = MELDS_9 + ["2p", "3p", "4p", "east", "east", "5s", "9m"]  # 一向聽
    r = suggest_claim(hand, "east")
    check(r['action'] == 'pon' and r['best']['shanten'] == 0, f"碰了能聽牌就建議碰（{r['reason']}）")
    check(r['best']['discard'] in ("5s", "9m"), f"碰完打孤張（{r['best']['discard']}）")


def test_pass_when_pon_does_not_help():
    hand = MELDS_9 + ["2p", "3p", "4p", "east", "east", "5s", "6s"]  # 已聽牌，東是將
    r = suggest_claim(hand, "east")
    check(r['action'] == 'pass', f"碰了進聽數沒變好就不碰（{r['reason']}）")


def test_chi_choice():
    hand = MELDS_9 + ["east", "east", "5s", "6s", "8m", "9m", "north"]  # 一向聽
    r = suggest_claim(hand, "4s", can_chi=True)
    check(r['action'] == 'chi' and r['best']['meld'] == ["4s", "5s", "6s"] and r['best']['discard'] == "north",
          f"上家打 4s 吃 456s、打北（{r['reason']}）")
    r = suggest_claim(hand, "4s", can_chi=False)
    check(r['action'] == 'pass', "不是上家打的不能吃")
    r = suggest_claim(hand, "7s", can_chi=True)
    check(r['action'] == 'chi' and r['best']['meld'] == ["5s", "6s", "7s"],
          f"7s 有 567s、678s 兩種吃法，選不拆面子的 567s（{r['reason']}）")


def test_kan():
    hand = MELDS_9 + ["north", "north", "north", "2p", "3p", "5m", "9m"]
    r = suggest_claim(hand, "north")
    check(r['action'] == 'kan', f"槓了進聽數不變差就槓，多補一張（{r['reason']}）")
    r = suggest_claim(hand, "north", allowed=['pon'])
    check(r['action'] != 'kan', f"遊戲只亮碰（不能槓）時不建議槓（{r['reason']}）")


def test_concealed_kan():
    hand = MELDS_9 + ["north"] * 4 + ["2p", "3p", "5m", "9m"]
    r = suggest_self_kan(hand)
    check(r['action'] == 'kan' and r['best']['tile'] == 'north' and r['best']['type'] == 'concealed',
          f"手上 4 張北，槓了進聽數不變就暗槓（{r['reason']}）")
    hand = ["1m"] * 4 + ["2m", "2m", "3m", "3m", "5p", "6p", "7p", "east", "east", "9s"]
    r = suggest_self_kan(hand)
    check(r['action'] == 'none', f"4 張 1m 拆了會壞掉順子就不槓（{r['reason']}）")


def test_added_kan():
    hand = MELDS_9 + ["2p", "3p", "east", "east", "5m"]
    r = suggest_self_kan(hand, pons=["5m"])
    check(r['action'] == 'kan' and r['best']['type'] == 'added', f"摸到碰過的 5m 就加槓（{r['reason']}）")
    r = suggest_self_kan(hand, pons=["9p"])
    check(r['action'] == 'none' and not r['options'], "沒有碰過的牌不能加槓")


class FakeClaim:
    """假的按鈕辨識：固定回傳出現按鈕、放大的牌是 tile"""
    def __init__(self, tile, buttons):
        self.result = {'buttons': buttons, 'tile': tile, 'tile_box': None,
                       'button_boxes': {b: (i * 200, 800, 160, 160) for i, b in
                                        enumerate(['chi', 'pon', 'kan', 'ting', 'hu', 'cancel'])}}

    def recognize(self, frame):
        return self.result


def test_analyze_frame_claim():
    hand = MELDS_9 + ["east", "east", "5s", "6s", "8m", "9m", "north"]
    frame = make_frame(hand)
    dets, lines = analyze_frame(frame, HandRecognizer(), {}, None, FakeClaim("4s", ["chi"]))
    check(lines[0] == "Claim: CHI 4s 5s 6s, then discard north | Shanten 1 -> 0", f"畫面第一行顯示吃的建議（{lines[0]}）")
    marked = [d['action'] for d in dets if d.get('action')]
    check(marked == ["CHI"], f"標出要按的按鈕（{marked}）")
    _, lines = analyze_frame(frame, HandRecognizer(), {}, None, FakeClaim("1p", []))
    check(lines[0].startswith("Claim: PASS on 1p"), f"不能吃碰時建議取消（{lines[0]}）")


def main():
    tests = [test_win, test_pon_when_it_helps, test_pass_when_pon_does_not_help, test_chi_choice, test_kan,
             test_concealed_kan, test_added_kan, test_analyze_frame_claim]
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
