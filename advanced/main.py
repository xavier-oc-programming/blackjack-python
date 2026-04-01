import os
import sys
import time
from typing import Callable

sys.path.insert(0, os.path.dirname(__file__))                    # advanced/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))   # repo root → art.py

import display
from blackjack import (
    GameResult,
    GameSession,
    Hand,
    chip_delta,
    compare,
)
from config import MIN_BET


# ── Module-level last session (for Statistics screen) ─────────────────────────

_last_session: GameSession | None = None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _resolve_hand(session: GameSession, result: GameResult, committed: int) -> int:
    """Apply result to session chips (bet already pre-deducted). Return net delta."""
    returned = chip_delta(result, committed)
    session.chips += returned
    session.record_result(result)
    return returned - committed


def _animate_dealer_reveal(
    session: GameSession, bet: int, player: Hand, dealer: Hand
) -> None:
    """Flip dealer's hole card, then animate hit/stand decisions one by one."""
    # Show with hole card still hidden
    display.show_game_state(session, bet, player, dealer, hide_second=True)
    print(f"\n  {display.DIM}Dealer reveals hole card...{display.RESET}")
    time.sleep(0.5)

    # Flip the hole card (index 1 was face-down)
    display.animate_deal(dealer.labels[1], dealer.suits[1], hold_after=1.5)
    display.show_game_state(session, bet, player, dealer, hide_second=False)
    time.sleep(0.45)

    # Dealer draws cards one by one with animation
    threshold = session.difficulty.dealer_threshold
    while not dealer.is_blackjack and dealer.score < threshold:
        display.show_game_state(session, bet, player, dealer, hide_second=False)
        print(f"\n  {display.YELLOW}{display.BOLD}DEALER HITS{display.RESET}")
        time.sleep(2.7)
        dealer.add_card(session.shoe)
        display.animate_deal(dealer.labels[-1], dealer.suits[-1], hold_after=1.5)
        display.show_game_state(session, bet, player, dealer, hide_second=False)
        time.sleep(0.35)

    # Dealer stands
    display.show_game_state(session, bet, player, dealer, hide_second=False)
    print(f"\n  {display.GREEN}{display.BOLD}DEALER STANDS{display.RESET}")
    time.sleep(5.0)


def _play_split_hand(
    hand: Hand, session: GameSession, bet: int, dealer: Hand
) -> tuple[Hand, int]:
    """Play a single split hand interactively. Returns (final_hand, final_bet)."""
    original_bet = bet
    first_action = True

    while not hand.is_bust:
        can_double = first_action and session.chips >= original_bet

        display.show_game_state(session, bet, hand, dealer, hide_second=True)
        print(f"  {display.CYAN}(Split hand){display.RESET}")

        if first_action:
            key = display.prompt_first_action(can_split=False, can_double=can_double)
        else:
            key = display.prompt_action()

        first_action = False

        if key == "q":
            break
        if key == "s":
            break
        if key == "d":
            session.chips -= original_bet
            bet *= 2
            hand.add_card(session.shoe)
            display.animate_deal(hand.labels[-1], hand.suits[-1])
            break
        # key == "h"
        hand.add_card(session.shoe)
        display.animate_deal(hand.labels[-1], hand.suits[-1])

    if hand.is_bust:
        display.animate_bust()
    return hand, bet


# ── Round ─────────────────────────────────────────────────────────────────────

def play_round(session: GameSession) -> bool:
    """Play one full round. Returns True to play again, False to stop."""

    # ── Bet ───────────────────────────────────────────────────────────────────
    display.show_header(
        "♠  BLACKJACK",
        f"Chips: {session.chips}   Difficulty: {session.difficulty.value}   Deck: {session.shoe.remaining}",
    )

    if session.chips < MIN_BET:
        display.print_error("You're out of chips! Session over.")
        display.prompt_continue()
        return False

    bet_amount = display.prompt_bet(session.chips)
    if bet_amount is None:
        return False

    # Pre-deduct bet
    session.chips -= bet_amount
    bet = bet_amount
    original_bet = bet

    # ── Deal ──────────────────────────────────────────────────────────────────
    player = Hand()
    dealer = Hand()
    for _ in range(2):
        player.add_card(session.shoe)
        dealer.add_card(session.shoe)

    session.rounds_played += 1

    # ── Insurance ─────────────────────────────────────────────────────────────
    insurance_bet = 0
    if dealer.cards[0] == 11:
        max_ins = bet // 2
        if max_ins > 0:
            display.show_game_state(session, bet, player, dealer, hide_second=True)
            insurance_bet = display.prompt_insurance(max_ins)
            if insurance_bet > 0:
                session.chips -= insurance_bet

    # ── Immediate blackjack check ─────────────────────────────────────────────
    if player.is_blackjack or dealer.is_blackjack:
        if insurance_bet > 0:
            if dealer.is_blackjack:
                session.chips += insurance_bet * 3
                display.print_info(f"Insurance pays! +{insurance_bet * 2} chips.")
            else:
                display.print_error(f"Insurance lost. -{insurance_bet} chips.")

        result = compare(player, dealer)
        display.animate_round_over()
        display.show_game_state(session, bet, player, dealer, hide_second=False)
        display.print_result(result)
        net = _resolve_hand(session, result, bet)
        display.show_chip_delta(net, session.chips)
        return display.prompt_continue() != "UP"

    # ── First action: double / split / hit / stay ─────────────────────────────
    can_double = session.chips >= original_bet
    can_split  = (
        len(player.cards) == 2
        and player.cards[0] == player.cards[1]
        and session.chips >= original_bet
    )

    display.show_game_state(session, bet, player, dealer, hide_second=True)
    first_key = display.prompt_first_action(can_split=can_split, can_double=can_double)

    # ── Forfeit ───────────────────────────────────────────────────────────────
    if first_key == "q":
        display.show_game_state(session, bet, player, dealer, hide_second=False)
        display.print_error("You forfeited the round.")
        display.show_chip_delta(-bet, session.chips)
        return False

    # ── SPLIT ─────────────────────────────────────────────────────────────────
    if first_key == "p":
        session.chips -= original_bet

        hand_a = Hand(
            cards=[player.cards[0]],
            suits=[player.suits[0]],
            labels=[player.labels[0]],
        )
        hand_b = Hand(
            cards=[player.cards[1]],
            suits=[player.suits[1]],
            labels=[player.labels[1]],
        )
        hand_a.add_card(session.shoe)
        hand_b.add_card(session.shoe)

        display.print_info("Playing split hand 1 of 2 ...")
        hand_a, bet_a = _play_split_hand(hand_a, session, original_bet, dealer)

        display.print_info("Playing split hand 2 of 2 ...")
        hand_b, bet_b = _play_split_hand(hand_b, session, original_bet, dealer)

        # Dealer plays once for both hands
        if not (hand_a.is_bust and hand_b.is_bust):
            _animate_dealer_reveal(session, bet, hand_a, dealer)

        display.animate_round_over()

        result_a = compare(hand_a, dealer)
        result_b = compare(hand_b, dealer)

        display.show_header("♠  BLACKJACK", "Split — Final result")
        display.show_hand("Hand 1", hand_a)
        display.show_hand("Hand 2", hand_b)
        display.show_hand("Dealer", dealer)

        net_a = _resolve_hand(session, result_a, bet_a)
        net_b = _resolve_hand(session, result_b, bet_b)

        display.print_result(result_a)
        print(f"  {display.DIM}Hand 1:{display.RESET}", end=" ")
        display.show_chip_delta(net_a, session.chips)
        display.print_result(result_b)
        print(f"  {display.DIM}Hand 2:{display.RESET}", end=" ")
        display.show_chip_delta(net_b, session.chips)

        return display.prompt_continue() != "UP"

    # ── DOUBLE DOWN ───────────────────────────────────────────────────────────
    if first_key == "d":
        session.chips -= original_bet
        bet *= 2
        player.add_card(session.shoe)
        display.animate_deal(player.labels[-1], player.suits[-1])
        if player.is_bust:
            display.animate_bust()

        _animate_dealer_reveal(session, bet, player, dealer)
        display.animate_round_over()

        result = compare(player, dealer)
        display.show_header("♠  BLACKJACK", "Double down — Final result")
        display.show_hand("Your hand", player)
        display.show_hand("Dealer", dealer)
        display.print_result(result)
        net = _resolve_hand(session, result, bet)
        display.show_chip_delta(net, session.chips)
        return display.prompt_continue() != "UP"

    # ── HIT / STAY loop ───────────────────────────────────────────────────────
    if first_key == "h":
        player.add_card(session.shoe)
        display.animate_deal(player.labels[-1], player.suits[-1])

    if first_key == "s":
        display.animate_stand()

    # Continue if not already standing or busted on first hit
    if first_key != "s" and not player.is_bust:
        while not player.is_bust:
            display.show_game_state(session, bet, player, dealer, hide_second=True)
            key = display.prompt_action()
            if key == "q":
                display.show_game_state(session, bet, player, dealer, hide_second=False)
                display.print_error("You forfeited the round.")
                display.show_chip_delta(-bet, session.chips)
                return False
            if key == "s":
                display.animate_stand()
                break
            player.add_card(session.shoe)
            display.animate_deal(player.labels[-1], player.suits[-1])

    # ── Dealer turn ───────────────────────────────────────────────────────────
    if player.is_bust:
        display.animate_bust()
    else:
        _animate_dealer_reveal(session, bet, player, dealer)

    # ── Round Over + results ──────────────────────────────────────────────────
    display.animate_round_over()
    result = compare(player, dealer)
    display.show_header("♠  BLACKJACK", "Final hands")
    display.show_hand("Your hand", player)
    display.show_hand("Dealer's hand", dealer)
    display.print_result(result)
    net = _resolve_hand(session, result, bet)
    display.show_chip_delta(net, session.chips)

    return display.prompt_continue() != "UP"


# ── Game loop ─────────────────────────────────────────────────────────────────

def game_loop() -> None:
    global _last_session

    difficulty = display.prompt_difficulty()
    session = GameSession(difficulty=difficulty)
    _last_session = session

    while True:
        if session.chips < MIN_BET:
            display.show_header("♠  BLACKJACK", "Out of chips")
            display.print_error(f"You have fewer than {MIN_BET} chips. Session over.")
            display.show_stats(session)
            break
        if not play_round(session):
            break


# ── Rules screen ──────────────────────────────────────────────────────────────

def rules_screen() -> None:
    display.show_header("♠  RULES", "House rules for this game")
    rules = [
        "· 4-deck shoe, reshuffled when < 20 cards remain.",
        "· J / Q / K = 10.  Ace = 11 or 1.",
        "· Blackjack = Ace + 10-value on first deal (2 cards only).",
        "· Dealer stands at 17 (Normal) or 18 (Hard).",
        "· Easy mode: dealer's full hand always visible.",
        "· Bust (over 21) = loss.",
        "· Ties are a draw.",
        "",
        "CHIPS",
        "· You start with 500 chips.  Min bet: 5.",
        "· Win → bet × 2 returned.  Draw → bet returned.",
        "",
        "DOUBLE DOWN",
        "· First action only.  Doubles bet, deals one card, then stand.",
        "",
        "SPLIT",
        "· First two cards must match in value.",
        "· Each hand is played separately; dealer plays once.",
        "",
        "INSURANCE",
        "· Offered when dealer shows an Ace.",
        "· Bet up to half your original bet.",
        "· Pays 2:1 if dealer has Blackjack.",
    ]
    for rule in rules:
        if rule and not rule.startswith("·"):
            print(f"\n  {display.BOLD}{rule}{display.RESET}")
        else:
            print(f"  {display.DIM}{rule}{display.RESET}")
    print(f"\n{display.DIM}[↑] Back{display.RESET}  ", end="", flush=True)
    while display.get_keypress() != "UP":
        pass


# ── Statistics screen ─────────────────────────────────────────────────────────

def stats_screen() -> None:
    display.show_stats(_last_session)


# ── Mode registry ─────────────────────────────────────────────────────────────

MODES: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Play Blackjack", game_loop),
    "2": ("Rules",          rules_screen),
    "3": ("Statistics",     stats_screen),
}


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    display.show_logo()
    while True:
        display.show_header("♠  BLACKJACK", "Choose a mode  ·  ↑ to quit")
        for key, (label, _) in MODES.items():
            print(f"  {display.CYAN}[{key}]{display.RESET}  {label}")
        print()
        key = display.get_keypress()
        if key == "UP":
            display.clear()
            break
        if key in MODES:
            MODES[key][1]()


if __name__ == "__main__":
    main()
