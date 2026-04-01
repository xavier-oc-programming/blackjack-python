# Blackjack

Day 11 project from [100 Days of Code – The Complete Python Pro Bootcamp](https://www.udemy.com/course/100-days-of-code/).

Two versions of the same game: a procedural solution close to the course brief, and a full rebuild with OOP, a chip system, animated terminal UI, and casino-style side bets.

---

## Table of Contents

- [Versions](#versions)
- [Requirements](#requirements)
- [How to Run](#how-to-run)
- [Project Structure](#project-structure)
- [Original Version](#original-version)
- [Advanced Version](#advanced-version)
  - [Menu](#menu)
  - [Difficulty Modes](#difficulty-modes)
  - [Chip System](#chip-system)
  - [Gameplay Actions](#gameplay-actions)
  - [Insurance](#insurance)
  - [Split](#split)
  - [Double Down](#double-down)
  - [Dealer Behaviour](#dealer-behaviour)
  - [Statistics Screen](#statistics-screen)
  - [Terminal UI & Animations](#terminal-ui--animations)
- [House Rules](#house-rules)
- [Architecture (Advanced)](#architecture-advanced)
- [Key Design Decisions](#key-design-decisions)

---

## Versions

| Version | Description |
|---------|-------------|
| `original/` | Procedural, single-file, close to the course solution |
| `advanced/` | Full OOP rebuild — modular architecture, chip system, animated terminal UX, side bets |

---

## Requirements

- Python 3.10 or higher
- No third-party dependencies — standard library only (`os`, `sys`, `random`, `time`, `tty`, `termios`, `dataclasses`, `enum`, `typing`)

---

## How to Run

```bash
# Version selector (recommended entry point)
python menu.py

# Run a specific version directly
python original/main.py
python advanced/main.py
```

`menu.py` is a root-level version selector that launches the chosen version as a subprocess, keeping each version's imports isolated.

---

## Project Structure

```
.
├── menu.py              # version selector — launches original or advanced
├── art.py               # shared ASCII logo (imported by menu and advanced)
├── requirements.txt
├── docs/
│   └── COURSE_NOTES.md  # original course brief and hints
├── original/
│   ├── main.py          # all game logic in one file (~75 lines)
│   └── art.py           # ASCII logo (local copy for standalone run)
└── advanced/
    ├── main.py          # orchestration layer — round loop, split/double/insurance flow
    ├── blackjack.py     # pure game logic — no UI, no side effects
    ├── display.py       # all terminal output, input prompts, and animations
    └── config.py        # all constants in one place
```

---

## Original Version

Located in `original/`. A clean, minimal implementation that follows the course solution closely.

**What it does:**
- Deals 2 cards to the player and dealer from an infinite deck
- Player chooses to hit or stand each turn
- Dealer draws automatically until reaching score ≥ 17
- Ace is automatically converted from 11 to 1 if the hand would bust
- Blackjack is detected as a 2-card hand totalling 21
- Result is printed as a plain-text string with emoji
- Player can restart without relaunching the script

**Functions:**
| Function | Description |
|----------|-------------|
| `deal_card()` | Returns a random card value from `[11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]` |
| `calculate_score(cards)` | Sums the hand; returns `0` as a blackjack sentinel; demotes Ace from 11 → 1 if bust |
| `compare(u_score, c_score)` | Evaluates both scores and returns a result string |
| `play_game()` | Full game loop — deal, player turn, dealer turn, compare |

---

## Advanced Version

Located in `advanced/`. A complete rebuild that goes well beyond the course brief.

### Menu

On launch, the advanced version presents a main menu with three options:

```
[1]  Play Blackjack
[2]  Rules
[3]  Statistics
[↑]  Quit
```

Navigation uses single-keypress input (no Enter required). The up-arrow key exits the current screen and returns to the menu.

### Difficulty Modes

Selected once per session before the first round. Affects two things: dealer threshold and hole-card visibility.

| Mode | Dealer Stands At | Dealer's Hole Card |
|------|------------------|--------------------|
| Easy | 17 | Always visible (full hand shown) |
| Normal | 17 | Hidden until dealer's turn |
| Hard | 18 | Hidden until dealer's turn |

In Easy mode the dealer's second card is never hidden, making it straightforward to decide when to hit or stand.

### Chip System

- Player starts each session with **500 chips**
- Minimum bet per round is **5 chips**
- Bet is entered via typed input at the start of each round
- Bet is pre-deducted from the chip balance immediately; winnings are returned at round end
- Session ends automatically when the player's balance falls below the minimum bet
- Profit/loss is displayed on the statistics screen relative to the 500-chip starting balance

**Payouts (after bet pre-deduction):**

| Outcome | Chips returned |
|---------|---------------|
| Win / Dealer bust | `bet × 2` (net +bet) |
| Blackjack win | `bet × 2` (net +bet) |
| Draw | `bet` returned (net 0) |
| Loss / Bust / Blackjack lose | `0` (net -bet) |

### Gameplay Actions

On each turn the player chooses via single keypress:

| Key | Action | When Available |
|-----|--------|---------------|
| `H` | Hit — draw one card | Any turn |
| `S` | Stay — end player turn | Any turn |
| `D` | Double Down | First action only, if chips allow |
| `P` | Split | First action only, if cards match and chips allow |
| `Q` | Forfeit — lose the bet and end the round | Any turn |

### Insurance

Offered automatically when the dealer's first visible card is an Ace.

- Player can bet **0 up to half their original bet**
- Entering `0` declines insurance
- If the dealer has Blackjack: insurance pays **2:1** (bet × 3 returned, net +bet×2)
- If the dealer does not have Blackjack: insurance bet is lost

Insurance is resolved before the player's turn begins if either side has Blackjack; otherwise the player's turn proceeds as normal.

### Split

Available on the first action when the player's two cards are equal in value.

- Requires enough chips to match the original bet (one extra bet is deducted)
- The two cards are split into two separate hands; each receives one new card immediately
- Each hand is played independently in sequence (`Hand 1 of 2`, then `Hand 2 of 2`)
- Each split hand supports Hit, Stay, Double Down (no further splits)
- The dealer plays one turn against both hands after both are resolved
- If both split hands bust, the dealer does not play
- Results and chip deltas are displayed separately for each hand

### Double Down

Available on the first action only.

- Requires enough chips to match the original bet (original bet is deducted again, total bet doubles)
- The player receives exactly one card, then stands automatically
- The dealer then reveals and plays their turn as normal

### Dealer Behaviour

After the player's turn ends (or on an immediate Blackjack):

1. The hole card (index 1) is revealed with a flip animation
2. The dealer draws cards one by one, each with a deal animation, until reaching the difficulty threshold (17 on Normal/Easy, 18 on Hard)
3. If the dealer already has Blackjack, they do not draw additional cards

On Easy difficulty the hole card is never hidden, so there is no reveal animation.

### Statistics Screen

Accessible from the main menu. Tracks the entire session:

| Stat | Description |
|------|-------------|
| Difficulty | Mode selected at session start |
| Rounds played | Number of complete rounds (including splits counted as one round) |
| Hands played | Total individual hands resolved (wins + losses + draws) |
| Wins | Hands won (including dealer busts) |
| Losses | Hands lost (including busts and blackjack losses) |
| Draws | Tied hands |
| Blackjacks | Hands won with a natural Blackjack |
| Busts | Hands lost by going over 21 |
| Win rate | `wins / hands_played × 100`, shown to 1 decimal place |
| Longest win streak | Most consecutive wins in the session |
| Final chips | Current chip balance |
| Profit / Loss | Difference from starting 500 chips, shown in green/red |

If no session has been played yet, the screen shows a placeholder message.

### Terminal UI & Animations

The entire interface runs in a raw terminal. No third-party UI libraries are used.

**Card rendering** — each card is drawn as a 9-wide × 7-tall ASCII box:

```
┌───────┐
│A      │
│       │
│   ♥   │
│       │
│      A│
└───────┘
```

Red suits (♥ ♦) are rendered in red; black suits (♠ ♣) in white. Face-down cards use a cyan `▓` fill.

**Deal animation** — when a card is dealt, a side-panel flip plays without clearing the board:
- Face-down full width → narrowing back → thin edge → face-up card
- Uses ANSI cursor-up escape codes to overwrite lines in place

**STAND / BUSTED / ROUND OVER** — big 5-line ASCII block-letter announcements rendered from a custom glyph font. STAND and BUSTED pulse once (bright → dim → bright) before holding.

**Dealer reveal sequence** — after the player stands:
1. Board redraws with hole card still hidden
2. `Dealer reveals hole card...` message with 0.5s pause
3. Flip animation for the hole card
4. Each dealer hit plays a full deal animation with a pause between cards
5. `DEALER STANDS` message holds for 5 seconds before the round-over screen

**Typewriter effect** — the logo on first launch is printed character-by-character with a 4ms delay.

**Single-keypress input** — all navigation (hit/stay/difficulty/menu) is captured via `tty`/`termios` raw mode. No Enter key required. The up-arrow escape sequence (`\x1b[A`) is detected and returned as the string `"UP"`.

---

## House Rules

- **Deck:** 4-deck shoe — `[11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10] × 4 suits × 4 decks`
- **Reshuffle:** automatically when fewer than 20 cards remain in the shoe
- **Ace:** counts as 11; automatically demoted to 1 if the hand would bust
- **J / Q / K:** all count as 10 (randomly labelled when drawn)
- **Blackjack:** Ace + any 10-value card on the first deal (2 cards only)
- **Dealer threshold:** stands at 17 (Normal/Easy) or 18 (Hard)
- **Bust:** any hand over 21 is an immediate loss
- **Tie:** same score = draw, bet returned

*(The `original/` version uses an infinite deck with no shoe.)*

---

## Architecture (Advanced)

The advanced version enforces a strict separation of concerns across four files:

**`config.py`** — all magic numbers in one place. Nothing is hardcoded elsewhere.

```python
DECK            = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]
STARTING_CHIPS  = 500
MIN_BET         = 5
DECK_COUNT      = 4
RESHUFFLE_THRESHOLD = 20
DEALER_HIT_THRESHOLD_NORMAL = 17
DEALER_HIT_THRESHOLD_HARD   = 18
BLACKJACK_SENTINEL          = 0
```

**`blackjack.py`** — pure game logic with no I/O, no `print`, no `input`. Contains:
- `GameResult` enum — `WIN`, `LOSE`, `DRAW`, `BLACKJACK_WIN`, `BLACKJACK_LOSE`, `BUST`, `DEALER_BUST`
- `Difficulty` enum — `EASY`, `NORMAL`, `HARD` with `dealer_threshold` and `show_dealer_hand` properties
- `Shoe` dataclass — finite deck that reshuffles automatically
- `Hand` dataclass — holds cards, suits, labels; exposes `score`, `is_blackjack`, `is_bust`
- `calculate_score(cards)` — pure function; handles Ace demotion and blackjack sentinel
- `compare(player, dealer)` — returns a `GameResult`
- `chip_delta(result, bet)` — returns chips to return to player after a pre-deducted bet
- `GameSession` dataclass — tracks chips, shoe, difficulty, and all stat counters

**`display.py`** — all terminal output, input, and animations. Imports from `blackjack` for type hints only. Contains:
- ANSI colour constants
- Card rendering (`_card_rows`, `_render_cards`)
- Avatar rendering (dealer and player ASCII characters)
- All `prompt_*` functions
- `show_game_state` — full-screen table view
- `show_stats` — statistics screen
- All animation functions (`animate_deal`, `animate_stand`, `animate_bust`, `animate_round_over`)
- Custom ASCII block-letter glyph font (`_ASCII_FONT`, `_render_big_text`)

**`main.py`** — orchestration only. Calls `display.*` for input/output, calls `blackjack.*` for logic. Contains:
- `play_round(session)` — one full round including bet, deal, insurance, player turn, dealer turn, result
- `_play_split_hand(hand, ...)` — plays a single split hand interactively
- `_animate_dealer_reveal(...)` — sequences the dealer reveal animations
- `_resolve_hand(session, result, bet)` — applies chip delta and records result
- `game_loop()` — session loop, calls `play_round` until exit or out of chips
- `rules_screen()`, `stats_screen()` — wrapper screens
- `MODES` registry — maps keypress → (label, callable) for the main menu

---

## Key Design Decisions

**Blackjack sentinel value** — `calculate_score` returns `0` (not `21`) for a natural Blackjack. This avoids ambiguity in `compare`: a score of `0` can only mean Blackjack, never a valid hand total. The sentinel is named `BLACKJACK_SENTINEL` in config rather than a bare `0`.

**Bet pre-deduction** — the bet is subtracted from chips immediately when placed, before any cards are dealt. `chip_delta` returns the number of chips to *add back*, not a net change. This simplifies accounting for split hands (two separate bets, two separate deltas).

**Shoe over infinite deck** — the original course uses an infinite deck (sampling with replacement from a fixed list). The advanced version uses a finite 4-deck shoe that reshuffles when low, which more closely models real casino play and gives the `Shoe.remaining` counter a meaningful value to display in the UI.

**`Hand` stores labels and suits separately from card values** — card values drive all game logic; labels (A, 2–9, 10, J, Q, K) and suits are cosmetic and stored separately for rendering. A 10-value card is randomly labelled as `10`, `J`, `Q`, or `K` on draw, matching real card distribution visually without affecting score.

**Raw terminal input** — `tty`/`termios` raw mode is used so that single-keypress navigation works without pressing Enter. The escape sequence `\x1b[A` (up-arrow) is used as a universal "back/quit" signal throughout the UI.
