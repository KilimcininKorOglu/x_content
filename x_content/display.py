"""Terminal output formatting.

Renders signal comparisons, category bars, and summary tables.
Uses ANSI colors, dynamic terminal width, and clean formatting
that makes tweet text easily copyable.
"""

import shutil
import textwrap

from x_content.algorithm import ACTIONS, ACTION_LABELS, NEGATIVE_ACTIONS
from x_content import config


# ── ANSI Color Codes ──────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[97m"
GRAY = "\033[90m"

# Bright variants
BRIGHT_CYAN = "\033[96m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_RED = "\033[91m"
BRIGHT_MAGENTA = "\033[95m"

# Background
BG_DARK = "\033[48;5;234m"
BG_DARKER = "\033[48;5;232m"

# ── Box Drawing Characters ────────────────────────────────────────
H_LINE = "\u2500"       # ─
BLOCK_FULL = "\u2588"   # █
BLOCK_MED = "\u2593"    # ▓
BLOCK_LIGHT = "\u2591"  # ░
ARROW_RIGHT = "\u2192"  # →
ARROW_UP = "\u25b2"     # ▲
ARROW_DOWN = "\u25bc"   # ▼
BULLET = "\u2022"       # •
CHECK = "\u2713"        # ✓
CROSS = "\u2717"        # ✗


def _get_width() -> int:
    """Get terminal width, with a sensible fallback."""
    try:
        cols = shutil.get_terminal_size().columns
        return min(max(cols, 60), 120)
    except Exception:
        return 80


def _bar(value: float, width: int = 20) -> str:
    """Render a colored progress bar."""
    cfg_width = config.get("display", {}).get("bar_width", width)
    filled = int(value * cfg_width)
    empty = cfg_width - filled

    if value >= 0.7:
        color = GREEN
    elif value >= 0.4:
        color = YELLOW
    else:
        color = DIM

    return f"{color}{BLOCK_FULL * filled}{GRAY}{BLOCK_LIGHT * empty}{RESET}"


def _bar_negative(value: float, width: int = 20) -> str:
    """Render a progress bar for negative signals (lower is better)."""
    cfg_width = config.get("display", {}).get("bar_width", width)
    filled = int(value * cfg_width)
    empty = cfg_width - filled

    if value <= 0.05:
        color = GREEN
    elif value <= 0.15:
        color = YELLOW
    else:
        color = RED

    return f"{color}{BLOCK_FULL * filled}{GRAY}{BLOCK_LIGHT * empty}{RESET}"


def _change_arrows(delta_pct: float, is_negative: bool = False) -> str:
    """Render colored change arrows."""
    if is_negative:
        if delta_pct <= -50:
            return f"{GREEN}{ARROW_DOWN}{ARROW_DOWN} improved{RESET}"
        elif delta_pct < 0:
            return f"{GREEN}{ARROW_DOWN} improved{RESET}"
        elif delta_pct > 50:
            return f"{RED}{ARROW_UP}{ARROW_UP} worse{RESET}"
        elif delta_pct > 0:
            return f"{RED}{ARROW_UP} worse{RESET}"
        return ""
    else:
        abs_d = abs(delta_pct)
        if abs_d >= 300:
            arrows = ARROW_UP * 4 if delta_pct > 0 else ARROW_DOWN * 4
        elif abs_d >= 100:
            arrows = ARROW_UP * 3 if delta_pct > 0 else ARROW_DOWN * 3
        elif abs_d >= 50:
            arrows = ARROW_UP * 2 if delta_pct > 0 else ARROW_DOWN * 2
        elif abs_d > 0:
            arrows = ARROW_UP if delta_pct > 0 else ARROW_DOWN
        else:
            return ""
        color = GREEN if delta_pct > 0 else RED
        return f"{color}{arrows}{RESET}"


def _header_line(text: str, width: int) -> str:
    """Create a styled header line."""
    pad = width - len(text) - 4
    return f"{BOLD}{CYAN}{'─' * 2} {text} {'─' * max(pad, 0)}{RESET}"


def _section_title(text: str) -> str:
    """Create a section title."""
    return f"\n  {BOLD}{WHITE}{text}{RESET}"


def _divider(width: int) -> str:
    """Create a subtle divider."""
    return f"  {GRAY}{'─' * (width - 4)}{RESET}"


def _wrap_text(text: str, width: int, indent: int = 4) -> list[str]:
    """Wrap text to fit terminal width."""
    lines = []
    for line in text.split("\n"):
        if len(line) + indent <= width:
            lines.append(line)
        else:
            wrapped = textwrap.wrap(line, width=width - indent - 2)
            lines.extend(wrapped)
    return lines


# ═══════════════════════════════════════════════════════════════════
#  PHASE 1: Preserve-style result display
# ═══════════════════════════════════════════════════════════════════

def render_preserve_style(result: dict) -> str:
    """Render Phase 1 result: original vs same-style optimized tweet."""
    w = _get_width()
    parts = []

    # Header
    parts.append("")
    parts.append(f"  {BOLD}{BRIGHT_CYAN}╔{'═' * (w - 6)}╗{RESET}")
    parts.append(f"  {BOLD}{BRIGHT_CYAN}║  {WHITE}X ALGORITHM TWEET OPTIMIZER{' ' * (w - 33)}║{RESET}")
    parts.append(f"  {BOLD}{BRIGHT_CYAN}╚{'═' * (w - 6)}╝{RESET}")
    parts.append("")

    tweet = result["tweet"]
    analysis = result["analysis"]
    report = result["original_report"]
    optimized = result["optimized"]
    comparison = result["comparison"]

    orig_overall = report["overall"]
    opt_overall = comparison["optimized"]["overall"] if comparison else 0
    change = comparison["overall_change"] if comparison else 0
    change_str = f"+{change:.0f}" if change >= 0 else f"{change:.0f}"

    # ── Original Tweet ──
    parts.append(_header_line("ORIGINAL TWEET", w))
    parts.append("")

    # Show tweet text cleanly (no box decorations)
    parts.append(f"  {DIM}{ITALIC}")
    for line in _wrap_text(tweet, w):
        parts.append(f"    {line}")
    parts.append(f"  {RESET}")
    parts.append("")

    chars = analysis["char_count"]
    lang_str = analysis["lang"].upper()
    char_color = RED if chars > 280 else GREEN
    parts.append(f"  {GRAY}Characters: {char_color}{chars}/280{RESET}  {GRAY}│  Lang: {CYAN}{lang_str}{RESET}  {GRAY}│  Score: {YELLOW}{orig_overall:.0f}%{RESET}")

    # ── Signal Profile (compact) ──
    parts.append("")
    parts.append(_section_title("Signal Profile"))
    parts.append(_divider(w))

    display_cfg = config.get("display", {})
    show_all = display_cfg.get("show_all_signals", False)
    top_n = display_cfg.get("top_signals_count", 8)

    signals = report["signals"]
    if show_all:
        display_actions = ACTIONS
    else:
        scored = []
        for a in ACTIONS:
            if a in NEGATIVE_ACTIONS:
                scored.append((a, 999))
            else:
                scored.append((a, signals.get(a, 0.0)))
        scored.sort(key=lambda x: -x[1])
        display_actions = [a for a, _ in scored[:top_n]]

    for action in display_actions:
        val = signals.get(action, 0.0)
        is_neg = action in NEGATIVE_ACTIONS
        bar = _bar_negative(val) if is_neg else _bar(val)
        risk_label = f"  {RED}risk{RESET}" if is_neg else ""
        name = ACTION_LABELS.get(action, action)
        parts.append(f"    {GRAY}{name:<22}{RESET} {bar} {val:>4.0%}{risk_label}")

    # ── Optimized Tweet ──
    parts.append("")
    parts.append("")
    score_color = GREEN if change > 0 else RED if change < 0 else YELLOW
    parts.append(_header_line(f"OPTIMIZED TWEET  {score_color}{orig_overall:.0f}% {ARROW_RIGHT} {opt_overall:.0f}% ({change_str}pts){RESET}", w + 20))
    parts.append("")

    opt_tweet = optimized.get("tweet", "")
    opt_chars = optimized.get("char_count", len(opt_tweet))

    # Show the optimized tweet in a clean, copyable format
    parts.append(f"  {BOLD}{WHITE}")
    for line in _wrap_text(opt_tweet, w):
        parts.append(f"    {line}")
    parts.append(f"  {RESET}")
    parts.append("")

    char_color = RED if opt_chars > 280 else GREEN
    parts.append(f"  {GRAY}Characters: {char_color}{opt_chars}/280{RESET}")

    # ── What Changed ──
    explanation = optimized.get("explanation", "")
    if explanation:
        parts.append("")
        parts.append(f"  {GRAY}{ITALIC}What changed: {explanation}{RESET}")

    # ── Signal Changes (top improvements) ──
    if comparison:
        parts.append("")
        parts.append(_section_title("Signal Changes"))
        parts.append(_divider(w))

        delta = comparison["delta"]
        sorted_actions = sorted(
            ACTIONS,
            key=lambda a: abs(delta[a]["delta_pct"]),
            reverse=True,
        )
        display_delta_actions = sorted_actions[:top_n]

        for action in display_delta_actions:
            d = delta[action]
            is_neg = action in NEGATIVE_ACTIONS
            orig_pct = d["original"]
            opt_pct = d["optimized"]
            dpct = d["delta_pct"]
            arrows = _change_arrows(dpct, is_neg)
            sign = "+" if dpct >= 0 else ""
            name = ACTION_LABELS.get(action, action)
            parts.append(
                f"    {GRAY}{name:<22}{RESET} {orig_pct:>3.0%} {ARROW_RIGHT} {opt_pct:>3.0%}  {sign}{dpct:.1f}%  {arrows}"
            )

        # ── Category Scores ──
        parts.append("")
        parts.append(_section_title("Category Scores"))
        parts.append(_divider(w))

        cat_delta = comparison["category_delta"]
        cat_order = ["engagement", "discoverability", "shareability",
                     "content_quality", "safety"]
        for cat in cat_order:
            if cat in cat_delta:
                cd = cat_delta[cat]
                opt_val = cd["optimized"]
                ch = cd["change"]
                bar = _bar(opt_val / 100.0, 20)
                sign = "+" if ch >= 0 else ""
                cat_label = cat.replace("_", " ").title()
                ch_color = GREEN if ch > 0 else RED if ch < 0 else GRAY
                parts.append(
                    f"    {GRAY}{cat_label:<20}{RESET} {bar} {opt_val:>3.0f}%  {ch_color}({sign}{ch:.0f}pts){RESET}"
                )

    # Media suggestion
    media_sug = optimized.get("media_suggestion", "")
    if media_sug:
        parts.append("")
        parts.append(f"  {MAGENTA}{BULLET} Media tip:{RESET} {DIM}{media_sug}{RESET}")

    # Analysis
    claude_analysis = result.get("claude_analysis", "")
    if claude_analysis:
        parts.append("")
        parts.append(_section_title("Analysis"))
        parts.append(_divider(w))
        for line in _wrap_text(claude_analysis, w - 4):
            parts.append(f"    {DIM}{line}{RESET}")

    parts.append("")
    parts.append(f"  {GRAY}{'─' * (w - 4)}{RESET}")
    parts.append("")

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PHASE 2: Different style variations display
# ═══════════════════════════════════════════════════════════════════

def render_variation_card(
    index: int,
    variation: dict,
    comparison: dict | None,
    verbose: bool = False,
) -> str:
    """Render a single variation as a clean card."""
    w = _get_width()
    parts = []

    tweet = variation.get("tweet", "")
    strategy = variation.get("strategy", "")
    char_count = variation.get("char_count", len(tweet))
    media_sug = variation.get("media_suggestion", "")
    explanation = variation.get("explanation", "")

    opt_overall = 0.0
    overall_change = 0.0
    if comparison:
        opt_overall = comparison["optimized"]["overall"]
        overall_change = comparison["overall_change"]

    change_str = f"+{overall_change:.0f}" if overall_change >= 0 else f"{overall_change:.0f}"
    change_color = GREEN if overall_change > 0 else RED if overall_change < 0 else GRAY

    # Card header
    parts.append("")
    parts.append(f"  {BOLD}{BRIGHT_MAGENTA}[{index}]{RESET} {BOLD}{WHITE}{strategy}{RESET}  {change_color}{opt_overall:.0f}% ({change_str}pts){RESET}")
    parts.append(_divider(w))
    parts.append("")

    # Tweet text — clean and copyable
    parts.append(f"  {BOLD}{WHITE}")
    for line in _wrap_text(tweet, w):
        parts.append(f"    {line}")
    parts.append(f"  {RESET}")
    parts.append("")

    char_color = RED if char_count > 280 else GREEN
    parts.append(f"  {GRAY}Characters: {char_color}{char_count}/280{RESET}")

    if explanation:
        parts.append(f"  {GRAY}{ITALIC}{explanation}{RESET}")

    # Signal changes (compact - top 5)
    if comparison:
        parts.append("")
        delta = comparison["delta"]
        sorted_actions = sorted(
            ACTIONS,
            key=lambda a: abs(delta[a]["delta_pct"]),
            reverse=True,
        )

        for action in sorted_actions[:5]:
            d = delta[action]
            is_neg = action in NEGATIVE_ACTIONS
            orig_pct = d["original"]
            opt_pct = d["optimized"]
            dpct = d["delta_pct"]
            arrows = _change_arrows(dpct, is_neg)
            sign = "+" if dpct >= 0 else ""
            name = ACTION_LABELS.get(action, action)
            parts.append(
                f"    {GRAY}{name:<22}{RESET} {orig_pct:>3.0%} {ARROW_RIGHT} {opt_pct:>3.0%}  {sign}{dpct:.1f}%  {arrows}"
            )

        # Category scores (compact single line)
        cat_delta = comparison["category_delta"]
        cat_parts = []
        for cat in ["engagement", "discoverability", "shareability", "content_quality", "safety"]:
            if cat in cat_delta:
                cd = cat_delta[cat]
                ch = cd["change"]
                sign = "+" if ch >= 0 else ""
                color = GREEN if ch > 0 else RED if ch < 0 else GRAY
                short_name = cat.replace("_", " ").title()[:12]
                cat_parts.append(f"{color}{short_name}: {sign}{ch:.0f}{RESET}")
        parts.append("")
        parts.append(f"    {GRAY}Categories:{RESET} {'  '.join(cat_parts)}")

    if media_sug:
        parts.append(f"    {MAGENTA}{BULLET} Media:{RESET} {DIM}{media_sug[:60]}{'...' if len(media_sug) > 60 else ''}{RESET}")

    parts.append("")
    return "\n".join(parts)


def render_variations(result: dict, verbose: bool = False) -> str:
    """Render Phase 2: all style variations."""
    w = _get_width()
    parts = []

    parts.append("")
    parts.append(f"  {BOLD}{BRIGHT_CYAN}╔{'═' * (w - 6)}╗{RESET}")
    parts.append(f"  {BOLD}{BRIGHT_CYAN}║  {WHITE}STYLE VARIATIONS{' ' * (w - 22)}║{RESET}")
    parts.append(f"  {BOLD}{BRIGHT_CYAN}╚{'═' * (w - 6)}╝{RESET}")

    for i, (var, comp) in enumerate(
        zip(result["variations"], result["comparisons"]), 1
    ):
        parts.append(render_variation_card(i, var, comp, verbose=verbose))

    # Summary comparison table
    parts.append(_header_line("SUMMARY", w))
    parts.append("")

    original_overall = result["original_report"]["overall"]
    parts.append(f"    {GRAY}{'Tweet':<8} {'Strategy':<28} {'Score':>6}  {'Change':>8}{RESET}")
    parts.append(f"    {GRAY}{'─' * 54}{RESET}")
    parts.append(f"    {DIM}{'Original':<8} {'-':<28} {original_overall:>5.0f}%  {'-':>8}{RESET}")

    for i, (var, comp) in enumerate(zip(result["variations"], result["comparisons"]), 1):
        strategy = var.get("strategy", "")[:26]
        if comp:
            opt_score = comp["optimized"]["overall"]
            ch = comp["overall_change"]
            sign = "+" if ch >= 0 else ""
            ch_color = GREEN if ch > 0 else RED if ch < 0 else GRAY
            parts.append(
                f"    {BRIGHT_MAGENTA}#{i:<7}{RESET} {WHITE}{strategy:<28}{RESET} {opt_score:>5.0f}%  {ch_color}{sign}{ch:.0f}pts{RESET}"
            )
        else:
            parts.append(f"    {BRIGHT_MAGENTA}#{i:<7}{RESET} {strategy:<28}   {'N/A':>5}  {'N/A':>8}")

    # Analysis
    if result.get("claude_analysis"):
        parts.append("")
        parts.append(f"  {GRAY}{ITALIC}Analysis: {result['claude_analysis']}{RESET}")

    parts.append("")
    parts.append(f"  {GRAY}{'─' * (w - 4)}{RESET}")
    parts.append("")

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  Legacy: Full render (backwards compatible for --json mode)
# ═══════════════════════════════════════════════════════════════════

def render_full(result: dict, verbose: bool = False) -> str:
    """Render the complete optimization result (legacy full output)."""
    return render_variations(result, verbose=verbose)


def render_json(result: dict) -> str:
    """Render result as JSON string."""
    import json
    output = {
        "original": {
            "tweet": result["tweet"],
            "char_count": result["analysis"]["char_count"],
            "lang": result["lang"],
            "scores": result["original_report"]["signals"],
            "categories": result["original_report"]["categories"],
            "overall_score": result["original_report"]["overall"],
        },
        "variations": [],
        "analysis": result.get("claude_analysis", ""),
    }

    for var, comp in zip(result["variations"], result["comparisons"]):
        v = {
            "tweet": var.get("tweet", ""),
            "strategy": var.get("strategy", ""),
            "char_count": var.get("char_count", 0),
            "targeted_signals": var.get("targeted_signals", []),
            "scores": var.get("scores", {}),
            "media_suggestion": var.get("media_suggestion", ""),
            "explanation": var.get("explanation", ""),
        }
        if comp:
            v["overall_score"] = comp["optimized"]["overall"]
            v["overall_change"] = comp["overall_change"]
            v["category_scores"] = {
                k: round(v2 * 100, 1)
                for k, v2 in comp["optimized"]["categories"].items()
            }
        output["variations"].append(v)

    return json.dumps(output, indent=2, ensure_ascii=False)
