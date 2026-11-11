from calculate_shanten import ShantenCalculator, calculate_max_melds, find_tatsu, count_tatsu, find_max_tatsu, calculate_shanten

def assert_equal(actual, expected, message=""):
    """簡單的斷言函數"""
    if actual != expected:
        print(f"❌ 測試失敗: {message}")
        print(f"   期望: {expected}")
        print(f"   實際: {actual}")
        return False
    else:
        print(f"✓ {message}")
        return True

def parse_tile_string(tile_str):
    """解析牌字符串，返回 (類型, 數字) 用於測試"""
    calculator = ShantenCalculator()
    return calculator._parse_tile(tile_str)

def test_calculate_max_melds():
    """測試計算最大面子數量"""
    print("\n=== 測試計算最大面子數量 ===")
    # 手牌：[1萬,1萬,1萬,2萬,3萬,4萬,5萬,6萬,1筒,1筒,2筒,2筒,3筒,3筒,4筒,5筒]
    hand = ["1m", "1m", "1m", "2m", "3m", "4m", "5m", "6m",
            "1p", "1p", "2p", "2p", "3p", "3p", "4p", "5p"]
    
    calculator = ShantenCalculator()
    max_melds = calculator.calculate_max_melds(hand)
    assert_equal(max_melds, 4, "這手牌應該有4個面子")
    
    # 測試便捷函式
    max_melds_func = calculate_max_melds(hand)
    assert_equal(max_melds_func, 4, "便捷函式應該返回相同結果")

def test_calculate_max_melds_with_triplets():
    """測試計算最大面子數量（優先考慮刻子）"""
    print("\n=== 測試計算最大面子數量（刻子） ===")
    hand = ["1m", "1m", "1m", "2m", "2m", "2m", "3m", "3m", "3m",
            "4m", "4m", "4m", "5m", "5m", "5m", "6m"]
    
    calculator = ShantenCalculator()
    max_melds = calculator.calculate_max_melds(hand)
    assert_equal(max_melds, 5, "這手牌應該有5個面子")

def test_calculate_max_melds_with_straights():
    """測試計算最大面子數量（優先考慮順子）"""
    print("\n=== 測試計算最大面子數量（順子） ===")
    hand = ["1m", "2m", "3m", "2m", "3m", "4m", "3m", "4m", "5m",
            "4m", "5m", "6m", "5m", "6m", "7m", "6m"]
    
    calculator = ShantenCalculator()
    max_melds = calculator.calculate_max_melds(hand)
    assert_equal(max_melds, 5, "這手牌應該有5個面子")

def test_calculate_max_melds_with_honor_tiles():
    """測試包含字牌的情況"""
    print("\n=== 測試包含字牌的情況 ===")
    hand = ["1m", "1m", "2m", "3m", "4m", "5m", "6m", "7m",
            "east", "east", "east", "south", "south", "south", "middle", "middle"]
    
    calculator = ShantenCalculator()
    max_melds = calculator.calculate_max_melds(hand)
    assert_equal(max_melds, 4, "這手牌應該有4個面子")

def test_calculate_max_melds_no_pairs():
    """測試完全沒有搭子的手牌情況"""
    print("\n=== 測試完全沒有搭子的手牌情況 ===")
    hand = ["1m", "4m", "8m", "1p", "4p", "8p", "1s", "4s", "8s",
            "east", "south", "west", "north", "middle", "fa", "white"]
    
    calculator = ShantenCalculator()
    max_melds = calculator.calculate_max_melds(hand)
    assert_equal(max_melds, 0, "這手牌應該沒有面子")

def test_find_tatsu_pair():
    """測試尋找對子搭子"""
    print("\n=== 測試尋找對子搭子 ===")
    hand = ["1m", "1m", "2m", "3m"]
    
    calculator = ShantenCalculator()
    tatsu_list = calculator.find_tatsu(hand)
    
    # 檢查是否找到一個對子搭子
    pair_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in tatsu_list if tatsu_type == "pair"]
    assert_equal(len(pair_tatsu), 1, "應該找到一個對子搭子")
    
    # 檢查對子搭子的內容
    if len(pair_tatsu) > 0:
        t1, t2, tatsu_type = pair_tatsu[0]
        assert_equal(t1, "1m", "對子搭子的第一張牌應該是一萬")
        assert_equal(t2, "1m", "對子搭子的第二張牌應該是一萬")
    
    # 測試便捷函式
    tatsu_list_func = find_tatsu(hand)
    assert_equal(len(tatsu_list_func), len(tatsu_list), "便捷函式應該返回相同結果")

def test_find_tatsu_sequence():
    """測試尋找連續搭子"""
    print("\n=== 測試尋找連續搭子 ===")
    hand = ["1m", "2m", "4m", "5m"]
    
    calculator = ShantenCalculator()
    tatsu_list = calculator.find_tatsu(hand)
    
    # 檢查是否找到兩個連續搭子
    sequence_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in tatsu_list if tatsu_type == "sequence"]
    assert_equal(len(sequence_tatsu), 2, "應該找到兩個連續搭子")
    
    # 檢查連續搭子的內容，不依賴順序
    sequence_pairs = set()
    for t1, t2, _ in sequence_tatsu:
        tile_type1, num1 = parse_tile_string(t1)
        tile_type2, num2 = parse_tile_string(t2)
        if tile_type1 == tile_type2:
            sequence_pairs.add((num1, num2))
    
    assert_equal((1, 2) in sequence_pairs, True, "應該有 [1萬,2萬] 的連續搭子")
    assert_equal((4, 5) in sequence_pairs, True, "應該有 [4萬,5萬] 的連續搭子")

def test_find_tatsu_gap():
    """測試尋找間隔搭子"""
    print("\n=== 測試尋找間隔搭子 ===")
    hand = ["1m", "3m", "5m", "7m"]
    
    calculator = ShantenCalculator()
    tatsu_list = calculator.find_tatsu(hand)
    
    # 檢查是否找到三個間隔搭子
    gap_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in tatsu_list if tatsu_type == "gap"]
    assert_equal(len(gap_tatsu), 3, "應該找到三個間隔搭子")
    
    # 檢查間隔搭子的內容，不依賴順序
    gap_pairs = set()
    for t1, t2, _ in gap_tatsu:
        tile_type1, num1 = parse_tile_string(t1)
        tile_type2, num2 = parse_tile_string(t2)
        if tile_type1 == tile_type2:
            gap_pairs.add((num1, num2))
    
    assert_equal((1, 3) in gap_pairs, True, "應該有 [1萬,3萬] 的間隔搭子")
    assert_equal((3, 5) in gap_pairs, True, "應該有 [3萬,5萬] 的間隔搭子")
    assert_equal((5, 7) in gap_pairs, True, "應該有 [5萬,7萬] 的間隔搭子")

def test_find_tatsu_honor():
    """測試尋找字牌搭子"""
    print("\n=== 測試尋找字牌搭子 ===")
    hand = ["east", "east", "south", "west", "north", "middle", "middle"]
    
    calculator = ShantenCalculator()
    tatsu_list = calculator.find_tatsu(hand)
    
    # 檢查是否找到兩個對子搭子
    pair_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in tatsu_list if tatsu_type == "pair"]
    assert_equal(len(pair_tatsu), 2, "應該找到兩個對子搭子")
    
    # 檢查第一個對子搭子的內容
    if len(pair_tatsu) > 0:
        t1, t2, tatsu_type = pair_tatsu[0]
        assert_equal(t1, "east", "對子搭子的第一張牌應該是東風")
        assert_equal(t2, "east", "對子搭子的第二張牌應該是東風")
    
    # 檢查第二個對子搭子的內容
    if len(pair_tatsu) > 1:
        t1, t2, tatsu_type = pair_tatsu[1]
        assert_equal(t1, "middle", "對子搭子的第一張牌應該是紅中")
        assert_equal(t2, "middle", "對子搭子的第二張牌應該是紅中")

def test_count_tatsu():
    """測試計算搭子數量"""
    print("\n=== 測試計算搭子數量 ===")
    hand = ["1m", "1m", "2m", "3m", "4m", "6m", "east", "east", "middle", "middle"]
    
    calculator = ShantenCalculator()
    tatsu_list = calculator.find_tatsu(hand)
    
    # 檢查對子搭子
    pair_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in tatsu_list if tatsu_type == "pair"]
    assert_equal(len(pair_tatsu), 3, "應該有3個對子搭子")
    
    # 檢查連續搭子
    sequence_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in tatsu_list if tatsu_type == "sequence"]
    sequence_pairs = set()
    for t1, t2, _ in sequence_tatsu:
        tile_type1, num1 = parse_tile_string(t1)
        tile_type2, num2 = parse_tile_string(t2)
        if tile_type1 == "wan" and tile_type2 == "wan":
            sequence_pairs.add((num1, num2))
    
    assert_equal((2, 3) in sequence_pairs, True, "應該有 [2萬,3萬] 的連續搭子")
    assert_equal((3, 4) in sequence_pairs, True, "應該有 [3萬,4萬] 的連續搭子")
    
    # 檢查間隔搭子
    gap_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in tatsu_list if tatsu_type == "gap"]
    gap_pairs = set()
    for t1, t2, _ in gap_tatsu:
        tile_type1, num1 = parse_tile_string(t1)
        tile_type2, num2 = parse_tile_string(t2)
        if tile_type1 == "wan" and tile_type2 == "wan":
            gap_pairs.add((num1, num2))
    
    assert_equal((2, 4) in gap_pairs, True, "應該有 [2萬,4萬] 的間隔搭子")
    
    # 檢查總數
    tatsu_count = calculator.count_tatsu(hand)
    assert_equal(tatsu_count["pair"], 3, "應該有3個對子搭子")
    assert_equal(tatsu_count["total"], len(tatsu_list), "總搭子數量應該與搭子列表長度相同")
    
    # 測試便捷函式
    tatsu_count_func = count_tatsu(hand)
    assert_equal(tatsu_count_func["total"], tatsu_count["total"], "便捷函式應該返回相同結果")

def test_find_max_tatsu():
    """測試尋找最多搭子的組合"""
    print("\n=== 測試尋找最多搭子的組合 ===")
    hand = ["1m", "1m", "2m", "2m", "3m", "4m", "5m", "6m"]
    
    calculator = ShantenCalculator()
    max_tatsu_list = calculator.find_max_tatsu(hand)
    
    # 檢查搭子數量
    assert_equal(len(max_tatsu_list), 4, "應該找到4個搭子")
    
    # 檢查對子搭子
    pair_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in max_tatsu_list if tatsu_type == "pair"]
    assert_equal(len(pair_tatsu), 2, "應該有2個對子搭子")
    
    # 檢查連續搭子
    sequence_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in max_tatsu_list if tatsu_type == "sequence"]
    assert_equal(len(sequence_tatsu), 2, "應該有2個連續搭子")
    
    # 檢查間隔搭子
    gap_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in max_tatsu_list if tatsu_type == "gap"]
    assert_equal(len(gap_tatsu), 0, "應該沒有間隔搭子")
    
    # 測試便捷函式
    max_tatsu_list_func = find_max_tatsu(hand)
    assert_equal(len(max_tatsu_list_func), len(max_tatsu_list), "便捷函式應該返回相同結果")

def test_find_max_tatsu_simple():
    """測試簡單的最多搭子組合"""
    print("\n=== 測試簡單的最多搭子組合 ===")
    hand = ["1m", "2m", "4m", "5m"]
    
    calculator = ShantenCalculator()
    max_tatsu_list = calculator.find_max_tatsu(hand)
    
    # 檢查搭子數量
    assert_equal(len(max_tatsu_list), 2, "應該找到2個搭子")
    
    # 檢查連續搭子
    sequence_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in max_tatsu_list if tatsu_type == "sequence"]
    assert_equal(len(sequence_tatsu), 2, "應該有2個連續搭子")
    
    # 檢查連續搭子的內容，不依賴順序
    sequence_pairs = set()
    for t1, t2, _ in sequence_tatsu:
        tile_type1, num1 = parse_tile_string(t1)
        tile_type2, num2 = parse_tile_string(t2)
        if tile_type1 == tile_type2:
            sequence_pairs.add((num1, num2))
    
    assert_equal((1, 2) in sequence_pairs, True, "應該有 [1萬,2萬] 的連續搭子")
    assert_equal((4, 5) in sequence_pairs, True, "應該有 [4萬,5萬] 的連續搭子")

def test_find_max_tatsu_complex():
    """測試複雜的最多搭子組合"""
    print("\n=== 測試複雜的最多搭子組合 ===")
    hand = ["1m", "1m", "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m"]
    
    calculator = ShantenCalculator()
    max_tatsu_list = calculator.find_max_tatsu(hand)
    
    # 檢查搭子數量
    assert_equal(len(max_tatsu_list), 5, "應該找到5個搭子")
    
    # 檢查對子搭子
    pair_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in max_tatsu_list if tatsu_type == "pair"]
    assert_equal(len(pair_tatsu), 1, "應該有1個對子搭子")
    
    # 檢查連續搭子
    sequence_tatsu = [(t1, t2, tatsu_type) for t1, t2, tatsu_type in max_tatsu_list if tatsu_type == "sequence"]
    assert_equal(len(sequence_tatsu), 4, "應該有4個連續搭子")

def test_calculate_shanten_tenpai():
    """測試聽牌（0進聽）的情況"""
    print("\n=== 測試聽牌（0進聽）的情況 ===")
    hand = ["1m", "1m", "2m", "3m", "4m", "5m", "6m", "7m",
            "1p", "1p", "2p", "2p", "3p", "3p", "4p", "5p"]
    
    calculator = ShantenCalculator()
    shanten = calculator.calculate_shanten(hand)
    assert_equal(shanten, 0, "這手牌應該是聽牌（0進聽）")
    
    # 測試便捷函式
    shanten_func = calculate_shanten(hand)
    assert_equal(shanten_func, 0, "便捷函式應該返回相同結果")

def test_calculate_shanten_one_away():
    """測試一進聽的情況"""
    print("\n=== 測試一進聽的情況 ===")
    hand = ["1m", "1m", "1m", "2m", "3m", "4m", "5m", "7m",
            "1p", "1p", "2p", "2p", "3p", "3p", "4p", "5p"]
    
    calculator = ShantenCalculator()
    shanten = calculator.calculate_shanten(hand)
    assert_equal(shanten, 1, "這手牌應該是一進聽")

def test_calculate_shanten_two_away():
    """測試二進聽的情況"""
    print("\n=== 測試二進聽的情況 ===")
    hand = ["1m", "1m", "1m", "3m", "4m", "6m", "8m", "9m",
            "1p", "1p", "2p", "2p", "3p", "3p", "4p", "5p"]
    
    calculator = ShantenCalculator()
    shanten = calculator.calculate_shanten(hand)
    assert_equal(shanten, 2, "這手牌應該是二進聽")

def test_calculate_shanten_three_away():
    """測試三進聽的情況"""
    print("\n=== 測試三進聽的情況 ===")
    hand = ["1m", "1m", "2m", "7m", "7m", "8m",
            "1p", "2p", "3p", "6p", "7p", "9p",
            "5s", "6s", "9s", "9s"]
    
    calculator = ShantenCalculator()
    shanten = calculator.calculate_shanten(hand)
    assert_equal(shanten, 3, "這手牌應該是三進聽")

def test_calculate_shanten_four_away():
    """測試四進聽的情況"""
    print("\n=== 測試四進聽的情況 ===")
    hand = ["1m", "1m", "2m", "7m", "7m", "8m",
            "1p", "2p", "3p", "6p", "7p", "9p",
            "1s", "6s", "9s", "9s"]
    
    calculator = ShantenCalculator()
    shanten = calculator.calculate_shanten(hand)
    assert_equal(shanten, 4, "這手牌應該是四進聽")

def test_calculate_shanten_no_pairs():
    """測試完全沒有搭子的手牌情況"""
    print("\n=== 測試完全沒有搭子的手牌情況 ===")
    hand = ["1m", "4m", "8m", "1p", "4p", "8p", "1s", "4s", "8s",
            "east", "south", "west", "north", "middle", "fa", "white"]
    
    calculator = ShantenCalculator()
    shanten = calculator.calculate_shanten(hand)
    assert_equal(shanten, 10, "這手牌應該是十進聽")

def test_calculate_shanten_user_hand():
    """測試用戶指定手牌的進聽數"""
    print("\n=== 測試用戶指定手牌的進聽數 ===")
    hand = ["1m", "2m", "3m", "4m", "5m", "6m",
            "2p", "3p", "4p",
            "1s", "2s", "3s", "5s", "5s",
            "middle", "east"]
    
    calculator = ShantenCalculator()
    shanten = calculator.calculate_shanten(hand)
    assert_equal(shanten, 1, "這手牌應該是一進聽，只需要再湊一張中或東風成對子即可聽牌")
    
    # 測試便捷函式
    shanten_func = calculate_shanten(hand)
    assert_equal(shanten_func, 1, "便捷函式應該返回相同結果")

def test_calculate_shanten_four_triplets_two_pairs():
    """測試四刻子加兩對子的聽牌情況"""
    print("\n=== 測試四刻子加兩對子的聽牌情況 ===")
    # 手牌：1m,1m,1m,2m,2m,2m,3m,3m,3m,4m,4m,4m,east,east,west,west
    # 分析：
    # - 萬子：111, 222, 333, 444 可以組成4個刻子
    # - 字牌：east,east 和 west,west 是兩個對子
    # 總計：4個面子 + 2個對子，已經聽牌（聽 east 或 west）
    hand = ["1m", "1m", "1m", "2m", "2m", "2m", "3m", "3m", "3m", "4m", "4m", "4m",
            "east", "east", "west", "west"]
    
    calculator = ShantenCalculator()
    shanten = calculator.calculate_shanten(hand)
    print(f"   手牌: {hand}")
    print(f"   進聴數: {shanten}")
    assert_equal(shanten, 0, "這手牌應該是聽牌（0進聽），聽 east 或 west")
    
    # 測試便捷函式
    shanten_func = calculate_shanten(hand)
    assert_equal(shanten_func, 0, "便捷函式應該返回相同結果")

def main():
    """執行所有測試"""
    print("=" * 60)
    print("開始執行測試")
    print("=" * 60)
    
    tests = [
        test_calculate_max_melds,
        test_calculate_max_melds_with_triplets,
        test_calculate_max_melds_with_straights,
        test_calculate_max_melds_with_honor_tiles,
        test_calculate_max_melds_no_pairs,
        test_find_tatsu_pair,
        test_find_tatsu_sequence,
        test_find_tatsu_gap,
        test_find_tatsu_honor,
        test_count_tatsu,
        test_find_max_tatsu,
        test_find_max_tatsu_simple,
        test_find_max_tatsu_complex,
        test_calculate_shanten_tenpai,
        test_calculate_shanten_one_away,
        test_calculate_shanten_two_away,
        test_calculate_shanten_three_away,
        test_calculate_shanten_four_away,
        test_calculate_shanten_no_pairs,
        test_calculate_shanten_user_hand,
        test_calculate_shanten_four_triplets_two_pairs,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ 測試執行錯誤: {test.__name__}")
            print(f"   錯誤訊息: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"測試完成: 通過 {passed} 個，失敗 {failed} 個")
    print("=" * 60)

if __name__ == '__main__':
    main()
