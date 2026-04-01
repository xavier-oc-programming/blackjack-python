"""Root version selector — launches original/ or advanced/ via subprocess."""
import os
import subprocess
import sys

from art import logo

RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
CYAN  = "\033[96m"
RED   = "\033[91m"

HERE = os.path.dirname(__file__)

VERSIONS: dict[str, tuple[str, str]] = {
    "1": ("Original  — procedural, close to course", "original/main.py"),
    "2": ("Advanced  — OOP, modular, full UX",       "advanced/main.py"),
}


def main() -> None:
    os.system("clear")
    while True:
        print(f"{CYAN}{logo}{RESET}")
        print(f"{DIM}Select a version:{RESET}\n")
        for key, (label, _) in VERSIONS.items():
            print(f"  [{key}] {label}")
        print("  [q] Quit\n")

        choice = input("> ").strip().lower()
        if choice == "q":
            break
        if choice in VERSIONS:
            _, path = VERSIONS[choice]
            subprocess.run([sys.executable, os.path.join(HERE, path)])
            os.system("clear")
        else:
            print(f"{RED}✗  Invalid choice.{RESET}")


if __name__ == "__main__":
    main()
