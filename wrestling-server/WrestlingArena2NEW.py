import random
import time
import sys
import os
import json

CYAN = '\033[96m'
GREEN = '\033[32m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[33m'
RESET = '\033[0m'

def flush_input():
    try:
        if os.name == 'posix':  # Unix/Linux/Mac
            import termios
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        else:  # Windows
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
    except Exception:
        pass

def print_slow(text, delay=0.05):
    """Print text one character at a time."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
        sys.stdout.flush()

def normalize_move(text):
    """Normalize user input to canonical move names."""
    if not text:
        return ""
    return text.strip().lower().replace('-', '').replace('_', '')

def save_match_result(player_name, result, opponent="Sting"):
    """Save match result to JSON file."""
    try:
        # Load existing data
        try:
            with open(".sting_progress.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"wins": 0, "losses": 0, "draws": 0, "matches": []}
        
        # Update win/loss/draw counts
        if result == "win":
            data["wins"] = data.get("wins", 0) + 1
        elif result == "loss":
            data["losses"] = data.get("losses", 0) + 1
        else:  # draw
            data["draws"] = data.get("draws", 0) + 1
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        match_record = {
            "date": timestamp,
            "player": player_name,
            "opponent": opponent,
            "result": result,
            "details": f"{player_name} vs {opponent}: {result.upper()}"
        }
        
        if "matches" not in data:
            data["matches"] = []
        data["matches"].append(match_record)
        
        if len(data["matches"]) > 50:
            data["matches"] = data["matches"][-50:]
        
        # Save to file
        with open(".sting_progress.json", "w") as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        print(f"Error saving match result: {e}")

def pin_attempt(health):
    pin_fail_chance = 1 - (health / 100.0)
    pin_fail_chance = max(0.0, min(1.0, pin_fail_chance))
    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    return random.random() < pin_fail_chance

def pin_attempt_with_daze(health, is_opponent_dazed=False):
    """Pin attempt with bonus chance if opponent is dazed."""
    pin_fail_chance = 1 - (health / 100.0)
    pin_fail_chance = max(0.0, min(1.0, pin_fail_chance))
    
    if is_opponent_dazed:
        pin_fail_chance *= 0.9  
    
    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    return random.random() < pin_fail_chance

def announce_draw(player_name):
    """Announce a draw result when player runs out of moves."""
    print("\n" + BLUE + "===========================================")
    print(BLUE + "           The match ends in a DRAW!" + RESET)
    print(BLUE + "===========================================" + RESET + "\n")
    
    print_slow("You are too exhausted to continue! The referee calls the match." + RESET)
    
    # Save draw result
    save_match_result(player_name, "draw")
    
    print_slow("\nReturning to main menu in 3 seconds..." + RESET)
    time.sleep(3)

def announce_winner(player_name, player_wins):
    print("3... The match is over!")
    
    if player_wins:
        print_slow(CYAN + f"Congratulations, {player_name}! You have pinned Sting!" + RESET)
        print("\n" + BLUE + "===========================================")
        print(BLUE + f"{player_name} wins the match!" + RESET)
        print(BLUE + "===========================================" + RESET + "\n")
        # Save win result
        save_match_result(player_name, "win")
    else:
        print_slow(RED + f"Oh no! {player_name} has been pinned by Sting!" + RESET)
        print("\n" + BLUE + "===========================================")
        print(BLUE + f"{player_name} loses the match!" + RESET)
        print(BLUE + "===========================================" + RESET + "\n")
        # Save loss result
        save_match_result(player_name, "loss")

        print_slow("\nReturning to main menu in 3 seconds..." + RESET)
        time.sleep(3)

def handle_kickout(is_player_kicking_out, player_name):
    """Handle kickout sequence with proper timing."""
    print("Kick out! The match continues!")
    if is_player_kicking_out:
        print(CYAN + f"{player_name} kicks out!" + RESET)
        return 30  
    else:
        print(RED + "Sting kicks out!" + RESET)
        return 30  
    
def wrestling_match():
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
    print(BLUE + "===========================================")
    print("           The Wrestling Arena!")
    print("===========================================" + RESET)
    
    time.sleep(1)
    flush_input()
    player_name = input("Enter your name: ")
    
    print_slow("\nWelcome! Today's challenger is...")
    print_slow("\nthe icon,\nthe franchise,\nthe man they call...")
    print_slow("\n" * 3)
    print_slow(RED + " 𓆫  Sting  𓆫 " + RESET)
    print_slow("\n" * 1)
    time.sleep(0.5)
    
    print_slow(RED + "\nI've faced the best, I've beaten the best, and I've been the best...\n")
    time.sleep(1)
    print_slow("but being the best isn't about titles or accolades, ")
    time.sleep(0.5)
    print_slow("\nit's about heart, passion, and fighting for what's right, ")
    time.sleep(0.5)
    print_slow("\nand that's why I stand here. \n")
    time.sleep(1)
    print_slow("It's showtime!" + RESET)
    print_slow("\n" * 1)
    
    print_slow("\nGet ready!\n" + RESET)
    print("\n" + "DING! DING! DING!" + RESET)
    print_slow("\n" * 1)
    
    # Initial stats
    player_health = 100
    opponent_health = 175
    player_punches = 12
    player_kicks = 8
    player_backdrops = 4
    player_powerbomb = 1
    opponent_punches = 15
    opponent_kicks = 10
    opponent_backdrops = 2
    opponent_scorpion_deathlock = 1
    opponent_dazed = False
    sting_dropped_last_turn = False
    daze_cooldown = 0
    combo_cooldown = 0
    
    while player_health > 0 and opponent_health > 0:
        if daze_cooldown > 0:
            daze_cooldown -= 1
        if combo_cooldown > 0:
            combo_cooldown -= 1
        
        sting_eligible_this_turn = sting_dropped_last_turn
        sting_dropped_last_turn = False
        
        print("===========================================" + RESET)
        print_slow(CYAN + f"{player_name}'s Health: {player_health}" + RESET)
        print_slow(RED + f"Sting's Health: {opponent_health}" + RESET)
        print("===========================================" + RESET + "\n")
        
        if player_health <= 30 and player_powerbomb > 0:
            print(YELLOW + "You can use your special move: powerbomb!" + RESET + "\n")
        
        allowed_moves = []
        if player_punches > 0:
            allowed_moves.append('punch')
        if player_kicks > 0:
            allowed_moves.append('kick')
        if player_backdrops > 0:  
            allowed_moves.append('backdrop') 
        if player_health <= 30 and player_powerbomb > 0: 
            allowed_moves.append('powerbomb') 
        
        if not allowed_moves:
            print_slow("You are too exhausted to continue! The referee calls the match.")
            announce_draw(player_name)
            break
        
        flush_input()
        player_move_raw = input(f"Choose your move ({', '.join(allowed_moves)}): ")
        player_move = normalize_move(player_move_raw)
        
        if player_move not in allowed_moves:
            print("Invalid move. Choose one of: " + ", ".join(allowed_moves) + ".")
            continue
        
        opponent_defense_modifier = 0.5 if opponent_dazed else 1.0
        prev_opponent_health = opponent_health
        
        player_damage = 0
        daze_chance_this_turn = False
        
        if player_move == 'punch':
            player_damage = random.randint(1, 15)
            daze_chance_this_turn = (daze_cooldown == 0 and random.random() < 0.15)
            
        elif player_move == 'kick':
            player_damage = random.randint(5, 20) 
            daze_chance_this_turn = (daze_cooldown == 0 and random.random() < 0.3)
            
        elif player_move == 'backdrop':  
            player_damage = random.randint(10, 30)  
            daze_chance_this_turn = (daze_cooldown == 0 and random.random() < 0.5)
            
        elif player_move == 'powerbomb':  
            player_damage = random.randint(40, 60)
        
        opponent_move = None
        opponent_damage = 0
        clash_detected = False
        clash_resolved = False
        clash_player_wins = False
        clash_total_damage = 0
        
        if opponent_health > 0 and not opponent_dazed:
            possible_moves = []
            if opponent_scorpion_deathlock > 0 and opponent_health <= 30 and sting_eligible_this_turn:  
                possible_moves.append(('scorpion_deathlock', 50))  
            if opponent_backdrops > 0: 
                possible_moves.append(('backdrop', 33))  
            if opponent_kicks > 0:
                possible_moves.append(('kick', 25))
            if opponent_punches > 0:
                possible_moves.append(('punch', 15))
            
            if possible_moves:
                moves, weights = zip(*possible_moves)
                total_weight = sum(weights)
                
                if random.random() < 0.8:
                    r = random.random() * total_weight
                    cumulative = 0
                    for i, weight in enumerate(weights):
                        cumulative += weight
                        if r <= cumulative:
                            opponent_move = moves[i]
                            break
                else:
                    opponent_move = random.choice(moves)
                
                if opponent_move == 'punch':
                    opponent_damage = random.randint(8, 20)
                elif opponent_move == 'kick':
                    opponent_damage = random.randint(12, 35)
                elif opponent_move == 'backdrop':  
                    opponent_damage = random.randint(18, 50)
                elif opponent_move == 'scorpion_deathlock':  
                    opponent_damage = random.randint(35, 60)
                
                if opponent_move == player_move:
                    clash_detected = True
                    
                    if player_damage > opponent_damage:
                        clash_player_wins = True
                        bonus_damage = int(opponent_damage * 0.25)
                        clash_total_damage = player_damage + bonus_damage
                        
                        print_slow(YELLOW + f"\nBoth {player_name} and Sting attempt a {player_move}!" + RESET)
                        print_slow(CYAN + f"{player_name} counters Sting and does {clash_total_damage} damage!" + RESET)
                        
                        opponent_health -= int(clash_total_damage * opponent_defense_modifier)
                        
                        if daze_chance_this_turn:
                            opponent_dazed = True
                            daze_cooldown = 2
                            print(RED + "Sting is dazed!" + RESET)
                        
                        if opponent_move == 'scorpion_deathlock':
                            opponent_scorpion_deathlock = 0
                        elif opponent_move == 'backdrop':
                            opponent_backdrops -= 1
                        elif opponent_move == 'kick':
                            opponent_kicks -= 1
                        elif opponent_move == 'punch':
                            opponent_punches -= 1
                            
                        if player_move == 'punch':
                            player_punches -= 1
                        elif player_move == 'kick':
                            player_kicks -= 1
                        elif player_move == 'backdrop':
                            player_backdrops -= 1
                        elif player_move == 'powerbomb':
                            player_powerbomb -= 1
                            
                        clash_resolved = True
                        
                    elif opponent_damage > player_damage:
                        clash_player_wins = False
                        bonus_damage = int(player_damage * 0.25)
                        clash_total_damage = opponent_damage + bonus_damage
                        
                        print_slow(YELLOW + f"\nBoth {player_name} and Sting attempt a {player_move}!" + RESET)
                        print_slow(RED + f"Sting counters {player_name} and does {clash_total_damage} damage!" + RESET)
                        
                        player_health -= clash_total_damage
                                                
                        if opponent_move == 'scorpion_deathlock':
                            opponent_scorpion_deathlock = 0
                        elif opponent_move == 'backdrop':
                            opponent_backdrops -= 1
                        elif opponent_move == 'kick':
                            opponent_kicks -= 1
                        elif opponent_move == 'punch':
                            opponent_punches -= 1
                            
                        if player_move == 'punch':
                            player_punches -= 1
                        elif player_move == 'kick':
                            player_kicks -= 1
                        elif player_move == 'backdrop':
                            player_backdrops -= 1
                        elif player_move == 'powerbomb':
                            player_powerbomb -= 1
                            
                        clash_resolved = True
                        
                    else:
                        clash_detected = False
        
        if not clash_detected or (clash_detected and not clash_resolved):
            # PLAYER'S TURN
            if player_move == 'punch':
                print_slow(CYAN + f"{player_name} punches Sting!" + RESET)
                print_slow(f"{player_name} dealt {player_damage} damage.")
                opponent_health -= int(player_damage * opponent_defense_modifier)
                if daze_chance_this_turn:
                    opponent_dazed = True
                    daze_cooldown = 2
                    print(RED + "Sting is dazed!" + RESET)
                player_punches -= 1
                
            elif player_move == 'kick':
                print_slow(CYAN + f"{player_name} kicks Sting!" + RESET)
                print_slow(f"{player_name} dealt {player_damage} damage.")
                opponent_health -= int(player_damage * opponent_defense_modifier)
                if daze_chance_this_turn:
                    opponent_dazed = True
                    daze_cooldown = 2
                    print(RED + "Sting is dazed!" + RESET)
                player_kicks -= 1
                
            elif player_move == 'backdrop':  
                print_slow(CYAN + f"{player_name} performs a backdrop on Sting!" + RESET)  
                print_slow(f"{player_name} dealt {player_damage} damage.")
                opponent_health -= int(player_damage * opponent_defense_modifier)
                if daze_chance_this_turn:
                    opponent_dazed = True
                    daze_cooldown = 2
                    print(RED + "Sting is dazed!" + RESET)
                player_backdrops -= 1  
                
            elif player_move == 'powerbomb':  
                print_slow(YELLOW + f"{player_name} executes a powerbomb on Sting!" + RESET) 
                print_slow(f"{player_name} dealt {player_damage} damage.")
                opponent_health -= int(player_damage * opponent_defense_modifier)
                player_powerbomb -= 1  
            
            # OPPONENT'S TURN
            if opponent_health > 0 and not opponent_dazed and opponent_move and not clash_resolved:
                if opponent_move == 'punch':
                    print_slow(RED + f"Sting punches {player_name}!" + RESET)
                    print_slow(f"{player_name} takes {opponent_damage} damage.")
                    player_health -= opponent_damage
                    opponent_punches -= 1
                    
                elif opponent_move == 'kick':
                    print_slow(RED + f"Sting kicks {player_name}!" + RESET)  
                    print_slow(f"{player_name} takes {opponent_damage} damage.")
                    player_health -= opponent_damage
                    opponent_kicks -= 1
                    
                elif opponent_move == 'backdrop':  
                    print_slow(RED + f"Sting performs a backdrop on {player_name}!" + RESET)  
                    print_slow(f"{player_name} takes {opponent_damage} damage.")
                    player_health -= opponent_damage
                    opponent_backdrops -= 1  
                    
                elif opponent_move == 'scorpion_deathlock':  
                    print_slow(YELLOW + f"Sting locks {player_name} in the Scorpion Deathlock!" + RESET)  
                    print_slow(f"{player_name} takes {opponent_damage} damage from the Scorpion Deathlock!")
                    player_health -= opponent_damage
                    opponent_scorpion_deathlock = 0  
                    print_slow(CYAN + f"{player_name} struggles and breaks free from the Scorpion Deathlock!" + RESET)
            
            elif opponent_health > 0 and not opponent_dazed and not opponent_move and not clash_resolved:
                print_slow(RED + "Sting can't attack right now." + RESET)
        
        if prev_opponent_health > 30 and opponent_health <= 30 and opponent_health > 0:
            sting_dropped_last_turn = True
        
        opponent_health = max(opponent_health, 0)
        
        if opponent_health <= 0:
            if pin_attempt_with_daze(player_health, opponent_dazed):
                announce_winner(player_name, True)
                break
            else:
                opponent_health = handle_kickout(False, player_name)
                opponent_dazed = False
                daze_cooldown = 1  
                combo_cooldown = 0  
        
        player_health = max(player_health, 0)
        
        if player_health <= 0:
            if pin_attempt_with_daze(opponent_health, False):
                announce_winner(player_name, False)
                break
            else:
                player_health = handle_kickout(True, player_name)
        
        if opponent_dazed and opponent_health > 0 and combo_cooldown == 0:  
            flush_input()
            combo_input_raw = input("Sting is dazed! Perform a combo now!: ")  
            combo_moves = [normalize_move(m) for m in combo_input_raw.split()]
            valid_moves = {'punch', 'kick', 'backdrop'}  
            
            if len(combo_moves) == 3 and all(m in valid_moves for m in combo_moves):
                variety = len(set(combo_moves))
                if variety == 1:
                    damage = random.randint(15, 20)
                elif variety == 2:
                    damage = random.randint(20, 30)
                else:
                    damage = random.randint(35, 45)
                
                if random.random() < 0.8:
                    print_slow(YELLOW + f"{player_name} performed a combo!" + RESET)
                    print_slow(f"{player_name} dealt {damage} damage.")
                    opponent_health -= damage
                    opponent_health = max(opponent_health, 0)
                else:
                    print("A near miss! Sting recovers.")  
            else:
                print("A near miss! Sting recovers.")  
            
            opponent_dazed = False
            combo_cooldown = 2  

if __name__ == "__main__":
    wrestling_match()
    
