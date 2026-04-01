import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Final

from config import (
    BLACKJACK_SENTINEL,
    DEALER_HIT_THRESHOLD_NORMAL,
    DEALER_HIT_THRESHOLD_HARD,
    DECK,
    DECK_COUNT,
    RESHUFFLE_THRESHOLD,
    STARTING_CHIPS,
)


# ── Game result ───────────────────────────────────────────────────────────────

class GameResult(Enum):
    WIN = auto()
    LOSE = auto()
    DRAW = auto()
    BLACKJACK_WIN = auto()
    BLACKJACK_LOSE = auto()
    BUST = auto()
    DEALER_BUST = auto()


# ── Difficulty ────────────────────────────────────────────────────────────────

class Difficulty(Enum):
    EASY   = "Easy"
    NORMAL = "Normal"
    HARD   = "Hard"

    @property
    def dealer_threshold(self) -> int:
        if self == Difficulty.HARD:
            return DEALER_HIT_THRESHOLD_HARD
        return DEALER_HIT_THRESHOLD_NORMAL

    @property
    def show_dealer_hand(self) -> bool:
        """Easy mode always shows the dealer's full hand."""
        return self == Difficulty.EASY


# ── Shoe (finite deck) ────────────────────────────────────────────────────────

@dataclass
class Shoe:
    deck_count: int = DECK_COUNT

    _cards: list[int] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._build()

    def _build(self) -> None:
        self._cards = DECK * (self.deck_count * 4)   # 4 suits per deck
        random.shuffle(self._cards)

    @property
    def remaining(self) -> int:
        return len(self._cards)

    def deal(self) -> int:
        if self.remaining < RESHUFFLE_THRESHOLD:
            self._build()
        return self._cards.pop()


# ── Score calculation ─────────────────────────────────────────────────────────

def calculate_score(cards: list[int]) -> int:
    """Returns hand score. Returns BLACKJACK_SENTINEL (0) for a 2-card 21."""
    working = list(cards)
    total = sum(working)
    if total == 21 and len(working) == 2:
        return BLACKJACK_SENTINEL
    while total > 21 and 11 in working:
        working.remove(11)
        working.append(1)
        total = sum(working)
    return total


# ── Hand ──────────────────────────────────────────────────────────────────────

_SUITS: Final[list[str]]      = ["♠", "♥", "♦", "♣"]
_TEN_LABELS: Final[list[str]] = ["10", "J", "Q", "K"]


@dataclass
class Hand:
    cards:  list[int] = field(default_factory=list)
    suits:  list[str] = field(default_factory=list, repr=False)
    labels: list[str] = field(default_factory=list, repr=False)

    @property
    def score(self) -> int:
        return calculate_score(self.cards)

    @property
    def is_blackjack(self) -> bool:
        return self.score == BLACKJACK_SENTINEL

    @property
    def is_bust(self) -> bool:
        return self.score > 21

    def add_card(self, shoe: Shoe | None = None) -> int:
        """Deal a card into the hand. Draws from shoe if provided, else random."""
        card = shoe.deal() if shoe is not None else random.choice(DECK)
        self.cards.append(card)
        self.suits.append(random.choice(_SUITS))
        if card == 11:
            self.labels.append("A")
        elif card == 10:
            self.labels.append(random.choice(_TEN_LABELS))
        else:
            self.labels.append(str(card))
        return card


# ── Dealer logic ──────────────────────────────────────────────────────────────

def run_dealer(dealer: Hand, threshold: int, shoe: Shoe | None = None) -> None:
    """Dealer draws until reaching threshold or blackjack."""
    while dealer.score != BLACKJACK_SENTINEL and dealer.score < threshold:
        dealer.add_card(shoe)


# ── Compare ───────────────────────────────────────────────────────────────────

def compare(player: Hand, dealer: Hand) -> GameResult:
    p, d = player.score, dealer.score
    if p == d:
        return GameResult.DRAW
    if d == BLACKJACK_SENTINEL:
        return GameResult.BLACKJACK_LOSE
    if p == BLACKJACK_SENTINEL:
        return GameResult.BLACKJACK_WIN
    if p > 21:
        return GameResult.BUST
    if d > 21:
        return GameResult.DEALER_BUST
    if p > d:
        return GameResult.WIN
    return GameResult.LOSE


# ── Chip delta ────────────────────────────────────────────────────────────────

def chip_delta(result: GameResult, bet: int) -> int:
    """Net chip change AFTER bet has already been pre-deducted.

    Win / Dealer bust / Blackjack win → return bet * 2 (profit = +bet)
    Draw                              → return bet      (profit = 0)
    Loss / Bust / Blackjack lose      → return 0        (profit = -bet)
    """
    if result in (GameResult.WIN, GameResult.DEALER_BUST, GameResult.BLACKJACK_WIN):
        return bet * 2
    if result == GameResult.DRAW:
        return bet
    return 0


# ── Session / statistics ──────────────────────────────────────────────────────

@dataclass
class GameSession:
    difficulty: Difficulty = Difficulty.NORMAL
    chips: int = STARTING_CHIPS
    shoe: Shoe = field(default_factory=Shoe)

    # stat counters
    wins: int = 0
    losses: int = 0
    draws: int = 0
    blackjacks: int = 0
    busts: int = 0
    rounds_played: int = 0

    _current_streak: int = field(default=0, init=False, repr=False)
    longest_win_streak: int = 0

    def record_result(self, result: GameResult) -> None:
        """Update stat counters for a single hand result (not per round)."""
        if result in (GameResult.WIN, GameResult.DEALER_BUST):
            self.wins += 1
            self._current_streak += 1
            if self._current_streak > self.longest_win_streak:
                self.longest_win_streak = self._current_streak
        elif result == GameResult.BLACKJACK_WIN:
            self.wins += 1
            self.blackjacks += 1
            self._current_streak += 1
            if self._current_streak > self.longest_win_streak:
                self.longest_win_streak = self._current_streak
        elif result == GameResult.DRAW:
            self.draws += 1
            # streak preserved on draw
        elif result == GameResult.BUST:
            self.losses += 1
            self.busts += 1
            self._current_streak = 0
        elif result in (GameResult.LOSE, GameResult.BLACKJACK_LOSE):
            self.losses += 1
            self._current_streak = 0

    @property
    def hands_played(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def win_rate(self) -> float:
        if self.hands_played == 0:
            return 0.0
        return self.wins / self.hands_played * 100
