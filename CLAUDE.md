# Project Context: Taiwanese Mahjong AI & UI Automation Sandbox

- **Purpose**: Academic research on 16-tile Mahjong game-tree search / heuristics and E2E UI automation testing framework.

- **Architecture**: Decoupled design (advisory only, no input automation):
  - `mahjong_engine/` — pure logic (`shanten.py`: shanten / discard / claim suggestions)
  - `vision_observer/` — screen state parser (window capture; hand, table/river, meld and claim-button recognizers)
  - `advisor.py` — combines recognizer output with the engine into advice (`analyze_frame`); `main_preview.py` is the live preview entry point
  - Templates: `samples/` (hand), `samples_river/` (river), `samples_meld/` (own melds), `samples_ui/` (buttons)
  - `tests/` (pytest, fixtures cropped from recordings in `tests/fixtures/`), `scripts/` (manual tools, run with `python -m scripts.<name>`)

- **Constraints**: Do not include any memory reading, packet injection, or reverse-engineering logic. All interactions must be strictly black-box UI level.