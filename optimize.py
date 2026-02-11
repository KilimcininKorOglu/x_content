#!/usr/bin/env python3
"""X Algorithm Tweet Optimizer - CLI Entry Point.

Two-phase interactive flow:
  Phase 1: Optimize tweet preserving original style/voice
  Phase 2: (Optional) Generate different style variations

Usage:
  python optimize.py "Tweet text here"
  python optimize.py "Tweet text" --topic "AI" --style provocative
  python optimize.py --file draft.txt --lang tr --thread
  python optimize.py "Tweet text" --no-interactive --variations 5
"""

import argparse
import platform
import subprocess
import sys

from x_content.optimizer import optimize, optimize_preserve_style, refine_tweet, OptimizationError
from x_content.display import render_preserve_style, render_variations, render_json


# ANSI helpers for interactive prompts
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
WHITE = "\033[97m"
GRAY = "\033[90m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_GREEN = "\033[92m"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Optimize tweets for maximum X algorithm reach",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python optimize.py "AI will replace 80%% of jobs"\n'
            '  python optimize.py "Test tweet" --topic "AI" --variations 5\n'
            '  python optimize.py --file draft.txt --lang tr --thread\n'
        ),
    )

    parser.add_argument(
        "tweet",
        nargs="?",
        help="Tweet text to optimize",
    )
    parser.add_argument(
        "--topic",
        help="Topic/niche context (e.g., 'AI', 'startups')",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "tr", "auto"],
        default="auto",
        help="Language: en, tr, or auto (default: auto)",
    )
    parser.add_argument(
        "--variations",
        type=int,
        default=3,
        help="Number of style variations for Phase 2 (default: 3)",
    )
    parser.add_argument(
        "--style",
        choices=["professional", "casual", "provocative", "educational"],
        default="professional",
        help="Tone style for Phase 2 variations (default: professional)",
    )
    parser.add_argument(
        "--media",
        action="store_true",
        help="Tweet will include media (photo/video)",
    )
    parser.add_argument(
        "--thread",
        action="store_true",
        help="Optimize for thread format",
    )
    parser.add_argument(
        "--file",
        help="Read tweet from file instead of positional arg",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON (non-interactive)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed algorithm analysis",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        dest="no_interactive",
        help="Skip interactive prompts, show all variations directly",
    )

    return parser


def copy_to_clipboard(text: str) -> tuple[bool, str]:
    """Copy text to system clipboard. Returns (success, error_message)."""
    system = platform.system()
    try:
        if system == "Darwin":
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
            if proc.returncode == 0:
                return True, ""
            return False, "pbcopy failed"
        elif system == "Linux":
            tools = [
                (["xclip", "-selection", "clipboard"], "xclip"),
                (["xsel", "--clipboard", "--input"], "xsel"),
            ]
            missingTools = []
            for cmd, name in tools:
                try:
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    proc.communicate(text.encode("utf-8"))
                    if proc.returncode == 0:
                        return True, ""
                except FileNotFoundError:
                    missingTools.append(name)
                    continue
            if len(missingTools) == len(tools):
                return False, f"Install xclip or xsel: sudo apt install xclip"
            return False, "Clipboard command failed"
        elif system == "Windows":
            proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-16le"))
            if proc.returncode == 0:
                return True, ""
            return False, "clip command failed"
    except Exception as e:
        return False, str(e)
    return False, f"Unsupported platform: {system}"


def prompt_choice(question: str, options: list[str]) -> str:
    """Show an interactive menu and return the chosen option key."""
    print(f"\n  {BOLD}{WHITE}{question}{RESET}")
    for i, opt in enumerate(options, 1):
        print(f"    {BRIGHT_CYAN}[{i}]{RESET} {opt}")
    print()

    while True:
        try:
            raw = input(f"  {GRAY}Select (1-{len(options)}): {RESET}").strip()
            if not raw:
                return "1"  # default to first option
            idx = int(raw)
            if 1 <= idx <= len(options):
                return str(idx)
        except (ValueError, EOFError):
            pass
        print(f"  {DIM}Please enter a number between 1 and {len(options)}{RESET}")


def interactive_flow(args):
    """Run the two-phase interactive optimization flow."""
    original_tweet = args.tweet

    # ═══════════════════════════════════════════════════════════
    #  PHASE 1: Preserve-style optimization
    # ═══════════════════════════════════════════════════════════
    print(f"\n  {BOLD}{BRIGHT_CYAN}Optimizing tweet...{RESET}\n")

    try:
        result = optimize_preserve_style(
            tweet=original_tweet,
            topic=args.topic,
            lang=args.lang,
            has_media=args.media,
            thread=args.thread,
        )
    except OptimizationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Show Phase 1 result
    print(render_preserve_style(result))

    optimized_tweet = result["optimized"].get("tweet", "")
    detected_lang = result.get("lang", args.lang)

    # ═══════════════════════════════════════════════════════════
    #  Interactive Menu (loop)
    # ═══════════════════════════════════════════════════════════
    _interactive_menu(args, original_tweet, optimized_tweet, detected_lang)


def _interactive_menu(args, original_tweet: str, current_tweet: str, lang: str):
    """Show the interactive menu in a loop. Supports refine iterations."""
    while True:
        choice = prompt_choice(
            "What would you like to do?",
            [
                f"{GREEN}Copy optimized tweet to clipboard{RESET}",
                f"{CYAN}Refine with AI (request changes){RESET}",
                f"{MAGENTA}Generate different style variations{RESET}",
                f"{YELLOW}Copy original tweet to clipboard{RESET}",
                f"{DIM}Exit{RESET}",
            ],
        )

        if choice == "1":
            # Copy optimized tweet
            success, errMsg = copy_to_clipboard(current_tweet)
            if success:
                print(f"\n  {GREEN}{BOLD}Copied to clipboard!{RESET}\n")
            else:
                print(f"\n  {YELLOW}Could not access clipboard ({errMsg}). Here's the tweet to copy:{RESET}\n")
                print(f"  {current_tweet}\n")

        elif choice == "2":
            # Refine with AI
            current_tweet = _refine_loop(args, original_tweet, current_tweet, lang)

        elif choice == "3":
            # Different style variations
            _run_phase2(args, original_tweet)
            return

        elif choice == "4":
            # Copy original
            success, errMsg = copy_to_clipboard(original_tweet)
            if success:
                print(f"\n  {GREEN}{BOLD}Copied original to clipboard!{RESET}\n")
            else:
                print(f"\n  {YELLOW}Could not access clipboard ({errMsg}).{RESET}\n")

        else:
            print(f"\n  {DIM}Done.{RESET}\n")
            return


def _refine_loop(args, original_tweet: str, current_tweet: str, lang: str) -> str:
    """Ask user for feedback, send to AI, show result. Returns the latest tweet."""
    print(f"\n  {BOLD}{WHITE}What would you like to change?{RESET}")
    print(f"  {GRAY}(Type your instructions, e.g. 'make it shorter', 'keep the URL', 'add humor'){RESET}\n")

    try:
        feedback = input(f"  {BRIGHT_CYAN}> {RESET}").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return current_tweet

    if not feedback:
        print(f"  {DIM}No changes requested.{RESET}")
        return current_tweet

    print(f"\n  {BOLD}{BRIGHT_CYAN}Refining tweet...{RESET}\n")

    try:
        result = refine_tweet(
            original_tweet=original_tweet,
            current_tweet=current_tweet,
            user_feedback=feedback,
            lang=lang,
            has_media=args.media,
            thread=args.thread,
        )
    except OptimizationError as e:
        print(f"  {YELLOW}Refinement failed: {e}{RESET}\n")
        return current_tweet

    # Show the refined result
    print(render_preserve_style(result))

    return result["optimized"].get("tweet", current_tweet)


def _run_phase2(args, tweet: str):
    """Run Phase 2: generate different style variations."""
    print(f"\n  {BOLD}{BRIGHT_CYAN}Generating {args.variations} style variations...{RESET}\n")

    try:
        result = optimize(
            tweet=tweet,
            topic=args.topic,
            lang=args.lang,
            variations=args.variations,
            style=args.style,
            has_media=args.media,
            thread=args.thread,
        )
    except OptimizationError as e:
        print(f"Error: {e}", file=sys.stderr)
        return

    # Show variations
    print(render_variations(result, verbose=args.verbose))

    # Ask which one to copy
    num_vars = len(result["variations"])
    options = [
        f"Copy variation #{i+1} to clipboard"
        for i in range(num_vars)
    ]
    options.append(f"{DIM}Done{RESET}")

    choice = prompt_choice("Which tweet would you like to copy?", options)

    try:
        idx = int(choice) - 1
        if 0 <= idx < num_vars:
            var_tweet = result["variations"][idx].get("tweet", "")
            success, errMsg = copy_to_clipboard(var_tweet)
            if success:
                print(f"\n  {GREEN}{BOLD}Variation #{idx+1} copied to clipboard!{RESET}\n")
            else:
                print(f"\n  {YELLOW}Could not access clipboard ({errMsg}). Here's the tweet:{RESET}\n")
                print(f"  {var_tweet}\n")
        else:
            print(f"\n  {DIM}Done.{RESET}\n")
    except (ValueError, IndexError):
        print(f"\n  {DIM}Done.{RESET}\n")


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Get tweet text
    tweet = args.tweet
    if args.file:
        try:
            with open(args.file) as f:
                tweet = f.read().strip()
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)

    if not tweet:
        print("Error: Tweet text cannot be empty.", file=sys.stderr)
        sys.exit(1)

    if not tweet.strip():
        print("Error: Tweet text cannot be empty or whitespace only.", file=sys.stderr)
        sys.exit(1)

    args.tweet = tweet

    # JSON output mode (non-interactive)
    if args.json_output:
        try:
            result = optimize(
                tweet=tweet,
                topic=args.topic,
                lang=args.lang,
                variations=args.variations,
                style=args.style,
                has_media=args.media,
                thread=args.thread,
            )
        except OptimizationError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        print(render_json(result))
        return

    # Non-interactive mode (legacy behavior)
    if args.no_interactive:
        try:
            result = optimize(
                tweet=tweet,
                topic=args.topic,
                lang=args.lang,
                variations=args.variations,
                style=args.style,
                has_media=args.media,
                thread=args.thread,
            )
        except OptimizationError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        print(render_variations(result, verbose=args.verbose))
        return

    # Interactive mode (default)
    interactive_flow(args)


if __name__ == "__main__":
    main()
