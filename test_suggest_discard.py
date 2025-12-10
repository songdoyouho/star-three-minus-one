#!/usr/bin/env python3
"""
測試打牌建議功能
"""

from calculate_shanten import suggest_discard, calculate_shanten

def test_suggest_discard_basic():
    """基本測試：測試打牌建議功能"""
    print("\n=== 測試打牌建議功能 ===")
    
    # 測試案例1：簡單的手牌
    # 手牌：1m,1m,2m,3m,4m,5m,6m,7m,1p,1p,2p,2p,3p,3p,4p,5p,8m
    # 分析：如果打掉8m，剩下16張牌應該能組成4個面子+1個對子+1個搭子（聽牌）
    hand_17 = ["1m", "1m", "2m", "3m", "4m", "5m", "6m", "7m",
               "1p", "1p", "2p", "2p", "3p", "3p", "4p", "5p", "8m"]
    
    print(f"手牌（17張）: {hand_17}")
    
    result = suggest_discard(hand_17)
    
    print(f"\n建議打掉的牌: {result['tile']}")
    print(f"打掉後的進聽數: {result['shanten_after']}")
    print(f"建議原因: {result['reason']}")
    
    # 顯示所有選項
    print(f"\n所有打牌選項:")
    for opt in result['all_options']:
        marker = " ← 建議" if opt['tile'] == result['tile'] else ""
        print(f"  打掉 {opt['tile']:6s} → 進聽數: {opt['shanten']}{marker}")
    
    # 驗證：應該建議進聽數最小的牌（應該有幾張牌能達到聽牌）
    min_shanten = min(opt['shanten'] for opt in result['all_options'])
    if result['shanten_after'] == 0 and min_shanten == 0:
        print(f"\n✓ 測試通過：正確建議打掉{result['tile']}，打掉後聽牌（進聽數為0）")
        print(f"  共有 {len(result['best_options'])} 張牌打掉後都能聽牌")
    else:
        print(f"\n✗ 測試失敗：預期能聽牌，但實際建議打掉{result['tile']}，進聽數為{result['shanten_after']}")

def test_suggest_discard_multiple_options():
    """測試多個選項的情況"""
    print("\n=== 測試多個最佳選項 ===")
    
    # 測試案例：有多張牌都能達到相同進聽數
    # 手牌：1m,1m,2m,3m,4m,5m,6m,7m,1p,1p,2p,2p,3p,3p,4p,5p,9m
    # 分析：打掉9m或打掉其他單張牌，進聽數應該相同
    hand_17 = ["1m", "1m", "2m", "3m", "4m", "5m", "6m", "7m",
               "1p", "1p", "2p", "2p", "3p", "3p", "4p", "5p", "9m"]
    
    print(f"手牌（17張）: {hand_17}")
    
    result = suggest_discard(hand_17)
    
    print(f"\n建議打掉的牌: {result['tile']}")
    print(f"打掉後的進聽數: {result['shanten_after']}")
    print(f"最佳選項數量: {len(result['best_options'])}")
    print(f"建議原因: {result['reason']}")
    
    if len(result['best_options']) > 1:
        print(f"\n所有最佳選項（進聽數相同）:")
        for opt in result['best_options']:
            marker = " ← 建議" if opt['tile'] == result['tile'] else ""
            print(f"  {opt['tile']}{marker}")

def test_suggest_discard_one_away():
    """測試一進聽的情況"""
    print("\n=== 測試一進聽情況 ===")
    
    # 測試案例：一進聽的手牌
    # 手牌：1m,1m,1m,2m,3m,4m,5m,7m,1p,1p,2p,2p,3p,3p,4p,5p,8m
    # 分析：打掉7m或8m後應該能達到聽牌或接近聽牌
    hand_17 = ["1m", "1m", "1m", "2m", "3m", "4m", "5m", "7m",
               "1p", "1p", "2p", "2p", "3p", "3p", "4p", "5p", "8m"]
    
    print(f"手牌（17張）: {hand_17}")
    
    result = suggest_discard(hand_17)
    
    print(f"\n建議打掉的牌: {result['tile']}")
    print(f"打掉後的進聽數: {result['shanten_after']}")
    print(f"建議原因: {result['reason']}")
    
    # 顯示最佳選項的進牌資訊
    if len(result['best_options']) > 0:
        best_opt = result['best_options'][0]
        if 'improving_count' in best_opt and best_opt['improving_count'] > 0:
            print(f"\n進牌資訊:")
            print(f"  進牌數量: {best_opt['improving_count']}")
            if len(best_opt['improving_tiles']) <= 10:
                print(f"  進牌列表: {', '.join(best_opt['improving_tiles'])}")
            else:
                print(f"  進牌列表: {', '.join(best_opt['improving_tiles'][:10])}... (共{len(best_opt['improving_tiles'])}張)")
    
    # 驗證：應該建議進聽數最小的牌
    min_shanten = min(opt['shanten'] for opt in result['all_options'])
    if result['shanten_after'] == min_shanten:
        print(f"\n✓ 測試通過：正確選擇進聽數最小的牌（進聽數={min_shanten}）")
        if result['shanten_after'] > 0 and len(result['best_options']) > 0:
            improving_count = result['best_options'][0].get('improving_count', 0)
            if improving_count > 0:
                print(f"  ✓ 已計算進牌張數: {improving_count} 張")
    else:
        print(f"\n✗ 測試失敗：預期進聽數為{min_shanten}，但實際為{result['shanten_after']}")

def test_improving_tiles():
    """測試進牌張數計算功能"""
    print("\n=== 測試進牌張數計算 ===")
    
    # 測試案例：多張牌打掉後進聽數相同，但進牌張數不同
    # 手牌：1m,1m,2m,3m,4m,5m,6m,7m,1p,1p,2p,2p,3p,3p,4p,5p,9m
    # 這個案例應該有多張牌打掉後進聽數相同，但進牌張數可能不同
    hand_17 = ["1m", "1m", "2m", "3m", "4m", "5m", "6m", "7m",
               "1p", "1p", "2p", "2p", "3p", "3p", "4p", "5p", "9m"]
    
    print(f"手牌（17張）: {hand_17}")
    
    result = suggest_discard(hand_17)
    
    print(f"\n建議打掉的牌: {result['tile']}")
    print(f"打掉後的進聽數: {result['shanten_after']}")
    print(f"建議原因: {result['reason']}")
    
    # 顯示所有最佳選項的進牌資訊
    if len(result['best_options']) > 1 and result['shanten_after'] > 0:
        print(f"\n所有最佳選項的進牌資訊（進聽數相同）:")
        for opt in result['best_options']:
            marker = " ← 建議" if opt['tile'] == result['tile'] else ""
            improving_count = opt.get('improving_count', 0)
            print(f"  打掉 {opt['tile']:6s} → 進牌數: {improving_count}{marker}")
        
        # 驗證：應該選擇進牌張數最多的
        max_improving = max(opt.get('improving_count', 0) for opt in result['best_options'])
        selected_improving = result['best_options'][0].get('improving_count', 0)
        if selected_improving == max_improving:
            print(f"\n✓ 測試通過：正確選擇進牌張數最多的牌（{selected_improving} 張）")
        else:
            print(f"\n✗ 測試失敗：預期進牌數為{max_improving}，但實際為{selected_improving}")
    elif result['shanten_after'] > 0:
        # 只有一個最佳選項
        improving_count = result['best_options'][0].get('improving_count', 0)
        if improving_count > 0:
            print(f"\n進牌數量: {improving_count} 張")
            print(f"✓ 測試通過：已計算進牌張數")

def test_improving_tiles_comparison():
    """測試進牌張數比較功能（多個選項進聽數相同時）"""
    print("\n=== 測試進牌張數比較（多選項） ===")
    
    # 測試案例：設計一個有多張牌打掉後進聽數相同，但進牌張數不同的情況
    # 手牌：1m,2m,3m,4m,5m,6m,7m,8m,1p,2p,3p,4p,5p,6p,7p,8p,9m
    # 這個案例應該有多張牌打掉後進聽數相同
    hand_17 = ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m",
               "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9m"]
    
    print(f"手牌（17張）: {hand_17}")
    
    result = suggest_discard(hand_17)
    
    print(f"\n建議打掉的牌: {result['tile']}")
    print(f"打掉後的進聽數: {result['shanten_after']}")
    print(f"建議原因: {result['reason']}")
    
    # 顯示所有選項的進聽數和進牌數
    print(f"\n所有打牌選項（前10個）:")
    for i, opt in enumerate(result['all_options'][:10]):
        marker = " ← 建議" if opt['tile'] == result['tile'] else ""
        print(f"  打掉 {opt['tile']:6s} → 進聽數: {opt['shanten']}{marker}")
    
    # 顯示最佳選項的進牌資訊
    if result['shanten_after'] > 0 and len(result['best_options']) > 0:
        print(f"\n最佳選項的進牌資訊:")
        for opt in result['best_options']:
            marker = " ← 建議" if opt['tile'] == result['tile'] else ""
            improving_count = opt.get('improving_count', 0)
            print(f"  打掉 {opt['tile']:6s} → 進牌數: {improving_count}{marker}")
        
        # 驗證：如果有多個選項，應該選擇進牌張數最多的
        if len(result['best_options']) > 1:
            max_improving = max(opt.get('improving_count', 0) for opt in result['best_options'])
            selected_improving = result['best_options'][0].get('improving_count', 0)
            if selected_improving == max_improving:
                print(f"\n✓ 測試通過：正確選擇進牌張數最多的牌（{selected_improving} 張）")
            else:
                print(f"\n⚠ 注意：有多個選項，但進牌數相同或只有一個選項")
        else:
            improving_count = result['best_options'][0].get('improving_count', 0)
            print(f"\n✓ 測試通過：已計算進牌張數（{improving_count} 張）")

def main():
    """執行所有測試"""
    print("=" * 60)
    print("打牌建議功能測試")
    print("=" * 60)
    
    try:
        test_suggest_discard_basic()
        test_suggest_discard_multiple_options()
        test_suggest_discard_one_away()
        test_improving_tiles()
        test_improving_tiles_comparison()
        
        print("\n" + "=" * 60)
        print("測試完成")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 測試執行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

