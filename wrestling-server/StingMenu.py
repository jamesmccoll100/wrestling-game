import curses
import subprocess
import pygame
import os
import json
import time
import math
import random

# =============================================================================
#  CINEMATIC INTRO
# =============================================================================

def _ip(n):
    return curses.color_pair(n)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS  — use addstr throughout, never addch, so Unicode chars work
# ─────────────────────────────────────────────────────────────────────────────

def _put(stdscr, y, x, ch, attr):
    h, w = stdscr.getmaxyx()
    if 0 <= y < h and 0 <= x < w - 1:
        try:
            stdscr.addstr(y, x, ch, attr)
        except curses.error:
            pass

def _puts(stdscr, y, x, s, attr):
    h, w = stdscr.getmaxyx()
    if 0 <= y < h and 0 <= x < w:
        try:
            stdscr.addstr(y, max(0, x), s[:max(0, w - x - 1)], attr)
        except curses.error:
            pass

def _fill_row(stdscr, y, ch, attr):
    h, w = stdscr.getmaxyx()
    if 0 <= y < h:
        try:
            stdscr.addstr(y, 0, (ch * w)[:w - 1], attr)
        except curses.error:
            pass

def _fill_screen(stdscr, ch, attr):
    h, w = stdscr.getmaxyx()
    for y in range(h):
        _fill_row(stdscr, y, ch, attr)

def _wait_ms(stdscr, ms):
    """Wait ms milliseconds in chunks; return True if a key was pressed.
    Uses timeout(0) for non-blocking polls then restores timeout(-1)
    so the intro timing stays under napms control throughout."""
    waited = 0
    while waited < ms:
        curses.napms(min(50, ms - waited))
        waited += 50
        stdscr.timeout(0)
        k = stdscr.getch()
        stdscr.timeout(-1)
        if k != -1:
            return True
    return False

def _check_skip(stdscr):
    """Non-blocking key poll; preserves caller timeout state."""
    stdscr.timeout(0)
    k = stdscr.getch()
    stdscr.timeout(-1)
    return k != -1

# ─────────────────────────────────────────────────────────────────────────────
# TITLE TEXT — exactly matching what print_large_title uses in the menu
# ─────────────────────────────────────────────────────────────────────────────

_TITLE_BLOCK1 = [
    "██╗    ██╗██████╗ ███████╗███████╗████████╗██╗     ██╗███╗   ██╗ ██████╗",
    "██║    ██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██║     ██║████╗  ██║██╔════╝",
    "██║ █╗ ██║██████╔╝█████╗  ███████╗   ██║   ██║     ██║██╔██╗ ██║██║  ███╗",
    "██║███╗██║██╔══██╗██╔══╝  ╚════██║   ██║   ██║     ██║██║╚██╗██║██║   ██║",
    "╚███╔███╔╝██║  ██║███████╗███████║   ██║   ███████╗██║██║ ╚████║╚██████╔╝",
    " ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ",
    "                                                                         ",
    " █████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ",
    "██╔══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗",
    "███████║██████╔╝█████╗  ██╔██╗ ██║███████║",
    "██╔══██║██╔══██╗██╔══╝  ██║╚██╗██║██╔══██║",
    "██║  ██║██║  ██║███████╗██║ ╚████║██║  ██║",
    "╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝",
]

# The menu draws: subtitle at y=1, title block starts at y=3.
_MENU_TITLE_Y    = 3
_MENU_SUBTITLE_Y = 1
_SUBTITLE_TEXT   = "The Best There Ever Will Be"

def _draw_title_at(stdscr, y):
    """Draw the full WRESTLING ARENA ASCII block starting at row y."""
    h, w = stdscr.getmaxyx()
    for idx, line in enumerate(_TITLE_BLOCK1):
        lx = max(0, w // 2 - len(line) // 2)
        try:
            stdscr.addstr(y + idx, lx, line[:w - 1], _ip(16) | curses.A_BOLD)
        except curses.error:
            pass

def _draw_subtitle(stdscr, y, pair):
    """Draw the subtitle at row y in the given colour pair."""
    h, w = stdscr.getmaxyx()
    sx = max(0, w // 2 - len(_SUBTITLE_TEXT) // 2)
    _puts(stdscr, y, sx, _SUBTITLE_TEXT, _ip(pair) | curses.A_BOLD)

# ─────────────────────────────────────────────────────────────────────────────
# LIGHTNING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _make_bolt(h, w, start_x):
    pts = []
    x = start_x
    for y in range(h):
        pts.append((y, x))
        x += random.randint(-3, 3)
        x  = max(2, min(w - 4, x))
    return pts

def _draw_bolt(stdscr, pts, pair):
    attr = _ip(pair) | curses.A_BOLD
    for (y, x) in pts:
        _put(stdscr, y, x,     '|', attr)
        _put(stdscr, y, x - 1, '!', attr)
        _put(stdscr, y, x + 1, '!', attr)

def _strike_plain(stdscr, h, w, start_x, pair, draw_ms, linger_ms):
    """Build bolt downward, hold, clear. Returns True if skipped."""
    bolt = _make_bolt(h, w, start_x)
    for end in range(2, len(bolt) + 1, 2):
        stdscr.clear()
        _draw_bolt(stdscr, bolt[:end], pair)
        stdscr.refresh()
        curses.napms(draw_ms)
        if _check_skip(stdscr):
            return True
    stdscr.clear()
    _draw_bolt(stdscr, bolt, pair)
    stdscr.refresh()
    if _wait_ms(stdscr, linger_ms):
        return True
    stdscr.clear()
    stdscr.refresh()
    return False

def _strike_final(stdscr, h, w, start_x, pair, draw_ms):
    """White centre bolt → accelerating strobe → solid white-out."""
    bolt = _make_bolt(h, w, start_x)
    for end in range(2, len(bolt) + 1, 2):
        stdscr.clear()
        _draw_bolt(stdscr, bolt[:end], pair)
        stdscr.refresh()
        curses.napms(draw_ms)
        if _check_skip(stdscr):
            return True
    delays = [70, 55, 45, 35, 25, 20]
    for i, delay in enumerate(delays):
        stdscr.clear()
        if i % 2 == 0:
            _fill_screen(stdscr, 'X', _ip(45) | curses.A_BOLD)
        else:
            _draw_bolt(stdscr, bolt, pair)
        stdscr.refresh()
        curses.napms(delay)
        if _check_skip(stdscr):
            return True
    _fill_screen(stdscr, 'X', _ip(45) | curses.A_BOLD)
    stdscr.refresh()
    curses.napms(200)
    stdscr.clear()
    stdscr.refresh()
    return False

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 1 — LIGHTNING STRIKES (5 bolts on black screen)
# ─────────────────────────────────────────────────────────────────────────────

def scene_lightning_intro(stdscr):
    h, w = stdscr.getmaxyx()
    random.seed(13)
    stdscr.clear()
    stdscr.refresh()

    PINK  = 30   # RED for Sting's intro
    WHITE = 45

    left_x  = max(3, w * 22 // 100)
    right_x = max(3, min(w - 4, w * 75 // 100))
    mid_x   = w // 2

    plain_bolts = [
        (left_x,  PINK, 18, 280, 1500),
        (right_x, PINK, 14, 220, 1100),
        (left_x,  PINK, 10, 160,  800),
        (right_x, PINK,  7, 110,  600),
    ]

    for (sx, pair, draw_ms, linger_ms, gap_ms) in plain_bolts:
        if _strike_plain(stdscr, h, w, sx, pair, draw_ms, linger_ms):
            return
        if _wait_ms(stdscr, gap_ms):
            return

    _strike_final(stdscr, h, w, mid_x, WHITE, 5)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 2 — TITLE REVEAL
# ─────────────────────────────────────────────────────────────────────────────

def scene_title_reveal(stdscr):
    h, w = stdscr.getmaxyx()

    for cur_y in range(h, _MENU_TITLE_Y - 1, -2):
        stdscr.clear()
        _draw_title_at(stdscr, cur_y)
        stdscr.refresh()
        curses.napms(16)

    stdscr.clear()
    _draw_title_at(stdscr, _MENU_TITLE_Y)
    stdscr.refresh()
    curses.napms(400)

    sub_cycle = [30, 33, 32, 31, 44, 33, 30, 32, 31, 33]
    for pair in sub_cycle:
        stdscr.clear()
        _draw_title_at(stdscr, _MENU_TITLE_Y)
        _draw_subtitle(stdscr, _MENU_SUBTITLE_Y, pair)
        stdscr.refresh()
        curses.napms(110)

    stdscr.clear()
    _draw_title_at(stdscr, _MENU_TITLE_Y)
    _draw_subtitle(stdscr, _MENU_SUBTITLE_Y, 16)
    stdscr.refresh()
    curses.napms(800)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 3 — PRESS ENTER
# ─────────────────────────────────────────────────────────────────────────────

def scene_press_enter(stdscr):
    h, w = stdscr.getmaxyx()

    press   = ">>  PRESS  ENTER  TO  PLAY  <<"
    press_y = h - 4
    press_x = max(0, w // 2 - len(press) // 2)
    flash_s = [33, 31, 32, 31, 30, 31, 33, 16]

    stdscr.timeout(0)
    fi = elapsed = 0
    while elapsed < 30000:
        stdscr.clear()
        _draw_title_at(stdscr, _MENU_TITLE_Y)
        _draw_subtitle(stdscr, _MENU_SUBTITLE_Y, 16)
        pair = flash_s[fi % len(flash_s)]
        _puts(stdscr, press_y, press_x, press, _ip(pair) | curses.A_BOLD)
        stdscr.refresh()
        curses.napms(240)
        elapsed += 240
        fi += 1
        if stdscr.getch() != -1:
            break
    stdscr.timeout(-1)

# ─────────────────────────────────────────────────────────────────────────────
# SCENE 4 — MENU TRANSITION
# ─────────────────────────────────────────────────────────────────────────────

def scene_menu_transition(stdscr):
    h, w = stdscr.getmaxyx()
    random.seed(99)
    mid_x = w // 2
    _strike_final(stdscr, h, w, mid_x, 45, 4)
    stdscr.clear()
    _draw_title_at(stdscr, _MENU_TITLE_Y)
    _draw_subtitle(stdscr, _MENU_SUBTITLE_Y, 16)
    stdscr.refresh()
    curses.napms(60)
    stdscr.clear()
    stdscr.refresh()

# ─────────────────────────────────────────────────────────────────────────────
# MASTER INTRO
# ─────────────────────────────────────────────────────────────────────────────

def play_intro(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)

    stdscr.timeout(0)
    while stdscr.getch() != -1:
        pass

    stdscr.timeout(-1)
    scene_lightning_intro(stdscr)
    scene_title_reveal(stdscr)
    scene_press_enter(stdscr)
    scene_menu_transition(stdscr)
    stdscr.clear()
    stdscr.bkgd(' ', curses.color_pair(0))
    stdscr.timeout(200)
    curses.curs_set(0)


# =============================================================================
#  ORIGINAL GAME CODE
# =============================================================================

def get_sting_progress_path():
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), ".sting_progress.json")

def load_sting_high_scores():
    path = get_sting_progress_path()
    if not os.path.exists(path):
        return {"wins": 0, "losses": 0, "draws": 0}
    try:
        with open(path, "r") as f:
            data = json.load(f)
            if "wins" not in data:
                data["wins"] = 0
            if "losses" not in data:
                data["losses"] = 0
            if "draws" not in data:
                data["draws"] = 0
            return data
    except Exception:
        return {"wins": 0, "losses": 0, "draws": 0}

def display_match_record(stdscr):
    stats = load_sting_high_scores()

    current_row = 0
    color_flash = True

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        wins = stats.get("wins", 0)
        losses = stats.get("losses", 0)
        draws = stats.get("draws", 0)
        total_matches = wins + losses + draws
        win_percentage = (wins / total_matches * 100) if total_matches > 0 else 0

        box_width = 60
        box_height = 20
        box_x = (w - box_width) // 2
        box_y = (h - box_height) // 2

        stdscr.attron(curses.color_pair(16))
        for i in range(box_height):
            for j in range(box_width):
                if i == 0 or i == box_height - 1:
                    try:
                        stdscr.addch(box_y + i, box_x + j, curses.ACS_HLINE)
                    except curses.error:
                        pass
                elif j == 0 or j == box_width - 1:
                    try:
                        stdscr.addch(box_y + i, box_x + j, curses.ACS_VLINE)
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addch(box_y + i, box_x + j, ' ')
                    except curses.error:
                        pass
        try:
            stdscr.addch(box_y, box_x, curses.ACS_ULCORNER)
            stdscr.addch(box_y, box_x + box_width - 1, curses.ACS_URCORNER)
            stdscr.addch(box_y + box_height - 1, box_x, curses.ACS_LLCORNER)
            stdscr.addch(box_y + box_height - 1, box_x + box_width - 1, curses.ACS_LRCORNER)
        except curses.error:
            pass
        stdscr.attroff(curses.color_pair(16))

        title = " MATCH RECORD "
        try:
            stdscr.addstr(
                box_y,
                box_x + box_width // 2 - len(title) // 2,
                title,
                curses.color_pair(16)
            )
        except curses.error:
            pass

        total_text = f"Total Matches: {total_matches}"
        try:
            stdscr.addstr(box_y + 2, box_x + box_width // 2 - len(total_text) // 2, total_text, curses.color_pair(1))
        except curses.error:
            pass

        if total_matches > 0:
            percent_text = f"Win Rate: {win_percentage:.1f}%"
            try:
                stdscr.addstr(box_y + 3, box_x + box_width // 2 - len(percent_text) // 2, percent_text, curses.color_pair(1))
            except curses.error:
                pass

        sep_y = box_y + 4
        for j in range(1, box_width - 1):
            try:
                stdscr.addch(sep_y, box_x + j, curses.ACS_HLINE)
            except curses.error:
                pass

        col_y = sep_y + 2
        col_width = 18

        try:
            stdscr.addstr(col_y, box_x + 6 + col_width // 2 - 2, "WINS", curses.color_pair(20))
            stdscr.addstr(col_y + 2, box_x + 6 + col_width // 2, str(wins), curses.color_pair(20))
        except curses.error:
            pass

        mid_x = box_x + box_width // 2 - col_width // 2
        try:
            stdscr.addstr(col_y, mid_x + col_width // 2 - 4, "LOSSES", curses.color_pair(21))
            stdscr.addstr(col_y + 2, mid_x + col_width // 2, str(losses), curses.color_pair(21))
        except curses.error:
            pass

        right_x = box_x + box_width - col_width - 6
        try:
            stdscr.addstr(col_y, right_x + col_width // 2 - 3, "DRAWS", curses.color_pair(22))
            stdscr.addstr(col_y + 2, right_x + col_width // 2, str(draws), curses.color_pair(22))
        except curses.error:
            pass

        for i in range(col_y, col_y + 5):
            try:
                stdscr.addch(i, box_x + 24, curses.ACS_VLINE)
                stdscr.addch(i, box_x + 36, curses.ACS_VLINE)
            except curses.error:
                pass

        option = "Back to Main Menu"
        opt_x = box_x + box_width // 2 - len(option) // 2
        opt_y = box_y + box_height - 3

        try:
            if color_flash:
                stdscr.attron(curses.color_pair(5))
                stdscr.addstr(opt_y, opt_x, option)
                stdscr.attroff(curses.color_pair(5))
            else:
                stdscr.attron(curses.color_pair(9))
                stdscr.addstr(opt_y, opt_x, option)
                stdscr.attroff(curses.color_pair(9))
        except curses.error:
            pass

        stdscr.refresh()
        color_flash = not color_flash

        key = stdscr.getch()
        if key in [27, curses.KEY_ENTER, 10, 13]:
            return

GREEN = '\033[32m'
MAGENTA = '\033[95m'
CYAN = '\033[94m'
YELLOW = '\033[33m'
RESET = '\033[0m'

def check_screen_size(stdscr, mode="menu"):
    h, w = stdscr.getmaxyx()

    if mode == "menu":
        min_width = 70
        min_height = 20
        message = "screen to small to display the menu"
    else:
        min_width = 36
        min_height = 20
        message = "screen to small to display stats"

    if w < min_width or h < min_height:
        stdscr.clear()
        x = max(0, w // 2 - len(message) // 2)
        y = max(0, h // 2)
        try:
            stdscr.addstr(y, x, message, curses.color_pair(1))
            stdscr.refresh()
        except curses.error:
            pass
        return False
    return True

def print_large_title(stdscr):
    if not check_screen_size(stdscr, "menu"):
        return

    title = [
        "██╗    ██╗██████╗ ███████╗███████╗████████╗██╗     ██╗███╗   ██╗ ██████╗",
        "██║    ██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██║     ██║████╗  ██║██╔════╝",
        "██║ █╗ ██║██████╔╝█████╗  ███████╗   ██║   ██║     ██║██╔██╗ ██║██║  ███╗",
        "██║███╗██║██╔══██╗██╔══╝  ╚════██║   ██║   ██║     ██║██║╚██╗██║██║   ██║",
        "╚███╔███╔╝██║  ██║███████╗███████║   ██║   ███████╗██║██║ ╚████║╚██████╔╝",
        " ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ",
        "                                                                         ",
        " █████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ",
        "██╔══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗",
        "███████║██████╔╝█████╗  ██╔██╗ ██║███████║",
        "██╔══██║██╔══██╗██╔══╝  ██║╚██╗██║██╔══██║",
        "██║  ██║██║  ██║███████╗██║ ╚████║██║  ██║",
        "╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝"
    ]

    subtitle = "The Best There Ever Will Be"

    h, w = stdscr.getmaxyx()

    subtitle_x = w // 2 - len(subtitle) // 2
    subtitle_y = 1
    try:
        stdscr.addstr(subtitle_y, subtitle_x, subtitle, curses.color_pair(16))
    except curses.error:
        pass

    title_start_y = subtitle_y + 2

    for idx, line in enumerate(title):
        x = w // 2 - len(line) // 2
        y = title_start_y + idx
        try:
            stdscr.addstr(y, x, line, curses.color_pair(16))
        except curses.error:
            pass

def print_menu(stdscr, selected_row_idx, color_flash, wins=0, tag_color_pair=None):
    stdscr.clear()

    if not check_screen_size(stdscr, "menu"):
        return

    h, w = stdscr.getmaxyx()

    menu = ["Challanger", "Match Record"]
    if wins >= 5:
        menu.append("Tag-Team Match")
    menu.append("Exit")

    total_items = len(menu)
    tag_team_unlocked = wins >= 5

    print_large_title(stdscr)

    select_text = "-Select Mode-"
    select_text_x = w // 2 - len(select_text) // 2
    select_text_y = h // 2 - total_items // 2 + 4
    try:
        stdscr.addstr(select_text_y, select_text_x, select_text, curses.color_pair(1))
    except curses.error:
        pass

    for idx, row in enumerate(menu):
        x = w // 2 - len(row) // 2
        y = h // 2 - total_items // 2 + idx + 6

        try:
            if idx == selected_row_idx:
                highlight_color = curses.color_pair(5) if color_flash else curses.color_pair(9)
                stdscr.attron(highlight_color)

                if row == "Tag-Team Match" and tag_color_pair:
                    display_text = f"* {row} *"
                    display_x = w // 2 - len(display_text) // 2

                    stdscr.attroff(highlight_color)
                    stdscr.attron(curses.color_pair(tag_color_pair))
                    stdscr.addch(y, display_x, '*')
                    stdscr.attroff(curses.color_pair(tag_color_pair))

                    stdscr.addch(y, display_x + 1, ' ')
                    stdscr.attron(highlight_color)
                    stdscr.addstr(y, display_x + 2, row)
                    stdscr.attroff(highlight_color)
                    stdscr.addch(y, display_x + 2 + len(row), ' ')

                    stdscr.attron(curses.color_pair(tag_color_pair))
                    stdscr.addch(y, display_x + len(display_text) - 1, '*')
                    stdscr.attroff(curses.color_pair(tag_color_pair))
                else:
                    stdscr.addstr(y, x, row)
                stdscr.attroff(highlight_color)
            else:
                if row == "Tag-Team Match" and tag_color_pair:
                    display_text = f"* {row} *"
                    display_x = w // 2 - len(display_text) // 2

                    stdscr.attron(curses.color_pair(tag_color_pair))
                    stdscr.addch(y, display_x, '*')
                    stdscr.attroff(curses.color_pair(tag_color_pair))

                    stdscr.addch(y, display_x + 1, ' ')

                    stdscr.attron(curses.color_pair(4))
                    stdscr.addstr(y, display_x + 2, row)
                    stdscr.attroff(curses.color_pair(4))

                    stdscr.addch(y, display_x + 2 + len(row), ' ')

                    stdscr.attron(curses.color_pair(tag_color_pair))
                    stdscr.addch(y, display_x + 2 + len(row) + 1, '*')
                    stdscr.attroff(curses.color_pair(tag_color_pair))
                else:
                    if row == "Challanger":
                        stdscr.attron(curses.color_pair(1))
                    elif row == "Match Record":
                        stdscr.attron(curses.color_pair(3))
                    elif row == "Exit":
                        stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(y, x, row)
                    if row in ["Challanger", "Match Record", "Exit"]:
                        stdscr.attroff(curses.color_pair(1) if row == "Challanger" or row == "Exit" else curses.color_pair(3))
        except curses.error:
            pass

    footer_lines = [
        "© JAMES MCCOLL. INC",
        "NORTH WEST. UK. 2026"
    ]

    footer_x = w - max(len(line) for line in footer_lines) - 1
    footer_y_start = h - len(footer_lines) - 1

    for i, line in enumerate(footer_lines):
        try:
            stdscr.addstr(footer_y_start + i, footer_x, line, curses.color_pair(1))
        except curses.error:
            pass

    stdscr.refresh()

    footer_x = w - max(len(line) for line in footer_lines) - 1
    footer_y_start = h - len(footer_lines) - 1

    for i, line in enumerate(footer_lines):
        try:
            stdscr.addstr(footer_y_start + i, footer_x, line, curses.color_pair(1))
        except curses.error:
            pass

    stdscr.refresh()

def display_loading_message(stdscr, message, color_pair):
    h, w = stdscr.getmaxyx()
    for i in range(3):
        stdscr.clear()
        stdscr.bkgd(' ', color_pair)
        x = w // 2 - len(message) // 2
        y = h // 2
        try:
            stdscr.addstr(y, x, message + '.' * (i + 1))
        except curses.error:
            pass
        stdscr.refresh()
        curses.napms(500)

def reset_background(stdscr):
    stdscr.bkgd(' ', curses.color_pair(0))
    stdscr.clear()
    stdscr.refresh()

def start_sting_game(stdscr):
    display_loading_message(stdscr, "Loading game", curses.color_pair(14))
    curses.endwin()
    subprocess.call(["python3", "WrestlingArena2NEW.py"])
    reset_background(stdscr)

def start_tag_team_game(stdscr):
    display_loading_message(stdscr, "Loading game", curses.color_pair(15))
    curses.endwin()
    subprocess.call(["python3", "WrestlingArena3.py"])
    reset_background(stdscr)

ascii_art = {
    "Sting": [
        " ██╗████████╗ ██╗ ███████╗              ",
        " ██║╚══██╔══╝ ██║ ██╔════╝              ",
        " ██║   ██║    ╚═╝ ███████╗              ",
        " ██║   ██║        ╚════██║              ",
        " ██║   ██║        ███████║              ",
        " ╚═╝   ╚═╝        ╚══════╝              ",
        "                                        ",
        " ███████╗████████╗██╗███╗   ██╗ ██████╗ ",
        " ██╔════╝╚══██╔══╝██║████╗  ██║██╔════╝ ",
        " ███████╗   ██║   ██║██╔██╗ ██║██║  ███╗",
        " ╚════██║   ██║   ██║██║╚██╗██║██║   ██║",
        " ███████║   ██║   ██║██║ ╚████║╚██████╔╝",
        " ╚══════╝   ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝ "
    ],
}

def print_ascii_art(stdscr, art_lines, art_color, box_x, box_y):
    h, w = stdscr.getmaxyx()
    art_start_x = box_x + 40 + 2
    art_start_y = box_y

    for idx, line in enumerate(art_lines):
        if art_start_y + idx >= h:
            break
        x = art_start_x
        if x + len(line) >= w:
            break
        try:
            stdscr.addstr(art_start_y + idx, x, line, art_color)
        except curses.error:
            pass

animation_frames = ["|", "/", "-", "\\"]

def display_stats_page(stdscr, wrestler):
    stats = {
        "Sting": """Nickname: The Icon
Height: 6'2"
Weight: 250lbs
Special Move: Scorpion Deathlock
Wrestling Profile:
Shrouded in mystery, Sting looms
on the fringe of the wrestling world.
He's the icon, the franchise and the
master of the Scorpion Deathlock;
It's showtime... it's Sting!""",
    }

    sting_color = curses.color_pair(18)   # RED — Sting's colour
    white_color = curses.color_pair(1)

    current_row = 0
    color_flash = True
    frame_count = 0

    stdscr.timeout(200)   # non-blocking getch — lets frame_count tick on its own

    while True:
        stdscr.clear()

        if not check_screen_size(stdscr, "stats"):
            key = stdscr.getch()
            if key == 27:
                return False
            continue

        h, w = stdscr.getmaxyx()

        box_width = 42
        box_height = 14
        art_lines = ascii_art[wrestler]
        max_line_length = max(len(line) for line in art_lines)
        total_width_needed = box_width + max_line_length + 2
        total_height_needed = max(box_height, len(art_lines))

        box_x = (w - total_width_needed) // 2
        box_y = (h - total_height_needed) // 2

        if wrestler == "Sting":
            box_color_pair = sting_color

        stdscr.attron(box_color_pair)
        for i in range(box_height):
            for j in range(box_width):
                if i == 0 or i == box_height - 1:
                    try:
                        stdscr.addch(box_y + i, box_x + j, curses.ACS_HLINE)
                    except curses.error:
                        pass
                elif j == 0 or j == box_width - 1:
                    try:
                        stdscr.addch(box_y + i, box_x + j, curses.ACS_VLINE)
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addch(box_y + i, box_x + j, ' ')
                    except curses.error:
                        pass

        try:
            stdscr.addch(box_y, box_x, curses.ACS_ULCORNER)
            stdscr.addch(box_y, box_x + box_width - 1, curses.ACS_URCORNER)
            stdscr.addch(box_y + box_height - 1, box_x, curses.ACS_LLCORNER)
            stdscr.addch(box_y + box_height - 1, box_x + box_width - 1, curses.ACS_LRCORNER)
        except curses.error:
            pass
        stdscr.attroff(box_color_pair)

        title = f" Challanger stats {animation_frames[frame_count % len(animation_frames)]}"
        title_x = w // 2 - len(title) // 2
        try:
            stdscr.addstr(box_y + 1, box_x + 1, title, curses.color_pair(16))
        except curses.error:
            pass

        lines = stats[wrestler].split('\n')
        for idx, line in enumerate(lines):
            x = box_x + 2
            y = box_y + 3 + idx
            parts = line.split(':', 1)
            if len(parts) == 2:
                label, text = parts
                try:
                    stdscr.addstr(y, x, label + ":", white_color)
                    stdscr.addstr(y, x + len(label) + 1, text, box_color_pair)
                except curses.error:
                    pass
            else:
                try:
                    stdscr.addstr(y, x, line, box_color_pair)
                except curses.error:
                    pass

        if wrestler == "Sting":
            art_color = sting_color

        print_ascii_art(stdscr, art_lines, art_color, box_x, box_y)

        menu = ["Continue", "Back to Main Menu"]
        menu_start_y = box_y + box_height + 1
        color_pairs = {
            0: (curses.color_pair(1), curses.color_pair(5) if color_flash else curses.color_pair(9)),
            1: (curses.color_pair(2), curses.color_pair(6) if color_flash else curses.color_pair(10)),
        }

        for idx, row in enumerate(menu):
            x = w // 2 - len(row) // 2
            y = menu_start_y + idx

            try:
                if idx == current_row:
                    stdscr.attron(color_pairs[idx][1])
                    stdscr.addstr(y, x, row)
                    stdscr.attroff(color_pairs[idx][1])
                else:
                    stdscr.attron(color_pairs[idx][0])
                    stdscr.addstr(y, x, row)
                    stdscr.attroff(color_pairs[idx][0])
            except curses.error:
                pass

        stdscr.refresh()

        key = stdscr.getch()
        color_flash = not color_flash
        frame_count += 1

        if key == curses.KEY_DOWN:
            current_row = (current_row + 1) % 2
        elif key == curses.KEY_UP:
            current_row = (current_row - 1) % 2
        elif key == curses.KEY_ENTER or key in [10, 13]:
            stdscr.timeout(200)
            return current_row == 0
        elif key == 27:
            stdscr.timeout(200)
            return False

def main(stdscr):
    curses.curs_set(0)

    # ── Enforce 90×30 inside curses ──────────────────────────────────────────
    # The resize escape was already sent before curses.wrapper() started, but
    # some terminals need a moment to apply it.  Sending it again via the curses
    # resizeterm call guarantees the internal LINES/COLS values match 90×30.
    curses.resizeterm(30, 90)
    stdscr.clear()
    stdscr.refresh()
    # ─────────────────────────────────────────────────────────────────────────

    stdscr.timeout(200)

    color_frame = 0
    tag_colors = [30, 31, 32, 33]

    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_YELLOW)
    curses.init_pair(10, curses.COLOR_WHITE, curses.COLOR_YELLOW)
    curses.init_pair(11, curses.COLOR_WHITE, curses.COLOR_YELLOW)
    curses.init_pair(12, curses.COLOR_WHITE, curses.COLOR_YELLOW)
    curses.init_pair(13, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
    curses.init_pair(14, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(15, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(16, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(17, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(18, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(19, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(20, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(21, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(22, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(30, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(31, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(32, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(33, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    # Intro background-fill pairs
    curses.init_pair(40, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(41, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(42, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(43, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
    curses.init_pair(44, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(45, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(46, curses.COLOR_BLACK, curses.COLOR_BLUE)
    curses.init_pair(47, curses.COLOR_WHITE, curses.COLOR_BLACK)

    # ── Play intro ──────────────────────────────────────────────────────────
    play_intro(stdscr)
    # ────────────────────────────────────────────────────────────────────────

    current_row = 0
    color_flash = True

    while True:
        stats = load_sting_high_scores()
        wins = stats.get("wins", 0)

        color_frame += 1
        tag_color_index = color_frame % len(tag_colors)

        print_menu(
            stdscr,
            current_row,
            color_flash,
            wins,
            tag_colors[tag_color_index] if wins >= 5 else None
        )

        key = stdscr.getch()
        color_flash = not color_flash

        if wins >= 5:
            menu_items = 4
            if key == curses.KEY_DOWN:
                current_row = (current_row + 1) % menu_items
            elif key == curses.KEY_UP:
                current_row = (current_row - 1) % menu_items
            elif key == curses.KEY_ENTER or key in [10, 13]:
                if current_row == 0:
                    if display_stats_page(stdscr, "Sting"):
                        start_sting_game(stdscr)
                elif current_row == 1:
                    display_match_record(stdscr)
                elif current_row == 2:
                    start_tag_team_game(stdscr)
                elif current_row == 3:
                    break
        else:
            menu_items = 3
            if key == curses.KEY_DOWN:
                current_row = (current_row + 1) % menu_items
            elif key == curses.KEY_UP:
                current_row = (current_row - 1) % menu_items
            elif key == curses.KEY_ENTER or key in [10, 13]:
                if current_row == 0:
                    if display_stats_page(stdscr, "Sting"):
                        start_sting_game(stdscr)
                elif current_row == 1:
                    display_match_record(stdscr)
                elif current_row == 2:
                    break

    curses.endwin()

if __name__ == "__main__":
    # Send the resize escape BEFORE curses starts so the terminal window
    # is already 90 cols × 30 rows when curses.wrapper() captures dimensions.
    # The sleep gives the terminal emulator time to apply the resize.
    os.system('printf "\\e[8;30;90t"')
    time.sleep(0.15)
    curses.wrapper(main)
