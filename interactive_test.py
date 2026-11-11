#!/usr/bin/env python3
"""
互動式手牌測試工具
可以輸入手牌並測試各種功能
"""

from calculate_shanten import (
    calculate_shanten, 
    suggest_discard,
    calculate_max_melds,
    find_tatsu,
    count_tatsu,
    find_max_tatsu,
    find_pairs,
    visualize_hand,
    tile_to_chinese
)

def parse_hand_input(input_str: str) -> list:
    """解析用戶輸入的手牌字符串
    
    支援格式：
    - "1m 2m 3m ..." (空格分隔)
    - "1m,2m,3m,..." (逗號分隔)
    - "1m2m3m..." (連續)
    """
    # 移除空白和逗號
    input_str = input_str.replace(' ', '').replace(',', '')
    
    # 解析牌
    tiles = []
    i = 0
    while i < len(input_str):
        # 檢查是否為字牌
        word_tiles = ['east', 'south', 'west', 'north', 'middle', 'fa', 'white']
        found_word = False
        for word in word_tiles:
            if input_str[i:].startswith(word):
                tiles.append(word)
                i += len(word)
                found_word = True
                break
        
        if not found_word:
            # 數字牌：格式為 數字+字母
            if i + 2 <= len(input_str):
                tile = input_str[i:i+2]
                if tile[0].isdigit() and tile[1] in ['m', 'p', 's']:
                    tiles.append(tile)
                    i += 2
                else:
                    print(f"警告: 無法解析 '{input_str[i:i+2]}'，跳過")
                    i += 1
            else:
                print(f"警告: 輸入不完整，跳過剩餘部分")
                break
    
    return tiles

def print_tile_list(tiles: list, title: str = "手牌"):
    """格式化輸出牌列表"""
    print(f"\n{title}:")
    print(f"  數量: {len(tiles)} 張")
    
    # 使用視覺化功能顯示中文格式
    visual_str = visualize_hand(tiles, use_chinese=True)
    print(f"  視覺化: {visual_str}")
    
    # 同時顯示原始格式（用於參考）
    print(f"  原始格式: {', '.join(tiles)}")

def test_calculate_shanten(hand: list):
    """測試計算進聽數"""
    print("\n" + "="*60)
    print("測試: calculate_shanten (計算進聽數)")
    print("="*60)
    
    if len(hand) != 16:
        print(f"❌ 錯誤: 手牌必須是16張，目前有 {len(hand)} 張")
        return
    
    try:
        shanten = calculate_shanten(hand)
        print(f"\n✓ 進聽數: {shanten}")
        
        if shanten == 0:
            print("  → 已聽牌！")
        elif shanten == 1:
            print("  → 一進聽")
        elif shanten == 2:
            print("  → 二進聽")
        else:
            print(f"  → {shanten}進聽")
    except Exception as e:
        print(f"❌ 計算錯誤: {e}")

def test_suggest_discard(hand: list):
    """測試打牌建議（需要17張牌）"""
    print("\n" + "="*60)
    print("測試: suggest_discard (打牌建議)")
    print("="*60)
    
    if len(hand) != 17:
        print(f"❌ 錯誤: 打牌建議需要17張牌（16張手牌+1張摸到的牌），目前有 {len(hand)} 張")
        print("提示: 請輸入17張牌，最後一張會被視為摸到的牌")
        return
    
    try:
        result = suggest_discard(hand)
        
        # 使用中文顯示建議打掉的牌
        discard_tile_chinese = tile_to_chinese(result['tile'])
        print(f"\n✓ 建議打掉的牌: {discard_tile_chinese} ({result['tile']})")
        print(f"✓ 打掉後的進聽數: {result['shanten_after']}")
        print(f"✓ 建議原因: {result['reason']}")
        
        # 顯示最佳選項的詳細資訊
        if len(result['best_options']) > 0:
            best_opt = result['best_options'][0]
            
            if result['shanten_after'] == 0:
                # 已聽牌，顯示等待牌
                if best_opt.get('wait_count', 0) > 0:
                    print(f"\n等待牌資訊:")
                    print(f"  等待數量: {best_opt['wait_count']} 張")
                    wait_tiles = best_opt.get('wait_tiles', [])
                    # 使用中文顯示等待牌
                    wait_tiles_chinese = [tile_to_chinese(t) for t in wait_tiles]
                    if len(wait_tiles_chinese) <= 10:
                        print(f"  等待牌: {', '.join(wait_tiles_chinese)}")
                    else:
                        print(f"  等待牌: {', '.join(wait_tiles_chinese[:10])}... (共{len(wait_tiles_chinese)}張)")
            else:
                # 未聽牌，顯示進牌資訊
                if best_opt.get('improving_count', 0) > 0:
                    print(f"\n進牌資訊:")
                    print(f"  進牌數量: {best_opt['improving_count']} 張")
                    improving_tiles = best_opt.get('improving_tiles', [])
                    # 使用中文顯示進牌
                    improving_tiles_chinese = [tile_to_chinese(t) for t in improving_tiles]
                    if len(improving_tiles_chinese) <= 10:
                        print(f"  進牌: {', '.join(improving_tiles_chinese)}")
                    else:
                        print(f"  進牌: {', '.join(improving_tiles_chinese[:10])}... (共{len(improving_tiles_chinese)}張)")
        
        # 顯示所有選項（前10個）
        if len(result['all_options']) > 0:
            print(f"\n所有打牌選項（前10個）:")
            for i, opt in enumerate(result['all_options'][:10]):
                marker = " ← 建議" if opt['tile'] == result['tile'] else ""
                tile_chinese = tile_to_chinese(opt['tile'])
                print(f"  {i+1}. 打掉 {tile_chinese:4s} ({opt['tile']:6s}) → 進聽數: {opt['shanten']}{marker}")
            
            if len(result['all_options']) > 10:
                print(f"  ... (共 {len(result['all_options'])} 個選項)")
        
    except Exception as e:
        print(f"❌ 計算錯誤: {e}")
        import traceback
        traceback.print_exc()

def test_calculate_max_melds(hand: list):
    """測試計算最大面子數"""
    print("\n" + "="*60)
    print("測試: calculate_max_melds (計算最大面子數)")
    print("="*60)
    
    try:
        max_melds = calculate_max_melds(hand)
        print(f"\n✓ 最大面子數: {max_melds}")
    except Exception as e:
        print(f"❌ 計算錯誤: {e}")

def test_find_tatsu(hand: list):
    """測試尋找搭子"""
    print("\n" + "="*60)
    print("測試: find_tatsu (尋找所有搭子)")
    print("="*60)
    
    try:
        tatsu_list = find_tatsu(hand)
        print(f"\n✓ 找到 {len(tatsu_list)} 個搭子:")
        
        # 按類型分組
        by_type = {'pair': [], 'sequence': [], 'gap': []}
        for t1, t2, tatsu_type in tatsu_list:
            by_type[tatsu_type].append((t1, t2))
        
        type_names = {
            'pair': '對子搭子',
            'sequence': '連續搭子',
            'gap': '間隔搭子'
        }
        
        for tatsu_type, pairs in by_type.items():
            if pairs:
                print(f"\n  {type_names[tatsu_type]} ({len(pairs)} 個):")
                for t1, t2 in pairs[:10]:  # 最多顯示10個
                    print(f"    {t1} - {t2}")
                if len(pairs) > 10:
                    print(f"    ... (共 {len(pairs)} 個)")
    except Exception as e:
        print(f"❌ 計算錯誤: {e}")

def test_count_tatsu(hand: list):
    """測試計算搭子數量"""
    print("\n" + "="*60)
    print("測試: count_tatsu (計算搭子數量)")
    print("="*60)
    
    try:
        tatsu_count = count_tatsu(hand)
        print(f"\n✓ 搭子統計:")
        print(f"  對子搭子: {tatsu_count['pair']} 個")
        print(f"  連續搭子: {tatsu_count['sequence']} 個")
        print(f"  間隔搭子: {tatsu_count['gap']} 個")
        print(f"  總計: {tatsu_count['total']} 個")
    except Exception as e:
        print(f"❌ 計算錯誤: {e}")

def test_find_max_tatsu(hand: list):
    """測試尋找最多搭子組合"""
    print("\n" + "="*60)
    print("測試: find_max_tatsu (尋找最多搭子組合)")
    print("="*60)
    
    try:
        max_tatsu_list = find_max_tatsu(hand)
        print(f"\n✓ 最多搭子組合: {len(max_tatsu_list)} 個搭子")
        
        # 按類型分組
        by_type = {'pair': [], 'sequence': [], 'gap': []}
        for t1, t2, tatsu_type in max_tatsu_list:
            by_type[tatsu_type].append((t1, t2))
        
        type_names = {
            'pair': '對子搭子',
            'sequence': '連續搭子',
            'gap': '間隔搭子'
        }
        
        for tatsu_type, pairs in by_type.items():
            if pairs:
                print(f"\n  {type_names[tatsu_type]} ({len(pairs)} 個):")
                for t1, t2 in pairs:
                    print(f"    {t1} - {t2}")
    except Exception as e:
        print(f"❌ 計算錯誤: {e}")

def test_find_pairs(hand: list):
    """測試尋找對子"""
    print("\n" + "="*60)
    print("測試: find_pairs (尋找對子)")
    print("="*60)
    
    try:
        pairs = find_pairs(hand)
        print(f"\n✓ 找到 {len(pairs)} 個對子:")
        for t1, t2 in pairs:
            print(f"  {t1} - {t2}")
    except Exception as e:
        print(f"❌ 計算錯誤: {e}")

def show_menu():
    """顯示選單"""
    print("\n" + "="*60)
    print("請選擇要測試的功能:")
    print("="*60)
    print("1. calculate_shanten (計算進聽數) - 需要16張牌")
    print("2. suggest_discard (打牌建議) - 需要17張牌")
    print("3. calculate_max_melds (計算最大面子數)")
    print("4. find_tatsu (尋找所有搭子)")
    print("5. count_tatsu (計算搭子數量)")
    print("6. find_max_tatsu (尋找最多搭子組合)")
    print("7. find_pairs (尋找對子)")
    print("8. 測試所有功能 (16張牌)")
    print("9. 測試所有功能 (17張牌)")
    print("0. 退出")
    print("="*60)

def main():
    """主程式"""
    print("="*60)
    print("麻將手牌互動式測試工具")
    print("="*60)
    print("\n牌格式說明:")
    print("  數字牌: 1m-9m (萬), 1p-9p (筒), 1s-9s (條)")
    print("  字牌: east, south, west, north, middle, fa, white")
    print("\n輸入範例:")
    print("  1m 2m 3m 4m 5m 6m 7m 8m 1p 2p 3p 4p 5p 6p 7p 8p")
    print("  或: 1m2m3m4m5m6m7m8m1p2p3p4p5p6p7p8p")
    print("="*60)
    
    while True:
        show_menu()
        choice = input("\n請選擇 (0-9): ").strip()
        
        if choice == '0':
            print("\n再見！")
            break
        
        # 輸入手牌
        print("\n請輸入手牌（可用空格或逗號分隔，或連續輸入）:")
        hand_input = input("> ").strip()
        
        if not hand_input:
            print("❌ 輸入為空，請重新輸入")
            continue
        
        # 解析手牌
        hand = parse_hand_input(hand_input)
        
        if len(hand) == 0:
            print("❌ 無法解析手牌，請檢查輸入格式")
            continue
        
        print_tile_list(hand, "解析後的手牌")
        
        # 執行對應的測試
        if choice == '1':
            test_calculate_shanten(hand)
        elif choice == '2':
            test_suggest_discard(hand)
        elif choice == '3':
            test_calculate_max_melds(hand)
        elif choice == '4':
            test_find_tatsu(hand)
        elif choice == '5':
            test_count_tatsu(hand)
        elif choice == '6':
            test_find_max_tatsu(hand)
        elif choice == '7':
            test_find_pairs(hand)
        elif choice == '8':
            # 測試所有功能（16張牌）
            if len(hand) != 16:
                print(f"\n❌ 錯誤: 需要16張牌，目前有 {len(hand)} 張")
            else:
                test_calculate_shanten(hand)
                test_calculate_max_melds(hand)
                test_find_tatsu(hand)
                test_count_tatsu(hand)
                test_find_max_tatsu(hand)
                test_find_pairs(hand)
        elif choice == '9':
            # 測試所有功能（17張牌）
            if len(hand) != 17:
                print(f"\n❌ 錯誤: 需要17張牌，目前有 {len(hand)} 張")
            else:
                test_suggest_discard(hand)
                test_calculate_max_melds(hand)
                test_find_tatsu(hand)
                test_count_tatsu(hand)
                test_find_max_tatsu(hand)
                test_find_pairs(hand)
        else:
            print("❌ 無效的選擇，請重新輸入")
        
        # 等待用戶按 Enter 繼續
        input("\n按 Enter 繼續...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程式已中斷")
    except Exception as e:
        print(f"\n發生錯誤: {e}")
        import traceback
        traceback.print_exc()

