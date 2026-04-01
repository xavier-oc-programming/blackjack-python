from typing import Final

DECK: Final[list[int]] = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]
BLACKJACK_SENTINEL: Final[int] = 0   # score value that signals a blackjack hand
DEALER_HIT_THRESHOLD_NORMAL: Final[int] = 17
DEALER_HIT_THRESHOLD_HARD: Final[int] = 18
TYPEWRITER_DELAY: Final[float] = 0.004
LOGO_PAUSE: Final[float] = 0.6
DIVIDER_WIDTH: Final[int] = 52
STARTING_CHIPS: Final[int] = 500
DECK_COUNT: Final[int] = 4
RESHUFFLE_THRESHOLD: Final[int] = 20
MIN_BET: Final[int] = 5
