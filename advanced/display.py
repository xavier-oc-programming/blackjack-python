import os
import sys
import time
import tty
import termios

from art import logo as LOGO
from blackjack import Difficulty, GameResult, GameSession, Hand
from config import DIVIDER_WIDTH, LOGO_PAUSE, MIN_BET, STARTING_CHIPS, TYPEWRITER_DELAY

# ── ANSI colour codes ──────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
WHITE   = "\033[97m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"

_RESULT_DISPLAY: dict[GameResult, tuple[str, str]] = {
    GameResult.WIN:            (GREEN,  "You win!"),
    GameResult.LOSE:           (RED,    "You lose."),
    GameResult.DRAW:           (YELLOW, "Draw."),
    GameResult.BLACKJACK_WIN:  (GREEN,  "Blackjack! You win!"),
    GameResult.BLACKJACK_LOSE: (RED,    "Dealer has Blackjack. You lose."),
    GameResult.BUST:           (RED,    "Bust! You went over 21."),
    GameResult.DEALER_BUST:    (GREEN,  "Dealer busted! You win!"),
}


# ── ASCII card art ─────────────────────────────────────────────────────────────
#
#  Each card is 9 visual chars wide × 7 lines tall:
#
#    ┌───────┐
#    │A      │
#    │       │
#    │   ♥   │
#    │       │
#    │      A│
#    └───────┘
#
#  Back of card (face-down):
#
#    ┌───────┐
#    │▓▓▓▓▓▓▓│   (cyan fill)
#    │▓▓▓▓▓▓▓│
#    │▓▓▓▓▓▓▓│
#    │▓▓▓▓▓▓▓│
#    │▓▓▓▓▓▓▓│
#    └───────┘

_CARD_H = 7    # card height in lines
_CARD_W = 9    # card visual width (no ANSI codes)
_AVATAR_W = 10 # avatar visual width (no ANSI codes)

# Face-down card (cyan back)
_BACK_ROWS: list[str] = [
    "┌───────┐",
    f"│{CYAN}▓▓▓▓▓▓▓{RESET}│",
    f"│{CYAN}▓▓▓▓▓▓▓{RESET}│",
    f"│{CYAN}▓▓▓▓▓▓▓{RESET}│",
    f"│{CYAN}▓▓▓▓▓▓▓{RESET}│",
    f"│{CYAN}▓▓▓▓▓▓▓{RESET}│",
    "└───────┘",
]

# Avatars — pure ASCII, exactly _AVATAR_W=10 chars per line, _CARD_H=7 lines tall.
#
# DEALER: casino dealer with green eyeshade visor and bow tie
#
#   _____
#  [=====]  <- visor
#  ( o.o )  <- face
#    >-<    <- bow tie
#   /| |\   <- jacket lapels
#    | |
#   _| |_   <- feet
#
# PLAYER: relaxed T-pose, happy face
#
#    ___
#   (^_^)   <- happy face
#     |
#   --+--   <- arms spread
#     |
#    / \
#

_DEALER_AVATAR: list[str] = [
    "  _____   ",
    " [=====]  ",
    " ( o.o )  ",
    "   >-<    ",
    "  /| |\\   ",   # visual: /| |\
    "   | |    ",
    "  _| |_   ",
]

_PLAYER_AVATAR: list[str] = [
    "   ___    ",
    "  (^_^)   ",
    "    |     ",
    "  --+--   ",
    "    |     ",
    "   / \\    ",   # visual: / \
    "          ",
]


def _card_rows(label: str, suit: str) -> list[str]:
    """Return 7 strings for a single face-up card."""
    suit_color = RED if suit in ("♥", "♦") else WHITE
    c_suit = f"{suit_color}{suit}{RESET}"
    pad = 7 - len(label)   # inner width is 7; label is 1–2 chars
    return [
        f"{WHITE}┌───────┐{RESET}",
        f"{WHITE}│{RESET}{label}{' ' * pad}{WHITE}│{RESET}",
        f"{WHITE}│       │{RESET}",
        f"{WHITE}│   {c_suit}   │{RESET}",
        f"{WHITE}│       │{RESET}",
        f"{WHITE}│{RESET}{' ' * pad}{label}{WHITE}│{RESET}",
        f"{WHITE}└───────┘{RESET}",
    ]


def _render_cards(
    labels: list[str],
    suits: list[str],
    visible_count: int | None = None,
) -> list[str]:
    """Return _CARD_H lines with cards rendered side by side.

    visible_count — how many cards show face-up (rest are face-down back).
    None means all face-up.
    """
    if not labels:
        return [""] * _CARD_H

    if visible_count is None:
        visible_count = len(labels)

    all_cards = [
        _card_rows(lbl, suit) if i < visible_count else _BACK_ROWS
        for i, (lbl, suit) in enumerate(zip(labels, suits))
    ]
    return ["  ".join(c[row] for c in all_cards) for row in range(_CARD_H)]


def _render_person_section(
    title: str,
    score_str: str,
    avatar: list[str],
    card_rows: list[str],
    color: str,
    indent: str = "  ",
) -> None:
    """Print an avatar + cards section for dealer or player."""
    print(f"{indent}{color}{BOLD}{title}{RESET}  {DIM}[{score_str}]{RESET}")
    print()
    gap = "  "
    for av_line, card_line in zip(avatar, card_rows):
        print(f"{indent}{color}{av_line}{RESET}{gap}{card_line}")
    print()


# ── Utilities ─────────────────────────────────────────────────────────────────

def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def divider() -> None:
    print(f"{DIM}{'─' * DIVIDER_WIDTH}{RESET}")


def typewriter(text: str, delay: float = TYPEWRITER_DELAY) -> None:
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)


def get_keypress() -> str:
    """Read a single keypress. Returns 'UP' for the up-arrow key."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            nxt = sys.stdin.read(2)
            return "UP" if nxt == "[A" else f"{ch}{nxt}"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ── Display helpers ────────────────────────────────────────────────────────────

def show_logo() -> None:
    clear()
    typewriter(LOGO)
    time.sleep(LOGO_PAUSE)


def show_header(title: str, subtitle: str = "") -> None:
    clear()
    divider()
    print(f"{CYAN}{BOLD}{title}{RESET}")
    if subtitle:
        print(f"{DIM}{subtitle}{RESET}")
    divider()
    print()


def print_error(msg: str) -> None:
    print(f"{RED}✗  {msg}{RESET}")


def print_info(msg: str) -> None:
    print(f"{CYAN}ℹ  {msg}{RESET}")


def print_result(result: GameResult) -> None:
    color, msg = _RESULT_DISPLAY[result]
    print(f"\n{color}{BOLD}{msg}{RESET}")


def show_hand(label: str, hand: Hand, hide_second: bool = False) -> None:
    """Print a labelled hand with ASCII card art."""
    hide = hide_second and len(hand.cards) > 1
    visible_count = 1 if hide else None
    score_str = "?" if hide else ("Blackjack!" if hand.is_blackjack else str(hand.score))

    print(f"  {CYAN}{label}{RESET}  {DIM}[{score_str}]{RESET}")
    if hand.labels:
        for row in _render_cards(hand.labels, hand.suits, visible_count=visible_count):
            print(f"  {row}")
    print()


def show_chip_delta(delta: int, chips: int) -> None:
    if delta > 0:
        print(f"  {GREEN}{BOLD}+{delta} chips{RESET}   {DIM}Balance: {chips}{RESET}")
    elif delta == 0:
        print(f"  {YELLOW}±0 chips{RESET}   {DIM}Balance: {chips}{RESET}")
    else:
        print(f"  {RED}{BOLD}{delta} chips{RESET}   {DIM}Balance: {chips}{RESET}")


def show_game_state(
    session: GameSession,
    bet: int,
    player: Hand,
    dealer: Hand,
    hide_second: bool = True,
) -> None:
    """Full-screen table view: header + dealer section + player section."""
    clear()

    # ── Status bar ────────────────────────────────────────────────────────────
    diff_color = {
        Difficulty.EASY:   GREEN,
        Difficulty.NORMAL: CYAN,
        Difficulty.HARD:   RED,
    }[session.difficulty]
    divider()
    print(
        f"{CYAN}{BOLD}♠  BLACKJACK{RESET}   "
        f"{diff_color}{session.difficulty.value}{RESET}   "
        f"{YELLOW}Chips: {session.chips + bet}{RESET}   "
        f"{DIM}Bet: {bet}   Deck: {session.shoe.remaining}{RESET}"
    )
    divider()
    print()

    # ── Dealer section ────────────────────────────────────────────────────────
    hide = hide_second and not session.difficulty.show_dealer_hand
    visible = 1 if hide else None
    dealer_score = (
        "?" if hide
        else ("Blackjack!" if dealer.is_blackjack else str(dealer.score))
    )
    dealer_cards = _render_cards(dealer.labels, dealer.suits, visible_count=visible)
    _render_person_section("DEALER", dealer_score, _DEALER_AVATAR, dealer_cards, CYAN)

    # ── Player section ────────────────────────────────────────────────────────
    player_score = "Blackjack!" if player.is_blackjack else str(player.score)
    player_cards = _render_cards(player.labels, player.suits)
    _render_person_section("YOU", player_score, _PLAYER_AVATAR, player_cards, GREEN)


# ── Prompts ────────────────────────────────────────────────────────────────────

def prompt_bet(chips: int) -> int | None:
    """Prompt the player for a bet. Returns None if player types 'q'."""
    print(f"  {DIM}Your chips: {RESET}{YELLOW}{chips}{RESET}")
    print(f"  {DIM}Min bet: {MIN_BET}   Type 'q' to quit{RESET}")
    while True:
        try:
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass
        raw = input(f"  {CYAN}Bet: {RESET}").strip().lower()
        if raw == "q":
            return None
        if raw.isdigit():
            amount = int(raw)
            if amount < MIN_BET:
                print_error(f"Minimum bet is {MIN_BET}.")
            elif amount > chips:
                print_error("Not enough chips.")
            else:
                return amount
        else:
            print_error("Enter a number or 'q'.")


def prompt_insurance(max_bet: int) -> int:
    """Prompt the player for an insurance bet. Returns 0 to skip."""
    print(f"\n  {YELLOW}Dealer shows an Ace!{RESET}")
    print(f"  {DIM}Insurance bet (0 to {max_bet}, 0 = no insurance):{RESET}")
    while True:
        raw = input(f"  {CYAN}Insurance: {RESET}").strip()
        if raw.isdigit():
            amount = int(raw)
            if 0 <= amount <= max_bet:
                return amount
        print_error(f"Enter a number from 0 to {max_bet}.")


def prompt_first_action(can_split: bool, can_double: bool) -> str:
    """Show first-action prompt. Returns 'h', 's', 'd', 'p', or 'q'."""
    options = "[H] Hit   [S] Stay"
    if can_double:
        options += "   [D] Double"
    if can_split:
        options += "   [P] Split"
    options += "   [Q] Forfeit"
    print(f"\n{DIM}{options}{RESET}  ", end="", flush=True)
    valid = {"h", "s", "q"}
    if can_double:
        valid.add("d")
    if can_split:
        valid.add("p")
    while True:
        key = get_keypress().lower()
        if key in valid:
            return key


def prompt_action() -> str:
    """Show hit/stay/quit prompt. Returns 'h', 's', or 'q'."""
    print(f"\n{DIM}[H] Hit   [S] Stay   [Q] Forfeit{RESET}  ", end="", flush=True)
    while True:
        key = get_keypress().lower()
        if key in ("h", "s", "q"):
            return key


def prompt_continue() -> str:
    """Returns 'UP' for menu, any other key to play again."""
    print(f"\n{DIM}[Enter] Play Again   [↑] Menu{RESET}  ", end="", flush=True)
    return get_keypress()


def prompt_difficulty() -> Difficulty:
    """Full-screen difficulty selection. Returns chosen Difficulty."""
    show_header("♠  DIFFICULTY", "Choose your difficulty level")
    print(f"  {GREEN}[1]{RESET}  Easy    — dealer's hand always visible")
    print(f"  {CYAN}[2]{RESET}  Normal  — dealer stands at 17")
    print(f"  {RED}[3]{RESET}  Hard    — dealer stands at 18")
    print()
    while True:
        key = get_keypress()
        if key == "1":
            return Difficulty.EASY
        if key == "2":
            return Difficulty.NORMAL
        if key == "3":
            return Difficulty.HARD


# ── Statistics screen ──────────────────────────────────────────────────────────

def show_stats(session: GameSession | None) -> None:
    show_header("♠  STATISTICS", "Session summary")
    if session is None:
        print(f"  {DIM}No session played yet.{RESET}")
    else:
        diff_color = {
            Difficulty.EASY:   GREEN,
            Difficulty.NORMAL: CYAN,
            Difficulty.HARD:   RED,
        }[session.difficulty]
        rows = [
            ("Difficulty",         f"{diff_color}{session.difficulty.value}{RESET}"),
            ("Rounds played",      str(session.rounds_played)),
            ("Hands played",       str(session.hands_played)),
            ("Wins",               f"{GREEN}{session.wins}{RESET}"),
            ("Losses",             f"{RED}{session.losses}{RESET}"),
            ("Draws",              f"{YELLOW}{session.draws}{RESET}"),
            ("Blackjacks",         f"{GREEN}{session.blackjacks}{RESET}"),
            ("Busts",              f"{RED}{session.busts}{RESET}"),
            ("Win rate",           f"{session.win_rate:.1f}%"),
            ("Longest win streak", str(session.longest_win_streak)),
            ("Final chips",        f"{YELLOW}{session.chips}{RESET}"),
            ("Profit / Loss",      _profit_str(session.chips)),
        ]
        for label, value in rows:
            print(f"  {DIM}{label:<22}{RESET}{value}")
    print(f"\n{DIM}[↑] Back{RESET}  ", end="", flush=True)
    while get_keypress() != "UP":
        pass


def _profit_str(chips: int) -> str:
    delta = chips - STARTING_CHIPS
    if delta > 0:
        return f"{GREEN}+{delta}{RESET}"
    if delta < 0:
        return f"{RED}{delta}{RESET}"
    return f"{YELLOW}0{RESET}"


# ── ASCII block-letter font ────────────────────────────────────────────────────
#  Each glyph is exactly 6 chars wide × 5 lines tall.
#  Characters used across all animations: A B D E N O R S T U V !

_ASCII_FONT: dict[str, list[str]] = {
    'A': [" ###  ", "#   # ", "##### ", "#   # ", "#   # "],
    'B': ["####  ", "#   # ", "####  ", "#   # ", "####  "],
    'D': ["####  ", "#   # ", "#   # ", "#   # ", "####  "],
    'E': ["##### ", "#     ", "####  ", "#     ", "##### "],
    'N': ["#   # ", "##  # ", "# # # ", "#  ## ", "#   # "],
    'O': [" ###  ", "#   # ", "#   # ", "#   # ", " ###  "],
    'R': ["####  ", "#   # ", "####  ", "#  #  ", "#   # "],
    'S': [" #### ", "#     ", " ###  ", "    # ", "####  "],
    'T': ["##### ", "  #   ", "  #   ", "  #   ", "  #   "],
    'U': ["#   # ", "#   # ", "#   # ", "#   # ", " ###  "],
    'V': ["#   # ", "#   # ", " # #  ", " # #  ", "  #   "],
    '!': ["  #   ", "  #   ", "  #   ", "      ", "  #   "],
    ' ': ["      ", "      ", "      ", "      ", "      "],
}


def _render_big_text(word: str) -> list[str]:
    """Combine glyphs from _ASCII_FONT into 5 horizontal lines."""
    rows = [""] * 5
    for ch in word.upper():
        glyph = _ASCII_FONT.get(ch, _ASCII_FONT[' '])
        for i, row in enumerate(glyph):
            rows[i] += row
    return rows


# ── Animations ─────────────────────────────────────────────────────────────────

def animate_deal(label: str, suit: str, hold_after: float = 0.55) -> None:
    """Side-panel card-flip animation for a newly dealt card.

    Sequence: face-down back → narrowing back → edge → face-up card.
    Prints below the current board (no clear) so the table stays visible.
    Uses cursor-up ANSI escape to overwrite lines in place.
    """
    INDENT = " " * 55

    face_down_full = _BACK_ROWS
    face_down_mid = [
        "┌─────┐",
        f"│{CYAN}▓▓▓▓▓{RESET}│",
        f"│{CYAN}▓▓▓▓▓{RESET}│",
        f"│{CYAN}▓▓▓▓▓{RESET}│",
        f"│{CYAN}▓▓▓▓▓{RESET}│",
        f"│{CYAN}▓▓▓▓▓{RESET}│",
        "└─────┘",
    ]
    face_down_thin = [
        "┌─┐",
        f"│{CYAN}▓{RESET}│",
        f"│{CYAN}▓{RESET}│",
        f"│{CYAN}▓{RESET}│",
        f"│{CYAN}▓{RESET}│",
        f"│{CYAN}▓{RESET}│",
        "└─┘",
    ]
    face_up = _card_rows(label, suit)

    frames = [face_down_full, face_down_mid, face_down_thin, face_up]
    # Delays: how long to show each frame before moving to the next
    frame_delays = [0.14, 0.09, 0.09]   # transitions (one fewer than frames)

    # No clear — board stays visible; animation appears to the right below it
    print(f"\n{INDENT}{DIM}Dealing...{RESET}")

    # Print first frame
    for row in frames[0]:
        sys.stdout.write(f"{INDENT}{row}\n")
    sys.stdout.flush()

    # Animate through remaining frames
    for frame, delay in zip(frames[1:], frame_delays):
        time.sleep(delay)
        sys.stdout.write("\033[7A")          # cursor up 7 lines
        for row in frame:
            sys.stdout.write(f"\r{INDENT}{row}\033[K\n")
        sys.stdout.flush()

    time.sleep(hold_after)


def animate_stand() -> None:
    """Big ASCII block 'STAND' letters that pulse once then hold.

    Prints below the current board (no clear) so the table stays visible.
    """
    INDENT = " " * 44
    rows = _render_big_text("STAND")

    print()  # blank separator

    # First show — bright yellow
    for row in rows:
        sys.stdout.write(f"{INDENT}{YELLOW}{BOLD}{row}{RESET}\n")
    sys.stdout.flush()
    time.sleep(0.35)

    # Pulse dim
    sys.stdout.write("\033[5A")
    for row in rows:
        sys.stdout.write(f"\r{INDENT}{DIM}{row}{RESET}\033[K\n")
    sys.stdout.flush()
    time.sleep(0.18)

    # Pulse bright again
    sys.stdout.write("\033[5A")
    for row in rows:
        sys.stdout.write(f"\r{INDENT}{YELLOW}{BOLD}{row}{RESET}\033[K\n")
    sys.stdout.flush()
    time.sleep(1.1)


def animate_bust() -> None:
    """Big ASCII block 'BUSTED' letters in red that pulse once then hold.

    Prints below the current board (no clear) so the table stays visible.
    """
    INDENT = " " * 44
    rows = _render_big_text("BUSTED")

    print()  # blank separator

    # First show — bright red
    for row in rows:
        sys.stdout.write(f"{INDENT}{RED}{BOLD}{row}{RESET}\n")
    sys.stdout.flush()
    time.sleep(0.35)

    # Pulse dim
    sys.stdout.write("\033[5A")
    for row in rows:
        sys.stdout.write(f"\r{INDENT}{DIM}{RED}{row}{RESET}\033[K\n")
    sys.stdout.flush()
    time.sleep(0.18)

    # Pulse bright again
    sys.stdout.write("\033[5A")
    for row in rows:
        sys.stdout.write(f"\r{INDENT}{RED}{BOLD}{row}{RESET}\033[K\n")
    sys.stdout.flush()
    time.sleep(1.1)


def animate_round_over() -> None:
    """Big ASCII block 'ROUND OVER !' letters."""
    clear()
    print("\n\n")
    for row in _render_big_text("ROUND"):
        sys.stdout.write(f"  {YELLOW}{BOLD}{row}{RESET}\n")
    sys.stdout.write("\n")
    for row in _render_big_text("OVER !"):
        sys.stdout.write(f"  {YELLOW}{BOLD}{row}{RESET}\n")
    sys.stdout.flush()
    time.sleep(1.8)
