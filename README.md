# Blackjack

Day 11 project from [100 Days of Code – The Complete Python Pro Bootcamp](https://www.udemy.com/course/100-days-of-code/).

## Versions

| Version | Description |
|---------|-------------|
| `original/` | Procedural, close to the course solution |
| `advanced/` | Rebuilt with OOP, dataclasses, modular architecture, and full terminal UX |

## Run

```bash
python menu.py           # version selector
python original/main.py  # run original directly
python advanced/main.py  # run advanced directly
```

## Structure

```
.
├── menu.py              # version selector (subprocess launcher)
├── requirements.txt
├── docs/
│   └── COURSE_NOTES.md  # original course brief
├── original/
│   ├── main.py          # all logic in one file
│   └── art.py           # ASCII logo
└── advanced/
    ├── main.py          # orchestration — input → logic → display
    ├── blackjack.py     # pure game logic, no UI
    ├── display.py       # all terminal output and input
    └── config.py        # constants
```

## Advanced Features

The `advanced/` version goes well beyond the course brief:

- **Chip system** — start with 500 chips, min bet 5; session ends when chips run out
- **Difficulty modes** — Easy (dealer's full hand always visible), Normal (dealer stands at 17), Hard (dealer stands at 18)
- **4-deck shoe** — reshuffled automatically when fewer than 20 cards remain
- **Double down** — first action only; doubles bet, deals one card, then stand
- **Split** — when first two cards match; each hand played separately, dealer plays once
- **Insurance** — offered when dealer shows an Ace; pays 2:1 if dealer has Blackjack
- **Statistics screen** — tracks wins, losses, draws, blackjacks, busts, win rate, and longest win streak
- **Rules screen** — in-game reference for all house rules
- **Animated dealer reveal** — hole card flip and hit/stand decisions play out with timing

## House Rules

- 4-deck shoe, reshuffled when < 20 cards remain
- Ace = 11 or 1 · J/Q/K = 10 · No jokers
- Blackjack = Ace + 10-value card on first deal only (2 cards)
- Dealer stands at 17 (Normal) or 18 (Hard)
- Bust (over 21) = loss · Ties are a draw
