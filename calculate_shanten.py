from typing import List, Dict, Tuple, Set
from collections import defaultdict

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
    
    def _is_numeric_tile(self, tile: str) -> bool:
        """判斷是否為數字牌"""
        if len(tile) >= 2:
            return tile[1] in ['m', 'p', 's']
        return False
    
    def _is_word_tile(self, tile: str) -> bool:
        """判斷是否為字牌"""
        word_tiles = ['east', 'south', 'west', 'north', 'middle', 'fa', 'white']
        return tile in word_tiles
    
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
        """計算手牌的進聴數
        
        進聴數是指距離和牌還需要換幾張牌。
        計算方法：
        1. 先找出手牌中最大的面子數量
        2. 將這些面子從手牌中移除
        3. 在剩餘的牌中找出最多的搭子組合
        4. 將這些搭子從手牌中移除
        5. 剩下的是單張
        
        台灣麻將規則：
        - 基本手牌為 16 張
        - 必須湊齊五組牌加一對眼（四個面子 + 一個對子 + 一個搭子）
        
        進聴數計算公式：
        - 需要的面子數 = 4 - 已有面子數
        - 如果搭子數量 >= 需要的面子數，則需要進 需要的面子數 張牌
        - 如果搭子數量 < 需要的面子數，則需要先形成搭子，再升級為面子
        - 需要的對子數 = 1 - 已有對子數（最多為1）
        - 進聴數 = 需要進的牌數 + 需要的對子數
        
        Args:
            hand: 手牌列表，應該是16張牌，每個元素是牌字符串，例如 ["1m", "2m", "east"]
            
        Returns:
            int: 進聴數
        """
        if len(hand) != 16:
            raise ValueError(f"手牌必須是16張，目前有 {len(hand)} 張。計算進聴數需要固定的手牌數量。")
        
        # 複製手牌，避免修改原始手牌
        remaining_tiles = hand.copy()

        # 0. 先找出所有對子
        pairs = self.find_pairs(remaining_tiles)
        if len(pairs) != 0: # 如果手牌中有對子，則先處理對子
            tmp_shanten_list = []
            for pair in pairs:
                # 複製手牌，避免修改原始手牌
                tmp_remaining_tiles = remaining_tiles.copy()
                # print(f"移除對子: {pair[0]}, {pair[1]}")
                tmp_remaining_tiles.remove(pair[0])
                tmp_remaining_tiles.remove(pair[1])
                # print(f"移除對子後剩餘牌: {tmp_remaining_tiles}")

                # 1. 找出最大面子數量
                max_melds = self.calculate_max_melds(tmp_remaining_tiles)
                
                # 2. 將這些面子從手牌中移除
                # 由於 calculate_max_melds 不會返回具體的面子，我們需要重新計算
                grouped_tiles = self._group_tiles(tmp_remaining_tiles)
                remaining_grouped = self._remove_max_melds(grouped_tiles)
                
                # 將分組後的牌轉換回列表
                tiles_before_melds_removal = tmp_remaining_tiles.copy()
                tmp_remaining_tiles = self._grouped_to_list(remaining_grouped)
                # print(f"移除面子後剩餘牌: {tmp_remaining_tiles}")
                # print(f"移除的面子: {[t for t in tiles_before_melds_removal if t not in tmp_remaining_tiles]}")
                
                # 3. 在剩餘的牌中找出最多的搭子組合
                max_tatsu_list = self.find_max_tatsu(tmp_remaining_tiles)
                
                # 4. 將這些搭子從手牌中移除
                tiles_before_tatsu_removal = tmp_remaining_tiles.copy()
                for t1, t2, tatsu_type in max_tatsu_list:
                    # print(f"移除搭子: {t1}, {t2} (類型: {tatsu_type})")
                    if t1 in tmp_remaining_tiles:
                        tmp_remaining_tiles.remove(t1)
                    if t2 in tmp_remaining_tiles:
                        tmp_remaining_tiles.remove(t2)
                # print(f"移除搭子後剩餘牌: {tmp_remaining_tiles}")
                
                # 5. 剩下的是單張
                singles = len(tmp_remaining_tiles)
                
                # 計算進聴數
                has_pair = True
                
                # 搭子數量
                tatsu_count = len(max_tatsu_list)
                
                # 需要的面子數
                needed_melds = 4 - max_melds

                # print("needed_melds: ", needed_melds)
                # print("tatsu_count: ", tatsu_count)
                # print("has_pair: ", has_pair)
                # print("---------------------------------")

                # 計算進聴數
                if needed_melds == 0:
                    # 已經有4個面子，一個對子，確認一下搭子數量
                    if has_pair and tatsu_count == 1:
                        shanten = 0
                        tmp_shanten_list.append(shanten)
                    else:
                        shanten = 1
                        tmp_shanten_list.append(shanten)
                else:
                    # 需要進的牌數
                    if tatsu_count >= needed_melds:
                        # 搭子數量足夠，每個搭子需要進一張牌
                        tiles_needed = needed_melds
                        tatsu_left_count = tatsu_count - needed_melds
                    else:
                        # 搭子數量不足，需要先形成搭子，再升級為面子
                        tiles_needed = tatsu_count + (needed_melds - tatsu_count) * 2
                        tatsu_left_count = 0

                    # 接著處理搭子及對子
                    if tatsu_left_count == 1:
                        needed_tatsu = 0
                    else:
                        needed_tatsu = 1
                    
                    # 進聴數
                    shanten = tiles_needed + needed_tatsu
                    tmp_shanten_list.append(shanten)
            
            # print("tmp_shanten_list: ", tmp_shanten_list)
            shanten = min(tmp_shanten_list)

        else: # 如果手牌中沒有對子，則先找出最大面子數量
            # 1. 找出最大面子數量
            max_melds = self.calculate_max_melds(remaining_tiles)
            
            # 2. 將這些面子從手牌中移除
            # 由於 calculate_max_melds 不會返回具體的面子，我們需要重新計算
            grouped_tiles = self._group_tiles(remaining_tiles)
            remaining_grouped = self._remove_max_melds(grouped_tiles)
            
            # 將分組後的牌轉換回列表
            tiles_before_melds_removal = remaining_tiles.copy()
            remaining_tiles = self._grouped_to_list(remaining_grouped)
            # print(f"沒有對子，直接移除面子後剩餘牌: {remaining_tiles}")
            # print(f"移除的面子: {[t for t in tiles_before_melds_removal if t not in remaining_tiles]}")
            
            # 3. 在剩餘的牌中找出最多的搭子組合
            max_tatsu_list = self.find_max_tatsu(remaining_tiles)
            
            # 4. 將這些搭子從手牌中移除
            tiles_before_tatsu_removal = remaining_tiles.copy()
            for t1, t2, tatsu_type in max_tatsu_list:
                # print(f"移除搭子: {t1}, {t2} (類型: {tatsu_type})")
                if t1 in remaining_tiles:
                    remaining_tiles.remove(t1)
                if t2 in remaining_tiles:
                    remaining_tiles.remove(t2)
            # print(f"移除搭子後剩餘牌: {remaining_tiles}")
            
            # 5. 剩下的是單張
            singles = len(remaining_tiles)
            
            # 計算進聴數
            # 檢查是否有對子
            has_pair = False
            
            # 搭子數量
            tatsu_count = len(max_tatsu_list)
            
            # 需要的面子數
            needed_melds = 4 - max_melds

            # 計算進聴數
            if needed_melds == 0:
                # 已經有4個面子，只需要一個對子
                if has_pair and tatsu_count == 2:
                    shanten = 0
                else:
                    shanten = 1
            else:
                # 需要進的牌數
                if tatsu_count >= needed_melds:
                    # 搭子數量足夠，每個搭子需要進一張牌
                    tiles_needed = needed_melds
                    tatsu_left_count = tatsu_count - needed_melds
                else:
                    # 搭子數量不足，需要先形成搭子，再升級為面子
                    tiles_needed = tatsu_count + (needed_melds - tatsu_count) * 2
                    tatsu_left_count = 0

                # 接著處理搭子及對子
                if tatsu_left_count == 2 and has_pair:
                    needed_tatsu = 0
                elif tatsu_left_count == 2 and not has_pair:
                    needed_tatsu = 1
                elif tatsu_left_count == 1:
                    needed_tatsu = 1
                else:
                    needed_tatsu = 2
                
                # 進聴數
                shanten = tiles_needed + needed_tatsu
        
        # 特殊情況：如果已經有5個面子，則為聽牌（0進聴）
        if max_melds == 5:
            shanten = 0
        
        return shanten
    
    def _remove_max_melds(self, grouped_tiles: Dict[str, Dict[int, int]]) -> Dict[str, Dict[int, int]]:
        """從分組後的牌中移除最大數量的面子
        
        Args:
            grouped_tiles: 分組後的牌，格式為 {"wan": {1: 2, 2: 1}, ...}
            
        Returns:
            Dict[str, Dict[int, int]]: 移除面子後剩餘的牌
        """
        # 複製分組後的牌，避免修改原始數據
        remaining = {}
        for tile_type, numbers in grouped_tiles.items():
            remaining[tile_type] = numbers.copy()
        
        # 嘗試兩種計算方式，取最大值
        remaining1 = self._remove_melds(remaining.copy(), True)
        remaining2 = self._remove_melds(remaining.copy(), False)
        
        # 計算兩種方式移除後剩餘的牌數
        count1 = sum(sum(numbers.values()) for numbers in remaining1.values())
        count2 = sum(sum(numbers.values()) for numbers in remaining2.values())
        
        # 返回剩餘牌數較少的結果（即移除面子數較多的結果）
        return remaining1 if count1 <= count2 else remaining2
    
    def _remove_melds(self, grouped_tiles: Dict[str, Dict[int, int]], prioritize_triplets: bool = True) -> Dict[str, Dict[int, int]]:
        """從分組後的牌中移除面子
        
        Args:
            grouped_tiles: 分組後的牌，格式為 {"wan": {1: 2, 2: 1}, ...}
            prioritize_triplets: 是否優先考慮刻子，如果為False則優先考慮順子
            
        Returns:
            Dict[str, Dict[int, int]]: 移除面子後剩餘的牌
        """
        # 處理數字牌
        for tile_type in ['wan', 'tong', 'suo']:
            if tile_type not in grouped_tiles:
                continue
                
            numbers = grouped_tiles[tile_type]
            
            # 根據優先級處理面子
            if prioritize_triplets:
                # 先找刻子
                for num, count in list(numbers.items()):
                    if count >= 3:
                        numbers[num] -= 3
                        if numbers[num] == 0:
                            del numbers[num]
                
                # 再找順子
                while True:
                    found_straight = False
                    for num in range(1, 8):
                        if (numbers.get(num, 0) > 0 and 
                            numbers.get(num + 1, 0) > 0 and 
                            numbers.get(num + 2, 0) > 0):
                            numbers[num] -= 1
                            if numbers[num] == 0:
                                del numbers[num]
                            numbers[num + 1] -= 1
                            if numbers[num + 1] == 0:
                                del numbers[num + 1]
                            numbers[num + 2] -= 1
                            if numbers[num + 2] == 0:
                                del numbers[num + 2]
                            found_straight = True
                            break  # 找到一個就中斷，再繼續找下一個
                    if not found_straight:
                        break
            else:
                # 先找順子
                while True:
                    found_straight = False
                    for num in range(1, 8):
                        if (numbers.get(num, 0) > 0 and 
                            numbers.get(num + 1, 0) > 0 and 
                            numbers.get(num + 2, 0) > 0):
                            numbers[num] -= 1
                            if numbers[num] == 0:
                                del numbers[num]
                            numbers[num + 1] -= 1
                            if numbers[num + 1] == 0:
                                del numbers[num + 1]
                            numbers[num + 2] -= 1
                            if numbers[num + 2] == 0:
                                del numbers[num + 2]
                            found_straight = True
                            break  # 找到一個就中斷，再繼續找下一個
                    if not found_straight:
                        break
                
                # 再找刻子
                for num, count in list(numbers.items()):
                    if count >= 3:
                        numbers[num] -= 3
                        if numbers[num] == 0:
                            del numbers[num]
        
        # 處理字牌（風牌和三元牌）
        for tile_type in ['feng', 'sanyuan']:
            if tile_type not in grouped_tiles:
                continue
                
            numbers = grouped_tiles[tile_type]
            
            # 字牌只能形成刻子
            for num, count in list(numbers.items()):
                if count >= 3:
                    numbers[num] -= 3
                    if numbers[num] == 0:
                        del numbers[num]
        
        return grouped_tiles
    
    def _grouped_to_list(self, grouped_tiles: Dict[str, Dict[int, int]]) -> List[str]:
        """將分組後的牌轉換回列表
        
        Args:
            grouped_tiles: 分組後的牌，格式為 {"wan": {1: 2, 2: 1}, ...}
            
        Returns:
            List[str]: 牌列表，每個元素是牌字符串
        """
        tiles = []
        for tile_type, numbers in grouped_tiles.items():
            for num, count in numbers.items():
                for _ in range(count):
                    tiles.append(self._tile_to_string(tile_type, num))
        return tiles

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