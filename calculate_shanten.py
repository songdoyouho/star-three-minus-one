from typing import List, Dict, Tuple, Set, Any
from collections import defaultdict
from functools import lru_cache

class ShantenCalculator:
    """計算台灣麻將手牌進聽數的類別"""
    
    def __init__(self):
        self.total_tiles = 4  # 每種牌的總數量
    
    def _parse_tile(self, tile: str) -> Tuple[str, int]:
        """解析牌字符串，返回 (類型, 數字)
        
        Args:
            tile: 牌字符串，例如 "1m", "2p", "east"
            
        Returns:
            Tuple[str, int]: (類型, 數字)
                類型: "wan", "tong", "suo", "feng", "sanyuan"
                數字: 1-9 或字牌的編號
        """
        # 字牌映射
        word_tiles = {
            'east': ('feng', 1),
            'south': ('feng', 2),
            'west': ('feng', 3),
            'north': ('feng', 4),
            'middle': ('sanyuan', 1),
            'fa': ('sanyuan', 2),
            'white': ('sanyuan', 3)
        }
        
        if tile in word_tiles:
            return word_tiles[tile]
        
        # 數字牌：格式為 "數字+字母"
        if len(tile) >= 2:
            number = int(tile[0])
            suit = tile[1]
            if suit == 'm':
                return ('wan', number)
            elif suit == 'p':
                return ('tong', number)
            elif suit == 's':
                return ('suo', number)
        
        raise ValueError(f"無法解析牌: {tile}")
    
    def calculate_max_melds(self, hand: List[str]) -> int:
        """計算手牌中最多可以形成的面子數量
        
        Args:
            hand: 手牌列表，每個元素是牌字符串，例如 ["1m", "2m", "east"]
            
        Returns:
            int: 最多可以形成的面子數量
        """
        # 將牌按照類型分組
        grouped_tiles = self._group_tiles(hand)
        
        # 嘗試兩種計算方式，取最大值
        melds_prioritize_triplets, _ = self._count_melds_and_tatsu(grouped_tiles, True)
        melds_prioritize_straights, _ = self._count_melds_and_tatsu(grouped_tiles, False)
        
        # 返回最大的面子數量
        return max(melds_prioritize_triplets, melds_prioritize_straights)
    
    def _tile_to_string(self, tile_type: str, number: int) -> str:
        """將類型和數字轉換為牌字符串
        
        Args:
            tile_type: 類型 ("wan", "tong", "suo", "feng", "sanyuan")
            number: 數字 (1-9 或字牌編號)
            
        Returns:
            str: 牌字符串，例如 "1m", "2p", "east"
        """
        # 字牌映射
        word_tiles = {
            ('feng', 1): 'east',
            ('feng', 2): 'south',
            ('feng', 3): 'west',
            ('feng', 4): 'north',
            ('sanyuan', 1): 'middle',
            ('sanyuan', 2): 'fa',
            ('sanyuan', 3): 'white'
        }
        
        if (tile_type, number) in word_tiles:
            return word_tiles[(tile_type, number)]
        
        # 數字牌
        suit_map = {'wan': 'm', 'tong': 'p', 'suo': 's'}
        if tile_type in suit_map:
            return f"{number}{suit_map[tile_type]}"
        
        raise ValueError(f"無法轉換牌: {tile_type}, {number}")
    
    def _tile_to_chinese(self, tile: str) -> str:
        """將牌字符串轉換為中文顯示格式（僅用於 command line）
        
        Args:
            tile: 牌字符串，例如 "1m", "2p", "east"
            
        Returns:
            str: 中文格式，例如 "一萬", "二筒", "東"
        """
        # 字牌中文映射
        word_tiles_chinese = {
            'east': '東',
            'south': '南',
            'west': '西',
            'north': '北',
            'middle': '中',
            'fa': '發',
            'white': '白'
        }
        
        if tile in word_tiles_chinese:
            return word_tiles_chinese[tile]
        
        # 數字牌
        if len(tile) >= 2 and tile[0].isdigit():
            number = int(tile[0])
            suit = tile[1]
            
            # 數字中文映射
            number_chinese = {
                1: '一', 2: '二', 3: '三', 4: '四', 5: '五',
                6: '六', 7: '七', 8: '八', 9: '九'
            }
            
            # 花色中文映射
            suit_chinese = {
                'm': '萬',
                'p': '筒',
                's': '條'
            }
            
            if number in number_chinese and suit in suit_chinese:
                return f"{number_chinese[number]}{suit_chinese[suit]}"
        
        # 如果無法轉換，返回原字符串
        return tile
    
    def visualize_hand(self, hand: List[str], use_chinese: bool = True) -> str:
        """視覺化手牌，返回格式化的字符串
        
        Args:
            hand: 手牌列表
            use_chinese: 是否使用中文顯示（True 用於 command line，False 用於 OpenCV）
            
        Returns:
            str: 格式化的手牌字符串
        """
        if len(hand) == 0:
            return "空手牌"
        
        # 將牌按照類型分組
        grouped = self._group_tiles(hand)
        
        result_parts = []
        
        # 處理數字牌（萬、筒、條）
        suit_order = [('wan', '萬'), ('tong', '筒'), ('suo', '條')]
        for tile_type, suit_name in suit_order:
            if tile_type in grouped:
                numbers = grouped[tile_type]
                tiles_in_suit = []
                
                # 按數字排序
                for num in sorted(numbers.keys()):
                    count = numbers[num]
                    tile_str = self._tile_to_string(tile_type, num)
                    
                    if use_chinese:
                        # 使用中文顯示
                        chinese_tile = self._tile_to_chinese(tile_str)
                        tiles_in_suit.extend([chinese_tile] * count)
                    else:
                        # 使用英文格式（用於 OpenCV）
                        tiles_in_suit.extend([tile_str] * count)
                
                if tiles_in_suit:
                    if use_chinese:
                        result_parts.append(f"{suit_name}: {','.join(tiles_in_suit)}")
                    else:
                        result_parts.append(f"{tile_type}: {','.join(tiles_in_suit)}")
        
        # 處理字牌（風牌和三元牌）
        word_groups = {
            'feng': [],
            'sanyuan': []
        }
        
        word_tiles_map = {
            'east': ('feng', '東'),
            'south': ('feng', '南'),
            'west': ('feng', '西'),
            'north': ('feng', '北'),
            'middle': ('sanyuan', '中'),
            'fa': ('sanyuan', '發'),
            'white': ('sanyuan', '白')
        }
        
        for tile_type in ['feng', 'sanyuan']:
            if tile_type in grouped:
                numbers = grouped[tile_type]
                tiles_in_group = []
                
                for num in sorted(numbers.keys()):
                    count = numbers[num]
                    tile_str = self._tile_to_string(tile_type, num)
                    
                    if use_chinese:
                        chinese_tile = self._tile_to_chinese(tile_str)
                        tiles_in_group.extend([chinese_tile] * count)
                    else:
                        tiles_in_group.extend([tile_str] * count)
                
                if tiles_in_group:
                    if use_chinese:
                        group_name = '風' if tile_type == 'feng' else '三元'
                        result_parts.append(f"{group_name}: {','.join(tiles_in_group)}")
                    else:
                        result_parts.append(f"{tile_type}: {','.join(tiles_in_group)}")
        
        # 組合結果
        if result_parts:
            return " | ".join(result_parts)
        else:
            return "無法解析手牌"
    
    def find_tatsu(self, hand: List[str]) -> List[Tuple[str, str, str]]:
        """尋找手牌中的所有搭子
        
        搭子是指可以升級為面子的組合，包括：
        1. 對子搭子（兩張相同的牌）
        2. 連續搭子（兩張連續的牌，如 1-2）
        3. 間隔搭子（兩張間隔一張的牌，如 1-3）
        
        Args:
            hand: 手牌列表，可以是任意數量的牌，每個元素是牌字符串
            
        Returns:
            List[Tuple[str, str, str]]: 搭子列表，每個元素是一個元組，包含兩張牌和搭子類型
                搭子類型可以是 "pair"（對子）, "sequence"（連續搭子）, "gap"（間隔搭子）
        """
        # 將牌按照類型分組
        grouped_tiles = self._group_tiles(hand)
        
        # 搭子列表
        tatsu_list = []
        
        # 處理數字牌
        for tile_type in ['wan', 'tong', 'suo']:
            if tile_type not in grouped_tiles:
                continue
                
            numbers = grouped_tiles[tile_type].copy()
            
            # 找對子搭子
            for num, count in list(numbers.items()):
                if count >= 2:
                    tile_str = self._tile_to_string(tile_type, num)
                    # 添加對子搭子
                    tatsu_list.append((tile_str, tile_str, "pair"))
                    # 如果有多於兩張相同的牌，可以形成多個對子
                    if count >= 4:
                        tatsu_list.append((tile_str, tile_str, "pair"))
            
            # 找連續搭子
            # 使用集合來避免重複計算
            sequence_pairs = set()
            for num in range(1, 9):
                if (numbers.get(num, 0) > 0 and numbers.get(num + 1, 0) > 0):
                    sequence_pairs.add((num, num + 1))
            
            # 添加連續搭子
            for num1, num2 in sequence_pairs:
                tile1 = self._tile_to_string(tile_type, num1)
                tile2 = self._tile_to_string(tile_type, num2)
                tatsu_list.append((tile1, tile2, "sequence"))
            
            # 找間隔搭子
            # 使用集合來避免重複計算
            gap_pairs = set()
            for num in range(1, 8):
                if (numbers.get(num, 0) > 0 and numbers.get(num + 2, 0) > 0):
                    gap_pairs.add((num, num + 2))
            
            # 添加間隔搭子
            for num1, num2 in gap_pairs:
                tile1 = self._tile_to_string(tile_type, num1)
                tile2 = self._tile_to_string(tile_type, num2)
                tatsu_list.append((tile1, tile2, "gap"))
        
        # 處理字牌（風牌和三元牌）
        for tile_type in ['feng', 'sanyuan']:
            if tile_type not in grouped_tiles:
                continue
                
            numbers = grouped_tiles[tile_type].copy()
            
            # 字牌只能形成對子搭子
            for num, count in list(numbers.items()):
                if count >= 2:
                    tile_str = self._tile_to_string(tile_type, num)
                    # 添加對子搭子
                    tatsu_list.append((tile_str, tile_str, "pair"))
                    # 如果有多於兩張相同的牌，可以形成多個對子
                    if count >= 4:
                        tatsu_list.append((tile_str, tile_str, "pair"))
        
        return tatsu_list
    
    def count_tatsu(self, hand: List[str]) -> Dict[str, int]:
        """計算手牌中各類型搭子的數量
        
        Args:
            hand: 手牌列表，可以是任意數量的牌，每個元素是牌字符串
            
        Returns:
            Dict[str, int]: 各類型搭子的數量，包括：
                - "pair": 對子搭子數量
                - "sequence": 連續搭子數量
                - "gap": 間隔搭子數量
                - "total": 總搭子數量
        """
        tatsu_list = self.find_tatsu(hand)
        
        # 計算各類型搭子的數量
        tatsu_count = {
            "pair": 0,
            "sequence": 0,
            "gap": 0,
            "total": 0
        }
        
        for _, _, tatsu_type in tatsu_list:
            tatsu_count[tatsu_type] += 1
            tatsu_count["total"] += 1
        
        return tatsu_count
    
    def _group_tiles(self, hand: List[str]) -> Dict[str, Dict[int, int]]:
        """將牌按照類型和數字分組
        
        Args:
            hand: 手牌列表，每個元素是牌字符串，例如 ["1m", "2m", "east"]
            
        Returns:
            Dict[str, Dict[int, int]]: 分組後的牌，例如 {"wan": {1: 2, 2: 1}, "feng": {1: 1}}
        """
        groups = defaultdict(lambda: defaultdict(int))
        for tile in hand:
            tile_type, number = self._parse_tile(tile)
            groups[tile_type][number] += 1
        return groups
    
    def _count_melds_and_tatsu(self, grouped_tiles: Dict[str, Dict[int, int]], prioritize_triplets: bool = True) -> Tuple[int, int]:
        """計算面子和搭子的數量
        
        Args:
            grouped_tiles: 分組後的牌，格式為 {"wan": {1: 2, 2: 1}, ...}
            prioritize_triplets: 是否優先考慮刻子，如果為False則優先考慮順子
            
        Returns:
            Tuple[int, int]: (面子數量, 搭子數量)
        """
        total_melds = 0
        total_tatsu = 0
        
        # 處理數字牌
        for tile_type in ['wan', 'tong', 'suo']:
            if tile_type not in grouped_tiles:
                continue
                
            numbers = grouped_tiles[tile_type].copy()
            
            # 根據優先級處理面子
            if prioritize_triplets:
                # 先找刻子
                for num, count in list(numbers.items()):
                    if count >= 3:
                        total_melds += 1
                        numbers[num] -= 3
                
                # 再找順子
                while True:
                    found_straight = False
                    for num in range(1, 8):
                        if (numbers.get(num, 0) > 0 and 
                            numbers.get(num + 1, 0) > 0 and 
                            numbers.get(num + 2, 0) > 0):
                            numbers[num] -= 1
                            numbers[num + 1] -= 1
                            numbers[num + 2] -= 1
                            total_melds += 1
                            found_straight = True
                            break  # 找到一個就中斷，再繼續找下一個
                    if not found_straight:
                        break
            else:
                # 先找順子，使用貪婪算法
                while True:
                    found_straight = False
                    for num in range(1, 8):
                        if (numbers.get(num, 0) > 0 and 
                            numbers.get(num + 1, 0) > 0 and 
                            numbers.get(num + 2, 0) > 0):
                            numbers[num] -= 1
                            numbers[num + 1] -= 1
                            numbers[num + 2] -= 1
                            total_melds += 1
                            found_straight = True
                            break  # 找到一個就中斷，再繼續找下一個
                    if not found_straight:
                        break
                
                # 再找刻子
                for num, count in list(numbers.items()):
                    if count >= 3:
                        total_melds += 1
                        numbers[num] -= 3
            
            # 找搭子
            tatsu_count = 0
            
            # 先找對子搭子
            for num, count in list(numbers.items()):
                if count >= 2:
                    tatsu_count += 1
                    numbers[num] -= 2
            
            # 再找連續搭子
            for num in range(1, 9):
                if (numbers.get(num, 0) > 0 and numbers.get(num + 1, 0) > 0):
                    tatsu_count += 1
                    numbers[num] -= 1
                    numbers[num + 1] -= 1
            
            # 再找間隔搭子
            for num in range(1, 8):
                if (numbers.get(num, 0) > 0 and numbers.get(num + 2, 0) > 0):
                    tatsu_count += 1
                    numbers[num] -= 1
                    numbers[num + 2] -= 1
            
            total_tatsu += tatsu_count
        
        # 處理字牌（風牌和三元牌）
        for tile_type in ['feng', 'sanyuan']:
            if tile_type not in grouped_tiles:
                continue
                
            numbers = grouped_tiles[tile_type].copy()
            
            # 字牌只能形成刻子
            for num, count in list(numbers.items()):
                if count >= 3:
                    total_melds += 1
                    numbers[num] -= 3
                
                # 剩下的可以形成對子搭子
                if count % 3 >= 2:
                    total_tatsu += 1
        
        return total_melds, total_tatsu

    def find_max_tatsu(self, hand: List[str]) -> List[Tuple[str, str, str]]:
        """尋找手牌中最多搭子的組合
        
        與 find_tatsu 不同，這個函式會找出手牌中最多搭子的組合，而不是所有可能的搭子。
        每張牌只會被使用一次，不會重複計算。
        
        搭子優先順序：
        1. 對子搭子（兩張相同的牌）
        2. 連續搭子（兩張連續的牌，如 1-2）
        3. 間隔搭子（兩張間隔一張的牌，如 1-3）
        
        Args:
            hand: 手牌列表，可以是任意數量的牌，每個元素是牌字符串
            
        Returns:
            List[Tuple[str, str, str]]: 搭子列表，每個元素是一個元組，包含兩張牌和搭子類型
        """
        # 將牌按照類型分組
        grouped_tiles = self._group_tiles(hand)
        
        # 搭子列表
        tatsu_list = []
        
        # 處理數字牌
        for tile_type in ['wan', 'tong', 'suo']:
            if tile_type not in grouped_tiles:
                continue
                
            numbers = grouped_tiles[tile_type].copy()
            
            # 先找對子搭子（優先級最高）
            for num, count in list(numbers.items()):
                while count >= 2:
                    tile_str = self._tile_to_string(tile_type, num)
                    # 添加對子搭子
                    tatsu_list.append((tile_str, tile_str, "pair"))
                    numbers[num] -= 2
                    count -= 2
            
            # 再找連續搭子（優先級次之）
            for num in range(1, 9):
                while numbers.get(num, 0) > 0 and numbers.get(num + 1, 0) > 0:
                    tile1 = self._tile_to_string(tile_type, num)
                    tile2 = self._tile_to_string(tile_type, num + 1)
                    # 添加連續搭子
                    tatsu_list.append((tile1, tile2, "sequence"))
                    numbers[num] -= 1
                    numbers[num + 1] -= 1
            
            # 最後找間隔搭子（優先級最低）
            for num in range(1, 8):
                while numbers.get(num, 0) > 0 and numbers.get(num + 2, 0) > 0:
                    tile1 = self._tile_to_string(tile_type, num)
                    tile2 = self._tile_to_string(tile_type, num + 2)
                    # 添加間隔搭子
                    tatsu_list.append((tile1, tile2, "gap"))
                    numbers[num] -= 1
                    numbers[num + 2] -= 1
        
        # 處理字牌（風牌和三元牌）
        for tile_type in ['feng', 'sanyuan']:
            if tile_type not in grouped_tiles:
                continue
                
            numbers = grouped_tiles[tile_type].copy()
            
            # 字牌只能形成對子搭子
            for num, count in list(numbers.items()):
                while count >= 2:
                    tile_str = self._tile_to_string(tile_type, num)
                    # 添加對子搭子
                    tatsu_list.append((tile_str, tile_str, "pair"))
                    numbers[num] -= 2
                    count -= 2
        
        return tatsu_list

    def find_pairs(self, hand: List[str]) -> List[Tuple[str, str]]:
        """尋找手牌中所有的對子

        Args:
            hand: 手牌列表，每個元素是牌字符串

        Returns:
            包含對子的列表，每個對子表示為 (牌1, 牌2)
        """
        grouped_tiles = self._group_tiles(hand)
        pairs_list = []

        # 遍歷所有花色和點數
        for tile_type in grouped_tiles:
            for num, count in grouped_tiles[tile_type].items():
                # 如果數量大於等於2，則形成對子
                if count >= 2:
                    tile_str = self._tile_to_string(tile_type, num)
                    pairs_list.append((tile_str, tile_str))
        
        return pairs_list

    def calculate_shanten(self, hand: List[str]) -> int:
        """計算手牌的進聽數（精確解）

        進聽數 = 距離聽牌還需要換幾張牌（0 = 聽牌）。

        台灣麻將 16 張：胡牌需 5 個面子 + 1 個對子（眼）。
        做法：枚舉「選哪個對子當眼（或不選）」，再對每種花色完整枚舉
        面子/搭子的所有拆法，套用標準公式：
            進聽數 = 2 × 5 - 2 × 面子數 - 搭子數 - (有眼 ? 1 : 0)
        其中 面子數 + 搭子數 ≤ 5（多出來的搭子沒有用）。

        Args:
            hand: 手牌列表，應該是16張牌，每個元素是牌字符串，例如 ["1m", "2m", "east"]

        Returns:
            int: 進聽數
        """
        if len(hand) != 16:
            raise ValueError(f"手牌必須是16張，目前有 {len(hand)} 張。計算進聴數需要固定的手牌數量。")

        needed_melds = 5
        grouped = self._group_tiles(hand)
        # 每種花色/字牌轉成固定長度的張數陣列
        counts = {}
        for tile_type in ('wan', 'tong', 'suo'):
            counts[tile_type] = [grouped[tile_type].get(n, 0) for n in range(1, 10)] if tile_type in grouped else [0] * 9
        honors = [grouped['feng'].get(n, 0) for n in range(1, 5)] if 'feng' in grouped else [0] * 4
        honors += [grouped['sanyuan'].get(n, 0) for n in range(1, 4)] if 'sanyuan' in grouped else [0] * 3

        def best_shanten(suit_counts, honor_counts, has_head):
            options = {(0, 0)}
            for c in suit_counts.values():
                options = _merge_options(options, _suit_options(tuple(c)))
            options = _merge_options(options, _honor_options(tuple(honor_counts)))
            best = min(
                2 * needed_melds - 2 * m - min(t, needed_melds - m)
                for m, t in options
            )
            return best - (1 if has_head else 0)

        # 不選眼
        shanten = best_shanten(counts, honors, False)

        # 枚舉每一種對子當眼
        for tile_type, arr in counts.items():
            for i in range(9):
                if arr[i] >= 2:
                    arr[i] -= 2
                    shanten = min(shanten, best_shanten(counts, honors, True))
                    arr[i] += 2
        for i in range(7):
            if honors[i] >= 2:
                honors[i] -= 2
                shanten = min(shanten, best_shanten(counts, honors, True))
                honors[i] += 2

        return shanten
    



    def _all_tile_labels(self) -> List[str]:
        """回傳34種牌的標籤列表"""
        tiles = []
        for i in range(1, 10):
            tiles.extend([f"{i}m", f"{i}p", f"{i}s"])
        tiles.extend(['east', 'south', 'west', 'north', 'middle', 'fa', 'white'])
        return tiles

    def _can_form_complete_hand(self, hand: List[str]) -> bool:
        """判斷17張牌是否已經和牌（5個面子 + 1對子）"""
        if len(hand) != 17:
            return False

        grouped = self._group_tiles(hand)

        # 嘗試每一種可能的對子作為將牌
        for tile_type, numbers in grouped.items():
            for num, count in list(numbers.items()):
                if count >= 2:
                    grouped_copy = {t: n.copy() for t, n in grouped.items()}
                    # 先移除對子
                    grouped_copy[tile_type][num] -= 2
                    if grouped_copy[tile_type][num] == 0:
                        del grouped_copy[tile_type][num]
                    if len(grouped_copy[tile_type]) == 0:
                        del grouped_copy[tile_type]

                    # 嘗試拆成5個面子
                    if self._can_form_all_melds(grouped_copy):
                        return True
        return False

    def _can_form_all_melds(self, grouped_tiles: Dict[str, Dict[int, int]]) -> bool:
        """檢查所有剩餘的牌能否完全拆成面子（每個面子3張）"""
        for tile_type, numbers in grouped_tiles.items():
            if tile_type in ['wan', 'tong', 'suo']:
                if not self._can_form_melds_numbers(numbers):
                    return False
            else:
                # 字牌只能刻子，數量需為3的倍數
                for _, count in numbers.items():
                    if count % 3 != 0:
                        return False
        return True

    def _can_form_melds_numbers(self, numbers: Dict[int, int]) -> bool:
        """檢查數字牌是否能拆成面子"""
        counts = defaultdict(int, numbers)

        def backtrack(counts_dict: Dict[int, int]) -> bool:
            # 移除為0的鍵
            to_delete = [k for k, v in list(counts_dict.items()) if v == 0]
            for k in to_delete:
                del counts_dict[k]

            if not counts_dict:
                return True

            first = min(counts_dict.keys())

            # 嘗試刻子
            if counts_dict[first] >= 3:
                counts_dict[first] -= 3
                if backtrack(counts_dict):
                    counts_dict[first] += 3
                    return True
                counts_dict[first] += 3

            # 嘗試順子 first, first+1, first+2
            if (counts_dict.get(first, 0) > 0 and
                counts_dict.get(first + 1, 0) > 0 and
                counts_dict.get(first + 2, 0) > 0):
                counts_dict[first] -= 1
                counts_dict[first + 1] -= 1
                counts_dict[first + 2] -= 1
                if backtrack(counts_dict):
                    counts_dict[first] += 1
                    counts_dict[first + 1] += 1
                    counts_dict[first + 2] += 1
                    return True
                counts_dict[first] += 1
                counts_dict[first + 1] += 1
                counts_dict[first + 2] += 1

            return False

        return backtrack(counts)

    def _count_waiting_tiles(self, hand_16: List[str]) -> Tuple[int, List[str]]:
        """在進聽數為0的情況下，計算能胡的等待牌數量"""
        waits = []
        for tile in self._all_tile_labels():
            candidate = hand_16 + [tile]
            if self._can_form_complete_hand(candidate):
                waits.append(tile)
        return len(waits), waits

    def _count_improving_tiles(self, hand_16: List[str], current_shanten: int) -> Tuple[int, List[str]]:
        """計算能讓進聽數減少的進牌張數
        
        對於16張牌（進聽數為 current_shanten），計算加入哪些牌後，
        能讓進聽數進一步減少（變成 < current_shanten）。
        
        Args:
            hand_16: 16張牌的列表
            current_shanten: 當前16張牌的進聽數
            
        Returns:
            Tuple[int, List[str]]: (進牌數量, 進牌列表)
        """
        improving_tiles = []
        
        # 嘗試加入每一種可能的牌
        for tile in self._all_tile_labels():
            # 加入這張牌後變成17張
            hand_17 = hand_16 + [tile]
            
            # 計算這17張牌的最佳打牌選項（打掉某張後的最小進聽數）
            # 方法：對每張牌，計算打掉後剩餘16張的進聽數，取最小值
            min_shanten_after = None
            
            for i in range(len(hand_17)):
                hand_after_discard = hand_17[:i] + hand_17[i+1:]
                try:
                    shanten = self.calculate_shanten(hand_after_discard)
                    if min_shanten_after is None or shanten < min_shanten_after:
                        min_shanten_after = shanten
                except:
                    continue
            
            # 如果加入這張牌後，最佳進聽數 < 當前進聽數，則這張牌是進牌
            if min_shanten_after is not None and min_shanten_after < current_shanten:
                improving_tiles.append(tile)
        
        return len(improving_tiles), improving_tiles

    def suggest_discard(self, hand_17: List[str]) -> Dict[str, Any]:
        """建議17張牌中應該打哪一張
        
        這個方法會對每張牌進行評估，計算打掉該牌後剩餘16張牌的進聽數，
        然後選擇進聽數最小的牌作為建議。
        
        Args:
            hand_17: 17張牌的列表（16張手牌 + 1張摸到的牌），每個元素是牌字符串
            
        Returns:
            Dict[str, any]: 建議結果，包含：
                - 'tile': 建議打掉的牌
                - 'shanten_after': 打掉該牌後的進聽數
                - 'all_options': 所有可能的打牌選項列表，每個選項包含：
                    - 'tile': 牌
                    - 'shanten': 打掉後的進聽數
                - 'best_options': 所有最佳選項列表（進聽數相同的牌）
                - 'reason': 建議原因
        """
        if len(hand_17) != 17:
            raise ValueError(f"手牌必須是17張，目前有 {len(hand_17)} 張")
        
        # 儲存所有可能的打牌選項
        options = []
        
        # 對每張牌進行評估
        for i, tile in enumerate(hand_17):
            # 創建移除該牌後的16張牌列表
            hand_16 = hand_17[:i] + hand_17[i+1:]
            
            # 計算這16張牌的進聽數
            try:
                shanten = self.calculate_shanten(hand_16)
                options.append({
                    'tile': tile,
                    'shanten': shanten,
                    'index': i  # 紀錄位置，處理重複牌時使用
                })
            except Exception as e:
                # 如果計算失敗，跳過這張牌
                print(f"警告: 計算打掉 {tile} 後的進聽數時發生錯誤: {e}")
                continue
        
        if len(options) == 0:
            raise ValueError("無法計算任何打牌選項")
        
        # 找出進聽數最小的選項
        best_option = min(options, key=lambda x: x['shanten'])
        
        # 找出所有進聽數相同的選項（可能有多張牌都能達到相同進聽數）
        best_shanten = best_option['shanten']
        best_options = [opt for opt in options if opt['shanten'] == best_shanten]
        
        # 若進聽數為0，計算等待張數，優先等待越多的牌
        if best_shanten == 0:
            enriched = []
            for opt in best_options:
                hand_16 = hand_17[:opt['index']] + hand_17[opt['index'] + 1:]
                wait_count, wait_tiles = self._count_waiting_tiles(hand_16)
                opt = opt.copy()
                opt['wait_count'] = wait_count
                opt['wait_tiles'] = wait_tiles
                opt['improving_count'] = 0  # 聽牌時不需要進牌
                opt['improving_tiles'] = []
                enriched.append(opt)
            max_wait = max(enriched, key=lambda x: x['wait_count'])['wait_count']
            best_options = [o for o in enriched if o['wait_count'] == max_wait]
        else:
            # 若進聽數 > 0，計算進牌張數，優先進牌越多的牌
            enriched = []
            for opt in best_options:
                hand_16 = hand_17[:opt['index']] + hand_17[opt['index'] + 1:]
                improving_count, improving_tiles = self._count_improving_tiles(hand_16, best_shanten)
                opt = opt.copy()
                opt['wait_count'] = 0  # 未聽牌時沒有等待牌
                opt['wait_tiles'] = []
                opt['improving_count'] = improving_count
                opt['improving_tiles'] = improving_tiles
                enriched.append(opt)
            
            # 選擇進牌張數最多的選項
            if len(enriched) > 1:
                max_improving = max(enriched, key=lambda x: x['improving_count'])['improving_count']
                best_options = [o for o in enriched if o['improving_count'] == max_improving]
            else:
                best_options = enriched

        # 如果有多張牌進聽數（及等待數）相同，仍選第一張
        suggested_tile = best_options[0]['tile']
        
        # 生成建議原因
        if best_shanten == 0:
            reason = f"打掉這張牌後已聽牌，等待 {best_options[0]['wait_count']} 張"
        elif len(best_options) > 1:
            improving_count = best_options[0].get('improving_count', 0)
            if improving_count > 0:
                reason = f"打掉這張牌後進聽數為 {best_shanten}，有 {improving_count} 張進牌（共有 {len(best_options)} 張牌可達到此進聽數）"
            else:
                reason = f"打掉這張牌後進聽數為 {best_shanten}（共有 {len(best_options)} 張牌可達到此進聽數）"
        else:
            improving_count = best_options[0].get('improving_count', 0)
            if improving_count > 0:
                reason = f"打掉這張牌後進聽數為 {best_shanten}，有 {improving_count} 張進牌"
            else:
                reason = f"打掉這張牌後進聽數為 {best_shanten}，是最佳選擇"
        
        return {
            'tile': suggested_tile,
            'shanten_after': best_shanten,
            'all_options': options,
            'best_options': best_options,  # 所有最佳選項
            'reason': reason
        }


def _prune_options(options: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    """只保留不被支配的 (面子數, 搭子數) 組合"""
    return {
        (m, t) for m, t in options
        if not any((m2 >= m and t2 >= t and (m2, t2) != (m, t)) for m2, t2 in options)
    }


def _merge_options(a: Set[Tuple[int, int]], b: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    """合併兩組拆法：面子數、搭子數各自相加"""
    return _prune_options({(m1 + m2, t1 + t2) for m1, t1 in a for m2, t2 in b})


@lru_cache(maxsize=None)
def _suit_options(counts: Tuple[int, ...]) -> Set[Tuple[int, int]]:
    """數字牌（1-9）所有可能拆法的 (面子數, 搭子數)，完整枚舉"""
    i = next((k for k, c in enumerate(counts) if c > 0), None)
    if i is None:
        return {(0, 0)}
    c = list(counts)
    results = set()

    def sub(removals, dm, dt):
        for k in removals:
            c[k] -= 1
        for m, t in _suit_options(tuple(c)):
            results.add((m + dm, t + dt))
        for k in removals:
            c[k] += 1

    # 當孤張丟掉
    sub([i], 0, 0)
    # 刻子
    if c[i] >= 3:
        sub([i, i, i], 1, 0)
    # 順子
    if i + 2 < 9 and c[i + 1] > 0 and c[i + 2] > 0:
        sub([i, i + 1, i + 2], 1, 0)
    # 對子（當搭子）
    if c[i] >= 2:
        sub([i, i], 0, 1)
    # 兩面/邊張搭子
    if i + 1 < 9 and c[i + 1] > 0:
        sub([i, i + 1], 0, 1)
    # 嵌張搭子
    if i + 2 < 9 and c[i + 2] > 0:
        sub([i, i + 2], 0, 1)
    return _prune_options(results)


@lru_cache(maxsize=None)
def _honor_options(counts: Tuple[int, ...]) -> Set[Tuple[int, int]]:
    """字牌只能組刻子或對子"""
    options = {(0, 0)}
    for c in counts:
        tile_opts = {(0, 0)}
        if c >= 3:
            tile_opts.add((1, 0))
        if c >= 2:
            tile_opts.add((0, 1))
        options = _merge_options(options, tile_opts)
    return options


def calculate_max_melds(hand: List[str]) -> int:
    """計算手牌中最多可以形成的面子數量的便捷函式
    
    Args:
        hand: 手牌列表，每個元素是牌字符串，例如 ["1m", "2m", "east"]
        
    Returns:
        int: 最多可以形成的面子數量
    """
    calculator = ShantenCalculator()
    return calculator.calculate_max_melds(hand)

def find_tatsu(hand: List[str]) -> List[Tuple[str, str, str]]:
    """尋找手牌中的所有搭子的便捷函式
    
    Args:
        hand: 手牌列表，可以是任意數量的牌，每個元素是牌字符串
        
    Returns:
        List[Tuple[str, str, str]]: 搭子列表，每個元素是一個元組，包含兩張牌和搭子類型
    """
    calculator = ShantenCalculator()
    return calculator.find_tatsu(hand)

def count_tatsu(hand: List[str]) -> Dict[str, int]:
    """計算手牌中各類型搭子的數量的便捷函式
    
    Args:
        hand: 手牌列表，可以是任意數量的牌，每個元素是牌字符串
        
    Returns:
        Dict[str, int]: 各類型搭子的數量
    """
    calculator = ShantenCalculator()
    return calculator.count_tatsu(hand)

def find_max_tatsu(hand: List[str]) -> List[Tuple[str, str, str]]:
    """尋找手牌中的搭子，優先順序為：順子搭子 > 對子。

    Args:
        hand: 手牌列表，每個元素是牌字符串

    Returns:
        包含搭子的列表，每個搭子表示為 (牌1, 牌2, 類型)
    """
    calculator = ShantenCalculator()
    return calculator.find_max_tatsu(hand)

def find_pairs(hand: List[str]) -> List[Tuple[str, str]]:
    """尋找手牌中所有的對子

    Args:
        hand: 手牌列表，每個元素是牌字符串

    Returns:
        包含對子的列表，每個對子表示為 (牌1, 牌2)
    """
    calculator = ShantenCalculator()
    return calculator.find_pairs(hand)

def calculate_shanten(hand: List[str]) -> int:
    """計算手牌的進聴數的便捷函式
    
    Args:
        hand: 16張手牌，每個元素是牌字符串，例如 ["1m", "2m", "east", ...]
        
    Returns:
        int: 進聴數
    """
    calculator = ShantenCalculator()
    return calculator.calculate_shanten(hand)

def suggest_discard(hand_17: List[str]) -> Dict[str, Any]:
    """建議17張牌中應該打哪一張的便捷函式
    
    Args:
        hand_17: 17張牌的列表（16張手牌 + 1張摸到的牌），每個元素是牌字符串
        
    Returns:
        Dict[str, any]: 建議結果，包含：
            - 'tile': 建議打掉的牌
            - 'shanten_after': 打掉該牌後的進聽數
            - 'all_options': 所有可能的打牌選項列表
            - 'best_options': 所有最佳選項列表
            - 'reason': 建議原因
    """
    calculator = ShantenCalculator()
    return calculator.suggest_discard(hand_17)

def visualize_hand(hand: List[str], use_chinese: bool = True) -> str:
    """視覺化手牌的便捷函式
    
    將手牌轉換為格式化的字符串，方便顯示。
    在 command line 使用中文顯示，在 OpenCV 視窗中使用英文格式。
    
    Args:
        hand: 手牌列表，每個元素是牌字符串，例如 ["1m", "2m", "east"]
        use_chinese: 是否使用中文顯示
            - True: 用於 command line，顯示為 "萬: 一,二,三 | 筒: 四,五 | 字: 東,南"
            - False: 用於 OpenCV，顯示為 "wan: 1m,2m,3m | tong: 4p,5p | feng: east,south"
        
    Returns:
        str: 格式化的手牌字符串
        
    Examples:
        >>> visualize_hand(["1m", "2m", "3m", "1p", "2p", "east", "south"])
        '萬: 一,二,三 | 筒: 一,二 | 風: 東,南'
        
        >>> visualize_hand(["1m", "2m", "3m", "1p", "2p", "east", "south"], use_chinese=False)
        'wan: 1m,2m,3m | tong: 1p,2p | feng: east,south'
    """
    calculator = ShantenCalculator()
    return calculator.visualize_hand(hand, use_chinese)

def tile_to_chinese(tile: str) -> str:
    """將單張牌轉換為中文顯示格式的便捷函式
    
    Args:
        tile: 牌字符串，例如 "1m", "2p", "east"
        
    Returns:
        str: 中文格式，例如 "一萬", "二筒", "東"
        
    Examples:
        >>> tile_to_chinese("1m")
        '一萬'
        >>> tile_to_chinese("east")
        '東'
    """
    calculator = ShantenCalculator()
    return calculator._tile_to_chinese(tile) 