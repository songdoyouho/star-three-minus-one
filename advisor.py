"""把畫面辨識的結果交給引擎計算，產生要顯示在畫面上的建議文字與標記"""
from mahjong_engine.shanten import (suggest_discard, calculate_shanten, safest_discards, suggest_claim,
                                    suggest_self_kan, is_winning)


def _claim_advice(hand, tile, buttons, visible):
    """別人打出 tile、出現吃碰按鈕時的建議，回傳 (顯示文字, 建議按的按鈕)"""
    s = suggest_claim(hand, tile, 'chi' in buttons, visible, allowed=buttons)  # 只考慮亮著的按鈕
    best = s['best']
    print(f"別人打 {tile}，手牌 {' '.join(hand)} → {s['reason']}")
    if s['action'] == 'win':
        return f"Claim: HU! Win on {tile}", 'hu'
    if s['action'] == 'pass':
        return f"Claim: PASS on {tile} (shanten stays {best['shanten']})", 'cancel'
    text = f"Claim: {s['action'].upper()} {' '.join(best['meld'])}"
    if best['discard']:
        text += f", then discard {best['discard']}"
    return text + f" | Shanten {s['options'][0]['shanten']} -> {best['shanten']}", s['action']

def analyze_frame(frame, recognizer, cache, table=None, claim=None, meld=None):
    """辨識手牌（和桌上看得到的牌）並計算建議；都沒變就沿用上次的計算結果

    Args:
        table: TableRecognizer，給的話會辨識牌河，扣掉已出現的牌並給防守提示
        claim: ClaimRecognizer，給的話出現吃碰槓胡按鈕時會建議要按哪個
        meld: MeldRecognizer，給的話會辨識自己吃碰的牌（算進看得到的牌、判斷加槓）
    Returns:
        (detections, info_lines)
    """
    res = recognizer.recognize(frame)
    hand, drawn = res['hand'], res['drawn']
    lines = []
    if not hand:
        cache.clear()
        return res['detections'], lines

    # 吃碰槓胡按鈕和放大顯示的那張打出的牌
    claim_info = claim.recognize(frame) if claim is not None else None

    # 自己吃碰槓的牌（在第一張手牌左邊）
    visible, meld_dets, pons, meld_info = [], [], [], None
    if meld is not None:
        meld_info = meld.recognize(frame, min(d['x'] for d in res['detections']))
        visible += [t for t in meld_info['tiles'] if t != '?']
        pons = [g[0] for g in meld_info['melds'] if len(g) == 3 and len(set(g)) == 1 and g[0] != '?']
        meld_dets = meld_info['detections']
        for d in meld_dets:
            d['table'] = True

    # 桌上的牌（自己的手牌、吃碰的牌、放大的那張牌不掃，避免重複算到）
    table_dets = []
    if table is not None:
        exclude = [(d['x'], d['y'], d['w'], d['h']) for d in res['detections']]
        if claim_info and claim_info['tile_box']:
            exclude.append(claim_info['tile_box'])
        if meld_info:
            exclude.append(meld_info['area'])
        t = table.recognize(frame, exclude)
        visible += t['tiles']
        table_dets = t['detections']
        for d in table_dets:
            d['table'] = True

    # 手牌完整（沒有認不出來的牌、張數正確）才重新計算
    full = hand + ([drawn] if drawn else [])
    key = (tuple(full), tuple(sorted(visible)), tuple(pons))
    if res['unknown'] == 0 and len(hand) % 3 == 1 and key != cache.get('key'):
        cache['key'] = key
        cache['tile'] = None
        cache['defense'] = None
        cache['tsumo'] = False
        cache['kan'] = None
        try:
            if drawn and is_winning(full):
                cache['text'] = f"TSUMO! You win with {drawn} (press HU)"
                cache['tsumo'] = True
                print(f"手牌 {' '.join(full)} → 自摸！")
            elif drawn:
                s = suggest_discard(full, visible)
                best = s['best_options'][0]
                if s['shanten_after'] == 0:
                    detail = f"Waits: {' '.join(best['wait_tiles'])} ({best['wait_count']} left)"
                else:
                    detail = f"Improving: {best['improving_count']} tiles"
                cache['text'] = f"Discard: {s['tile']} | Shanten after: {s['shanten_after']} | {detail}"
                cache['tile'] = s['tile']
                if table is not None:
                    safe = safest_discards(full, visible)
                    seen = dict(safe)
                    cache['defense'] = (f"Defense: safest {safe[0][0]} ({safe[0][1]} seen)"
                                        f" | {s['tile']} has {seen[s['tile']]} seen")
                print(f"手牌 {' '.join(full)} → 建議打 {s['tile']}：{s['reason']}")
                k = suggest_self_kan(full, pons, visible)
                if k['action'] == 'kan':
                    kind = 'concealed' if k['best']['type'] == 'concealed' else 'added'
                    cache['kan'] = f"KAN: {k['best']['tile']} ({kind}) | Shanten stays {k['best']['shanten']}"
                if k['options']:
                    print(f"  槓：{k['reason']}")
            else:
                cache['text'] = f"Shanten: {calculate_shanten(hand)}"
        except Exception as e:
            cache['text'] = None
            print(f"建議計算失敗: {e}")

    # 出現吃碰槓胡按鈕：建議要不要吃碰（輪到別人出牌時手上是 3k+1 張、沒有摸牌）
    button = None
    if claim_info and claim_info['tile'] and not drawn and res['unknown'] == 0 and len(hand) % 3 == 1:
        ckey = (tuple(hand), claim_info['tile'], tuple(claim_info['buttons']), tuple(sorted(visible)))
        if ckey != cache.get('claim_key'):
            cache['claim_key'] = ckey
            try:
                cache['claim'] = _claim_advice(hand, claim_info['tile'], claim_info['buttons'], visible)
            except Exception as e:
                cache['claim'] = None
                print(f"吃碰建議計算失敗: {e}")
        if cache.get('claim'):
            lines.append(cache['claim'][0])
            button = cache['claim'][1]
    elif claim_info and cache.get('tsumo'):
        button = 'hu'
    elif claim_info and cache.get('kan') and drawn:
        button = 'kan'
    button_dets = []
    if button:
        x, y, w, h = claim_info['button_boxes'][button]
        button_dets.append({'x': x, 'y': y, 'w': w, 'h': h, 'label': button.upper(), 'confidence': 1.0,
                            'suggested': True, 'action': button.upper()})

    # 建議放第一行，並在畫面上標出要打的那張牌
    if cache.get('kan') and drawn:
        lines.append(cache['kan'])
    if cache.get('text'):
        lines.append(cache['text'])
    if cache.get('defense'):
        lines.append(cache['defense'])
    if cache.get('tile'):
        target = next((d for d in res['detections'] if d['label'] == cache['tile']), None)
        if target:
            target['suggested'] = True
    lines.append(f"Hand ({len(hand)}): {' '.join(hand)}" + (f" | Drawn: {drawn}" if drawn else ""))
    if meld_info and meld_info['melds']:
        lines.append("Melds: " + " | ".join(' '.join(g) for g in meld_info['melds']))
    if table is not None:
        lines.append(f"Seen on table: {len(visible)} tiles")
    if res['unknown']:
        lines.append(f"Unrecognized: {res['unknown']} tile(s) (covered or dimmed)")
    return res['detections'] + meld_dets + table_dets + button_dets, lines
