import random
import time
import sys
import os
import json

# ── Colours ──────────────────────────────────────────────────────────────────
CYAN    = '\033[96m'   # Player team
MAGENTA = '\033[95m'   # Bret Hart
RED     = '\033[91m'   # Sting
BLUE    = '\033[94m'   # Neutral / announcements
YELLOW  = '\033[33m'   # Special moves / combos
GREEN   = '\033[32m'   # Success messages
RESET   = '\033[0m'

# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def flush_input():
    try:
        if os.name == 'posix':
            import termios
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        else:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
    except Exception:
        pass

def print_slow(text, delay=0.04):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
        sys.stdout.flush()

def normalize_move(text):
    if not text:
        return ""
    return text.strip().lower().replace('-', '').replace('_', '').replace(' ', '')

# ─────────────────────────────────────────────────────────────────────────────
# SAVE / LOAD
# ─────────────────────────────────────────────────────────────────────────────

def save_tagteam_result(team_name, result, opponents="Bret Hart & Sting"):
    try:
        try:
            with open(".bret_progress.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"wins": 0, "losses": 0, "draws": 0, "matches": []}

        if result == "win":
            data["wins"] = data.get("wins", 0) + 1
        elif result == "loss":
            data["losses"] = data.get("losses", 0) + 1
        else:
            data["draws"] = data.get("draws", 0) + 1

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        match_record = {
            "date": timestamp,
            "team": team_name,
            "opponents": opponents,
            "result": result,
            "details": f"{team_name} vs {opponents}: {result.upper()}"
        }

        if "matches" not in data:
            data["matches"] = []
        data["matches"].append(match_record)
        if len(data["matches"]) > 50:
            data["matches"] = data["matches"][-50:]

        with open(".bret_progress.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving match result: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PIN / KICKOUT / ANNOUNCE
# ─────────────────────────────────────────────────────────────────────────────

def pin_attempt(pinned_health, is_dazed=False):
    """
    Returns True if the pin succeeds.
    Lower health = higher chance of staying down.
    Being dazed gives an extra 10 % success bonus.
    """
    fail_chance = 1.0 - (pinned_health / 100.0)
    fail_chance = max(0.0, min(1.0, fail_chance))
    if is_dazed:
        fail_chance = min(1.0, fail_chance * 1.1)

    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    return random.random() < fail_chance

def handle_kickout(wrestler_name, is_player_team):
    print("Kick out! The match continues!")
    colour = CYAN if is_player_team else (MAGENTA if "Bret" in wrestler_name else RED)
    print(colour + f"{wrestler_name} kicks out!" + RESET)
    return 25          # health restored after kickout

def announce_winner(team_name, player_wins):
    print("3... The match is over!")
    if player_wins:
        print_slow(GREEN + f"Congratulations, {team_name}! You have defeated the legends!" + RESET)
        print("\n" + BLUE + "===========================================")
        print(BLUE + f"{team_name} wins the match!" + RESET)
        print(BLUE + "===========================================" + RESET + "\n")
        save_tagteam_result(team_name, "win")
    else:
        print_slow(RED + f"Oh no! {team_name} has been defeated by the legends!" + RESET)
        print("\n" + BLUE + "===========================================")
        print(BLUE + f"{team_name} loses the match!" + RESET)
        print(BLUE + "===========================================" + RESET + "\n")
        save_tagteam_result(team_name, "loss")
    print_slow(YELLOW + "\nReturning to main menu in 5 seconds..." + RESET)
    time.sleep(5)

def announce_draw(team_name):
    print("\n" + BLUE + "===========================================")
    print(BLUE + "           The match ends in a DRAW!" + RESET)
    print(BLUE + "===========================================" + RESET + "\n")
    print_slow("Both teams are too exhausted to continue! The referee calls the match.")
    save_tagteam_result(team_name, "draw")
    print_slow(YELLOW + "\nReturning to main menu in 5 seconds..." + RESET)
    time.sleep(5)

# ─────────────────────────────────────────────────────────────────────────────
# OPPONENT AI MOVE SELECTION  (weighted, matches reference scripts)
# ─────────────────────────────────────────────────────────────────────────────

def opponent_choose_move(name, health, punches, kicks, backdrops, special_uses,
                         special_name, special_eligible):
    """
    Returns (move_name, damage).
    Mirrors the weighted AI from WrestlingArena.py.
    special_eligible: True only on the turn immediately after dropping below 30 HP.
    """
    possible_moves = []
    if special_uses > 0 and health <= 30 and special_eligible:
        possible_moves.append((special_name, 50))
    if backdrops > 0:
        possible_moves.append(('backdrop', 33))
    if kicks > 0:
        possible_moves.append(('kick', 25))
    if punches > 0:
        possible_moves.append(('punch', 15))

    if not possible_moves:
        return None, 0

    moves_list, weights = zip(*possible_moves)
    total = sum(weights)

    # 80 % of the time use the weighted picker; 20 % random
    if random.random() < 0.8:
        r = random.random() * total
        cumulative = 0
        chosen = moves_list[-1]
        for move, weight in zip(moves_list, weights):
            cumulative += weight
            if r <= cumulative:
                chosen = move
                break
    else:
        chosen = random.choice(moves_list)

    if chosen == 'punch':
        dmg = random.randint(8, 20)
    elif chosen == 'kick':
        dmg = random.randint(12, 35)
    elif chosen == 'backdrop':
        dmg = random.randint(18, 50)
    else:  # special
        dmg = random.randint(35, 60)

    return chosen, dmg

# ─────────────────────────────────────────────────────────────────────────────
# CLASH RESOLUTION  (full system from reference scripts)
# ─────────────────────────────────────────────────────────────────────────────

def resolve_clash(player_name, opponent_name, player_move, opponent_move,
                  player_damage, opponent_damage,
                  player_color, opponent_color):
    """
    Called when player and opponent pick the same move type.
    Returns (clash_happened, player_net_damage, opponent_net_damage)
    where net_damage is how much each side takes from this clash.
    """
    if player_move != opponent_move:
        return False, 0, 0

    if player_damage > opponent_damage:
        bonus = int(opponent_damage * 0.25)
        total = player_damage + bonus
        print_slow(YELLOW + f"\nBoth {player_name} and {opponent_name} attempt a {player_move}!" + RESET)
        print_slow(player_color + f"{player_name} counters {opponent_name} and does {total} damage!" + RESET)
        return True, 0, total          # opponent takes damage, player takes none

    elif opponent_damage > player_damage:
        bonus = int(player_damage * 0.25)
        total = opponent_damage + bonus
        print_slow(YELLOW + f"\nBoth {player_name} and {opponent_name} attempt a {player_move}!" + RESET)
        print_slow(opponent_color + f"{opponent_name} counters {player_name} and does {total} damage!" + RESET)
        return True, total, 0          # player takes damage, opponent takes none

    else:
        # Dead equal — no clash resolution, both moves proceed normally
        return False, 0, 0

# ─────────────────────────────────────────────────────────────────────────────
# COMBO SYSTEM  (3-move input, matches reference scripts)
# ─────────────────────────────────────────────────────────────────────────────

def attempt_combo(player_name, opponent_name, valid_moves):
    """
    Prompt player for a 3-move combo input.
    Returns damage dealt (0 if invalid / misses).
    """
    flush_input()
    raw = input(f"{opponent_name} is dazed! Perform a combo! Enter 3 moves ({', '.join(sorted(valid_moves))}): ")
    moves = [normalize_move(m) for m in raw.split()]

    if len(moves) == 3 and all(m in valid_moves for m in moves):
        variety = len(set(moves))
        if variety == 1:
            damage = random.randint(15, 20)
        elif variety == 2:
            damage = random.randint(20, 30)
        else:
            damage = random.randint(35, 45)

        if random.random() < 0.8:
            print_slow(YELLOW + f"{player_name} performed a combo!" + RESET)
            print_slow(f"Dealt {damage} damage!")
            return damage
        else:
            print_slow(f"A near miss! {opponent_name} recovers!")
            return 0
    else:
        print_slow(f"Invalid combo! {opponent_name} recovers!")
        return 0

# ─────────────────────────────────────────────────────────────────────────────
# ILLEGAL INTERFERENCE  (tag-team unique mechanic)
# ─────────────────────────────────────────────────────────────────────────────

def check_illegal_interference(illegal_opponent, illegal_health, active_player,
                                active_player_health, player_color):
    """
    Occasionally the resting opponent sneaks in a shot.
    Returns adjusted active_player_health.
    """
    if illegal_health <= 0:
        return active_player_health
    # ~12 % chance per turn
    if random.random() < 0.12:
        dmg = random.randint(5, 15)
        colour = MAGENTA if "Bret" in illegal_opponent else RED
        print_slow(colour + f"\n⚡ ILLEGAL: {illegal_opponent} sneaks in and hits {active_player} "
                            f"while the ref isn't looking! ({dmg} damage)" + RESET)
        return max(0, active_player_health - dmg)
    return active_player_health

# ─────────────────────────────────────────────────────────────────────────────
# DOUBLE-TEAM FINISHER  (tag-team unique mechanic)
# ─────────────────────────────────────────────────────────────────────────────

def attempt_double_team(p1_name, p2_name, target_name, target_health):
    """
    Available when player tags in while the opponent target is still dazed.
    Returns damage dealt.
    """
    print_slow(YELLOW + f"\n★ DOUBLE TEAM! {p1_name} and {p2_name} coordinate on {target_name}!" + RESET)
    time.sleep(0.5)
    damage = random.randint(40, 65)
    print_slow(GREEN + f"The double-team assault deals {damage} damage!" + RESET)
    return damage

# ─────────────────────────────────────────────────────────────────────────────
# STATUS DISPLAY
# ─────────────────────────────────────────────────────────────────────────────

def print_status(turn_count, player1_name, player1_health, player1_dazed, active_player,
                 player2_name, player2_health, player2_dazed,
                 bret_health, bret_dazed, active_opponent,
                 sting_health, sting_dazed):
    print("\n" + BLUE + "=" * 52 + RESET)
    print(BLUE + f"  TURN {turn_count}" + RESET)
    print(BLUE + "=" * 52 + RESET)

    print(CYAN + "\n  YOUR TEAM:" + RESET)
    for name, hp, dazed in [(player1_name, player1_health, player1_dazed),
                             (player2_name, player2_health, player2_dazed)]:
        tag   = " [IN RING]" if name == active_player else ""
        dz    = " [DAZED]"   if dazed                 else ""
        bar_f = max(0, min(20, hp // 5))
        bar   = "█" * bar_f + "░" * (20 - bar_f)
        print(f"  {CYAN}{name}{RESET}{tag}{dz}")
        print(f"    HP: {hp:>3}  [{bar}]")

    print(MAGENTA + "\n  LEGENDS TEAM:" + RESET)
    for name, hp, dazed, colour in [
            ("Bret Hart", bret_health, bret_dazed, MAGENTA),
            ("Sting",     sting_health, sting_dazed, RED)]:
        tag  = " [IN RING]" if name == active_opponent else ""
        dz   = " [DAZED]"   if dazed                  else ""
        bar_f = max(0, min(20, hp // 9))   # opponents start at 175
        bar   = "█" * bar_f + "░" * (20 - bar_f)
        print(f"  {colour}{name}{RESET}{tag}{dz}")
        print(f"    HP: {hp:>3}  [{bar}]")

    print(BLUE + "=" * 52 + RESET + "\n")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN MATCH
# ─────────────────────────────────────────────────────────────────────────────

def tag_team_match():
    print("\n" * 10)
    print(BLUE + "===========================================")
    print("               Welcome to...")
    print("===========================================" + RESET)
    ring_art = """
      ||-o=======================o-||
      ||-o=======================o-||
      ||-o=======================o-||
      |║                           ║|
      |║                           ║|
       ║                           ║
       ║                           ║
       ║                           ║
      ||-o=======================o-||
      ||-o=======================o-||
      ||-o=======================o-||
      ||---------------------------||
      ||                           ||
      ||___________________________|| """
    print(ring_art)
    print("\n")
    print(CYAN + "===========================================")
    print("         TAG TEAM MATCH ARENA!")
    print("===========================================" + RESET)

    time.sleep(1)
    flush_input()
    team_name    = input("Enter your tag team name: ")
    player1_name = input("Enter Wrestler 1 name: ")
    player2_name = input("Enter Wrestler 2 name: ")

    print_slow(f"\nWelcome! Today's challengers are...")
    print_slow(f"\nTeam: {CYAN}{team_name}{RESET}")
    print_slow(f"  {CYAN}{player1_name}{RESET} — armed with the Powerbomb")
    print_slow(f"  {CYAN}{player2_name}{RESET} — armed with the Suplex")
    print_slow("\n")
    time.sleep(1)

    print_slow("\nThey will face...")
    time.sleep(1)
    print_slow("\nthe best there is,\nthe best there was,\nthe best there ever will be...")
    time.sleep(1)
    print_slow("\n" + MAGENTA + " ♥  Bret Hart  ♥ " + RESET)
    time.sleep(1)
    print_slow("\n...and...")
    print_slow("\nthe icon,\nthe franchise,\nthe man they call...")
    time.sleep(1)
    print_slow("\n" + RED + " 𓆫  Sting  𓆫 " + RESET)
    time.sleep(1)

    print_slow(MAGENTA + "\nBret Hart: If you've got some kinda problem with me saying..." + RESET)
    time.sleep(0.4)
    print_slow(MAGENTA + "I'm the best there is, the best there was, "
                         "the best there ever will be... do something about it!" + RESET)

    print_slow(RED + "\nSting: It's showtime!" + RESET)

    print_slow("\n\n" + YELLOW + "THIS IS A TAG TEAM MATCH!" + RESET)
    print_slow("\nGet ready!\n")
    print("DING! DING! DING!")
    print_slow("\n")

    # ── Player team stats ────────────────────────────────────────────────────
    player1_health    = 100
    player1_punches   = 12
    player1_kicks     = 8
    player1_backdrops = 4
    player1_powerbomb = 1          # special: unlocks at <= 30 HP
    player1_dazed       = False
    player1_daze_cooldown = 0

    player2_health    = 100
    player2_punches   = 12
    player2_kicks     = 8
    player2_backdrops = 4
    player2_suplex    = 1          # special: unlocks at <= 30 HP
    player2_dazed       = False
    player2_daze_cooldown = 0

    # ── Opponent stats ───────────────────────────────────────────────────────
    bret_health       = 175
    bret_punches      = 15
    bret_kicks        = 10
    bret_backdrops    = 3
    bret_sharpshooter = 1
    bret_dazed        = False
    bret_daze_cooldown  = 0
    bret_dropped_last_turn = False   # Sharpshooter eligibility gate

    sting_health      = 175
    sting_punches     = 12
    sting_kicks       = 12
    sting_backdrops   = 3
    sting_deathlock   = 1
    sting_dazed       = False
    sting_daze_cooldown = 0
    sting_dropped_last_turn = False  # Deathlock eligibility gate

    # ── Tag state ────────────────────────────────────────────────────────────
    active_player   = player1_name
    active_opponent = "Bret Hart"

    # ── Turn counters ────────────────────────────────────────────────────────
    turn_count          = 0
    player_combo_cooldown = 0

    print_slow(f"\n{CYAN}{player1_name}{RESET} starts in the ring "
               f"against {MAGENTA}Bret Hart{RESET}!\n")

    # ── MAIN LOOP ────────────────────────────────────────────────────────────
    while (player1_health > 0 or player2_health > 0) and (bret_health > 0 or sting_health > 0):
        turn_count += 1

        # Decrement cooldowns properly (mutate variables, not loop copies)
        if player1_daze_cooldown > 0: player1_daze_cooldown -= 1
        if player2_daze_cooldown > 0: player2_daze_cooldown -= 1
        if bret_daze_cooldown    > 0: bret_daze_cooldown    -= 1
        if sting_daze_cooldown   > 0: sting_daze_cooldown   -= 1
        if player_combo_cooldown > 0: player_combo_cooldown -= 1

        # Snapshot eligibility before resetting
        bret_eligible_this_turn  = bret_dropped_last_turn
        sting_eligible_this_turn = sting_dropped_last_turn
        bret_dropped_last_turn   = False
        sting_dropped_last_turn  = False

        # ── Status display ───────────────────────────────────────────────────
        print_status(turn_count,
                     player1_name, player1_health, player1_dazed, active_player,
                     player2_name, player2_health, player2_dazed,
                     bret_health,  bret_dazed,  active_opponent,
                     sting_health, sting_dazed)

        # ── Forced tag if active player is knocked out ───────────────────────
        current_player_health = player1_health if active_player == player1_name else player2_health
        if current_player_health <= 0:
            other_name   = player2_name if active_player == player1_name else player1_name
            other_health = player2_health if active_player == player1_name else player1_health
            if other_health > 0:
                print_slow(f"{active_player} is knocked out! Forced tag!")
                active_player = other_name
                print_slow(f"{CYAN}{active_player} rushes in!{RESET}")
                continue
            else:
                break

        # ── Special move hint ────────────────────────────────────────────────
        if active_player == player1_name:
            if player1_health <= 30 and player1_powerbomb > 0:
                print(YELLOW + f"  {player1_name} can use: powerbomb!" + RESET)
        else:
            if player2_health <= 30 and player2_suplex > 0:
                print(YELLOW + f"  {player2_name} can use: suplex!" + RESET)

        # ── Build allowed moves ──────────────────────────────────────────────
        allowed_moves = []
        if active_player == player1_name:
            if player1_punches   > 0: allowed_moves.append('punch')
            if player1_kicks     > 0: allowed_moves.append('kick')
            if player1_backdrops > 0: allowed_moves.append('backdrop')
            if player1_health <= 30 and player1_powerbomb > 0:
                allowed_moves.append('powerbomb')
        else:
            if player2_punches   > 0: allowed_moves.append('punch')
            if player2_kicks     > 0: allowed_moves.append('kick')
            if player2_backdrops > 0: allowed_moves.append('backdrop')
            if player2_health <= 30 and player2_suplex > 0:
                allowed_moves.append('suplex')

        # Tag is always available if partner is alive
        partner_name   = player2_name if active_player == player1_name else player1_name
        partner_health = player2_health if active_player == player1_name else player1_health
        if partner_health > 0:
            allowed_moves.append('tag')

        if not allowed_moves:
            print_slow(f"{active_player} is too exhausted to continue!")
            announce_draw(team_name)
            break

        # ── Get player input ─────────────────────────────────────────────────
        flush_input()
        player_move_raw = input(f"{active_player}, choose move ({', '.join(allowed_moves)}): ")
        player_move = normalize_move(player_move_raw)

        if player_move not in allowed_moves:
            print("Invalid move. Choose one of: " + ", ".join(allowed_moves) + ".")
            continue

        # ── TAG ──────────────────────────────────────────────────────────────
        if player_move == 'tag':
            leaving_player = active_player
            entering_player = partner_name

            # Check if opponent is dazed — double-team opportunity
            target_dazed = bret_dazed if active_opponent == "Bret Hart" else sting_dazed
            target_health_now = bret_health if active_opponent == "Bret Hart" else sting_health

            if target_dazed and target_health_now > 0:
                print_slow(f"{CYAN}{leaving_player} tags {entering_player}!{RESET}")
                dt_damage = attempt_double_team(leaving_player, entering_player,
                                                active_opponent, target_health_now)
                if active_opponent == "Bret Hart":
                    bret_health = max(0, bret_health - dt_damage)
                else:
                    sting_health = max(0, sting_health - dt_damage)
                # Daze clears after double team
                bret_dazed  = False
                sting_dazed = False
            else:
                print_slow(f"{CYAN}{leaving_player} tags {entering_player}!{RESET}")
                # Opponent gets a free move on tag (legal rule)
                opp_colour = MAGENTA if active_opponent == "Bret Hart" else RED
                free_dmg = random.randint(8, 20)
                print_slow(opp_colour + f"\n{active_opponent} takes advantage of the tag "
                                        f"and hits {entering_player} for {free_dmg} damage!" + RESET)
                if entering_player == player1_name:
                    player1_health = max(0, player1_health - free_dmg)
                else:
                    player2_health = max(0, player2_health - free_dmg)

            active_player = entering_player
            print_slow(f"{CYAN}{active_player} is now the legal wrestler!{RESET}\n")
            continue

        # ── COMPUTE PLAYER DAMAGE ────────────────────────────────────────────
        player_damage    = 0
        daze_chance_this = False

        act_daze_cd = player1_daze_cooldown if active_player == player1_name else player2_daze_cooldown

        if player_move == 'punch':
            player_damage    = random.randint(1, 15)
            daze_chance_this = (act_daze_cd == 0 and random.random() < 0.15)

        elif player_move == 'kick':
            player_damage    = random.randint(5, 20)
            daze_chance_this = (act_daze_cd == 0 and random.random() < 0.30)

        elif player_move == 'backdrop':
            player_damage    = random.randint(10, 30)
            daze_chance_this = (act_daze_cd == 0 and random.random() < 0.50)

        elif player_move == 'powerbomb':
            player_damage    = random.randint(40, 60)
            daze_chance_this = (act_daze_cd == 0 and random.random() < 0.55)
            player1_powerbomb -= 1

        elif player_move == 'suplex':
            player_damage    = random.randint(40, 60)
            daze_chance_this = (act_daze_cd == 0 and random.random() < 0.55)
            player2_suplex   -= 1

        # ── OPPONENT AI MOVE ─────────────────────────────────────────────────
        opp_dazed = bret_dazed if active_opponent == "Bret Hart" else sting_dazed
        opp_defense_mod = 0.5 if opp_dazed else 1.0

        if active_opponent == "Bret Hart":
            opp_move, opp_damage = opponent_choose_move(
                "Bret Hart", bret_health,
                bret_punches, bret_kicks, bret_backdrops,
                bret_sharpshooter, 'sharpshooter', bret_eligible_this_turn
            )
        else:
            opp_move, opp_damage = opponent_choose_move(
                "Sting", sting_health,
                sting_punches, sting_kicks, sting_backdrops,
                sting_deathlock, 'scorpion_deathlock', sting_eligible_this_turn
            )

        # ── CLASH DETECTION ──────────────────────────────────────────────────
        opp_colour  = MAGENTA if active_opponent == "Bret Hart" else RED
        clash, p_takes, o_takes = resolve_clash(
            active_player, active_opponent,
            player_move, opp_move,
            player_damage, opp_damage,
            CYAN, opp_colour
        )

        if clash:
            # Apply clash damage
            if active_player == player1_name:
                player1_health = max(0, player1_health - p_takes)
            else:
                player2_health = max(0, player2_health - p_takes)

            if active_opponent == "Bret Hart":
                bret_health = max(0, bret_health - int(o_takes * opp_defense_mod))
            else:
                sting_health = max(0, sting_health - int(o_takes * opp_defense_mod))

            # Daze can still apply on clash win
            if o_takes > 0 and daze_chance_this:
                if active_opponent == "Bret Hart":
                    bret_dazed = True; bret_daze_cooldown = 2
                    print(MAGENTA + "Bret Hart is dazed!" + RESET)
                else:
                    sting_dazed = True; sting_daze_cooldown = 2
                    print(RED + "Sting is dazed!" + RESET)

            # Consume move resources on clash
            if opp_move in ('sharpshooter',):     bret_sharpshooter -= 1
            elif opp_move == 'backdrop':           bret_backdrops    -= 1
            elif opp_move == 'kick':               bret_kicks        -= 1
            elif opp_move == 'punch':              bret_punches      -= 1

            if active_player == player1_name:
                if player_move == 'punch':         player1_punches   -= 1
                elif player_move == 'kick':        player1_kicks     -= 1
                elif player_move == 'backdrop':    player1_backdrops -= 1
            else:
                if player_move == 'punch':         player2_punches   -= 1
                elif player_move == 'kick':        player2_kicks     -= 1
                elif player_move == 'backdrop':    player2_backdrops -= 1

        else:
            # ── PLAYER ATTACKS ───────────────────────────────────────────────
            if player_move == 'punch':
                print_slow(CYAN + f"{active_player} punches {active_opponent}!" + RESET)
                if active_player == player1_name: player1_punches   -= 1
                else:                             player2_punches   -= 1
            elif player_move == 'kick':
                print_slow(CYAN + f"{active_player} kicks {active_opponent}!" + RESET)
                if active_player == player1_name: player1_kicks     -= 1
                else:                             player2_kicks     -= 1
            elif player_move == 'backdrop':
                print_slow(CYAN + f"{active_player} performs a backdrop on {active_opponent}!" + RESET)
                if active_player == player1_name: player1_backdrops -= 1
                else:                             player2_backdrops -= 1
            elif player_move == 'powerbomb':
                print_slow(YELLOW + f"{active_player} executes a POWERBOMB on {active_opponent}!" + RESET)
            elif player_move == 'suplex':
                print_slow(YELLOW + f"{active_player} executes a SUPLEX on {active_opponent}!" + RESET)

            actual_player_dmg = int(player_damage * opp_defense_mod)
            print_slow(f"Dealt {actual_player_dmg} damage!")

            if active_opponent == "Bret Hart":
                bret_health = max(0, bret_health - actual_player_dmg)
            else:
                sting_health = max(0, sting_health - actual_player_dmg)

            if daze_chance_this:
                if active_opponent == "Bret Hart":
                    bret_dazed = True; bret_daze_cooldown = 2
                    print(MAGENTA + "Bret Hart is dazed!" + RESET)
                else:
                    sting_dazed = True; sting_daze_cooldown = 2
                    print(RED + "Sting is dazed!" + RESET)

            # ── OPPONENT ATTACKS ─────────────────────────────────────────────
            if not opp_dazed and opp_move:
                act_player_dazed = player1_dazed if active_player == player1_name else player2_dazed
                player_def_mod   = 0.5 if act_player_dazed else 1.0
                actual_opp_dmg   = int(opp_damage * player_def_mod)

                if active_opponent == "Bret Hart":
                    if opp_move == 'punch':
                        print_slow(MAGENTA + f"Bret Hart punches {active_player}!" + RESET)
                        bret_punches -= 1
                    elif opp_move == 'kick':
                        print_slow(MAGENTA + f"Bret Hart kicks {active_player}!" + RESET)
                        bret_kicks   -= 1
                    elif opp_move == 'backdrop':
                        print_slow(MAGENTA + f"Bret Hart performs a backdrop on {active_player}!" + RESET)
                        bret_backdrops -= 1
                    elif opp_move == 'sharpshooter':
                        print_slow(YELLOW + f"Bret Hart locks {active_player} in the Sharpshooter!" + RESET)
                        print_slow(f"{active_player} takes {actual_opp_dmg} damage!")
                        print_slow(CYAN + f"{active_player} struggles and breaks free!" + RESET)
                        bret_sharpshooter = 0

                    print_slow(f"{active_player} takes {actual_opp_dmg} damage!")

                else:  # Sting
                    if opp_move == 'punch':
                        print_slow(RED + f"Sting punches {active_player}!" + RESET)
                        sting_punches -= 1
                    elif opp_move == 'kick':
                        print_slow(RED + f"Sting kicks {active_player}!" + RESET)
                        sting_kicks   -= 1
                    elif opp_move == 'backdrop':
                        print_slow(RED + f"Sting performs a backdrop on {active_player}!" + RESET)
                        sting_backdrops -= 1
                    elif opp_move == 'scorpion_deathlock':
                        print_slow(YELLOW + f"Sting locks {active_player} in the Scorpion Deathlock!" + RESET)
                        print_slow(f"{active_player} takes {actual_opp_dmg} damage!")
                        print_slow(CYAN + f"{active_player} struggles and breaks free!" + RESET)
                        sting_deathlock = 0

                    print_slow(f"{active_player} takes {actual_opp_dmg} damage!")

                if active_player == player1_name:
                    player1_health = max(0, player1_health - actual_opp_dmg)
                else:
                    player2_health = max(0, player2_health - actual_opp_dmg)

            elif opp_dazed:
                print_slow(opp_colour + f"{active_opponent} can't attack — still dazed!" + RESET)

        # ── ILLEGAL INTERFERENCE ─────────────────────────────────────────────
        illegal_opponent = "Sting" if active_opponent == "Bret Hart" else "Bret Hart"
        illegal_health   = sting_health if illegal_opponent == "Sting" else bret_health
        cur_p_health = player1_health if active_player == player1_name else player2_health
        cur_p_health = check_illegal_interference(illegal_opponent, illegal_health,
                                                  active_player, cur_p_health, CYAN)
        if active_player == player1_name:
            player1_health = cur_p_health
        else:
            player2_health = cur_p_health

        # ── OPPONENT TAGS OUT if low health ──────────────────────────────────
        cur_opp_health = bret_health if active_opponent == "Bret Hart" else sting_health
        if cur_opp_health <= 20:
            if active_opponent == "Bret Hart" and sting_health > 0:
                print_slow(MAGENTA + "\nBret Hart is in trouble — he tags Sting!" + RESET)
                active_opponent = "Sting"
            elif active_opponent == "Sting" and bret_health > 0:
                print_slow(RED + "\nSting is in trouble — he tags Bret Hart!" + RESET)
                active_opponent = "Bret Hart"

        # ── Eligibility gate: flag if opponent just dropped below 30 ─────────
        prev_bret  = bret_health  + (int(player_damage * opp_defense_mod) if active_opponent == "Bret Hart" else 0)
        prev_sting = sting_health + (int(player_damage * opp_defense_mod) if active_opponent == "Sting"     else 0)
        if prev_bret  > 30 and bret_health  <= 30: bret_dropped_last_turn  = True
        if prev_sting > 30 and sting_health <= 30: sting_dropped_last_turn = True

        # ── PIN ATTEMPT — opponent down ───────────────────────────────────────
        if bret_health <= 0:
            print_slow(f"\n{CYAN}{active_player} goes for the pin on Bret Hart!{RESET}")
            if pin_attempt(bret_health, bret_dazed):
                announce_winner(team_name, True)
                return
            else:
                bret_health = handle_kickout("Bret Hart", False)
                bret_dazed  = False
                bret_daze_cooldown = 1

        if sting_health <= 0:
            print_slow(f"\n{CYAN}{active_player} goes for the pin on Sting!{RESET}")
            if pin_attempt(sting_health, sting_dazed):
                announce_winner(team_name, True)
                return
            else:
                sting_health = handle_kickout("Sting", False)
                sting_dazed  = False
                sting_daze_cooldown = 1

        # ── PIN ATTEMPT — player down ─────────────────────────────────────────
        active_player_health = player1_health if active_player == player1_name else player2_health
        if active_player_health <= 0:
            print_slow(f"\n{active_opponent} goes for the pin on {active_player}!")
            act_dazed = player1_dazed if active_player == player1_name else player2_dazed
            if pin_attempt(active_player_health, act_dazed):
                announce_winner(team_name, False)
                return
            else:
                restored = handle_kickout(active_player, True)
                if active_player == player1_name:
                    player1_health = restored; player1_dazed = False
                else:
                    player2_health = restored; player2_dazed = False

        # ── COMBO SYSTEM ──────────────────────────────────────────────────────
        active_opp_dazed = bret_dazed if active_opponent == "Bret Hart" else sting_dazed
        if active_opp_dazed and player_combo_cooldown == 0:
            valid_combo_moves = {'punch', 'kick', 'backdrop'}
            combo_dmg = attempt_combo(active_player, active_opponent, valid_combo_moves)
            if combo_dmg > 0:
                if active_opponent == "Bret Hart":
                    bret_health = max(0, bret_health - combo_dmg)
                    bret_dazed  = False
                else:
                    sting_health = max(0, sting_health - combo_dmg)
                    sting_dazed  = False
            else:
                bret_dazed  = False
                sting_dazed = False
            player_combo_cooldown = 2

        time.sleep(0.5)

    # ── POST-LOOP RESULT ──────────────────────────────────────────────────────
    both_players_out   = player1_health <= 0 and player2_health <= 0
    both_opponents_out = bret_health    <= 0 and sting_health    <= 0

    if both_opponents_out and not both_players_out:
        announce_winner(team_name, True)
    elif both_players_out and not both_opponents_out:
        announce_winner(team_name, False)
    else:
        announce_draw(team_name)


if __name__ == "__main__":
    tag_team_match()
