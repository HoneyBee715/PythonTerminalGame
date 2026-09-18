# battlefield.py
# Iron Commander — Battlefield Display and Game Loop
# Phase 3: Core build — Step 4

import random
import time
import os

from tank import ScoutTank, AssaultTank, HeavyTank, ArtilleryTank
from enemy import Raider, Enforcer, SiegeTank, Hunter, spawn_wave
from commander import Commander


# ─────────────────────────────────────────────
# DISPLAY HELPERS
# All terminal display functions live here.
# These print the battlefield, menus, and
# turn results in a clean readable format.
# ─────────────────────────────────────────────

def clear_screen():
    """Clears the terminal between turns for a clean display."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_divider(char="─", width=56):
    """Prints a horizontal divider line."""
    print("  " + char * width)


def print_header(wave, turn, score):
    """Prints the game header showing wave, turn, and score."""
    print_divider("═")
    print(f"  ██ IRON COMMANDER  │  Wave: {wave}  │  "
          f"Turn: {turn}  │  Score: {score}")
    print_divider("═")


def print_battlefield(squad, enemies, commander):
    """
    Prints the main battlefield string.
    Friendly tanks on the right, enemies on the left.
    Commander position is marked with ◄►.

    Example:
    ENEMY  [ RDR ] [ ENF ]  ◄══════► [ SCT ][CMD][ HVY ][ ART ]  SAFE
    """
    print("\n  BATTLEFIELD")
    print_divider()

    # Build enemy side string
    enemy_str = ""
    for e in enemies:
        if e.is_alive:
            enemy_str += f"[{e.symbol}] "

    # Build friendly side string with Commander marked
    friendly_str = ""
    for i, tank in enumerate(squad):
        if not tank.is_alive:
            friendly_str += f"[{tank.symbol}✕] "
        elif i == commander.position:
            friendly_str += f"[{tank.symbol}]◄CMD►"
        else:
            friendly_str += f"[{tank.symbol}] "

    # Print the full battlefield line
    if enemy_str:
        print(f"  ENEMY ◄  {enemy_str.strip()}  ║  "
              f"{friendly_str.strip()}  ║  SAFE")
    else:
        print(f"  NO ENEMIES REMAINING  ║  "
              f"{friendly_str.strip()}  ║  SAFE")

    print_divider()


def print_squad_status(squad, commander):
    """Prints a detailed HP and shield status for every friendly unit."""
    print("\n  FRIENDLY UNITS")
    print_divider()

    for i, tank in enumerate(squad):
        pos_marker = " ◄ Commander here" if i == commander.position else ""
        status     = "DESTROYED" if not tank.is_alive else ""
        shield_str = f"  SH:{tank.shield}" if tank.shield > 0 else ""
        print(f"  {i+1}. {tank.name:<16} "
              f"{tank.hp_bar(width=8)}{shield_str:<8} "
              f"{status}{pos_marker}")

    print_divider()


def print_enemy_status(enemies):
    """Prints HP status for all living enemies."""
    alive_enemies = [e for e in enemies if e.is_alive]
    if not alive_enemies:
        return

    print("\n  ENEMY UNITS")
    print_divider()
    for e in alive_enemies:
        print(f"  {e.name:<14} {e.hp_bar(width=8)}"
              f"  ATK:{e.attack}  RWD:+{e.supply_reward}")
    print_divider()


def print_action_menu(commander, squad):
    """Prints the Commander action menu for the current turn."""
    nearby = commander.get_nearby_tanks(squad)

    print("\n  COMMANDER ACTIONS")
    print_divider()
    print(f"  Supply: {commander.supply}/{commander.supply_cap}  │  "
          f"Shields: {commander.shield_charges}/{commander.shield_charges_max}")
    print_divider()
    print("  1. Move LEFT")
    print("  2. Move RIGHT")

    # Only show heal option if supply is available and nearby tanks need it
    healable = [t for t in nearby
                if t.hp < t.max_hp and t.is_alive]
    if healable and commander.supply > 0:
        print("  3. Grant HEALTH to a nearby tank")
    else:
        if commander.supply <= 0:
            print("  3. Grant HEALTH  [NO SUPPLY]")
        else:
            print("  3. Grant HEALTH  [ALL NEARBY TANKS AT FULL HP]")

    # Only show shield if charges remain and nearby tanks are alive
    shieldable = [t for t in nearby if t.is_alive]
    if shieldable and commander.shield_charges > 0:
        print("  4. Set SHIELD on a nearby tank")
    else:
        if commander.shield_charges <= 0:
            print("  4. Set SHIELD  [NO CHARGES REMAINING]")
        else:
            print("  4. Set SHIELD  [NO NEARBY TANKS]")

    print("  5. Show nearby tank details")
    print_divider()


# ─────────────────────────────────────────────
# INPUT HELPERS
# Safe input functions that catch bad values
# and ask again rather than crashing the game.
# ─────────────────────────────────────────────

def get_int_input(prompt, valid_range):
    """
    Asks for an integer input and keeps asking
    until a valid choice from valid_range is given.
    """
    while True:
        try:
            choice = int(input(prompt))
            if choice in valid_range:
                return choice
            print(f"  Please enter a number between "
                  f"{min(valid_range)} and {max(valid_range)}.")
        except ValueError:
            print("  Please enter a number.")


def choose_tank_from_list(tank_list, prompt):
    """
    Shows a numbered list of tanks and returns
    the one the player picks. Returns None if
    the list is empty.
    """
    if not tank_list:
        return None

    print(f"\n  {prompt}")
    for i, tank in enumerate(tank_list):
        print(f"  {i+1}. {tank.name}  {tank.hp_bar(width=8)}")

    choice = get_int_input(
        f"  Enter number (1-{len(tank_list)}): ",
        range(1, len(tank_list) + 1)
    )
    return tank_list[choice - 1]


# ─────────────────────────────────────────────
# COMMANDER TURN
# Handles all player input for one Commander
# action per turn.
# ─────────────────────────────────────────────

def commander_turn(commander, squad, enemies):
    """
    Displays the action menu and processes
    the player's chosen action for this turn.
    Returns True when a valid action is taken.
    """
    print_action_menu(commander, squad)

    choice = get_int_input(
        "  Your action (1-5): ",
        range(1, 6)
    )

    # ── Move left ──
    if choice == 1:
        commander.move_left(squad)
        return True

    # ── Move right ──
    elif choice == 2:
        commander.move_right(squad)
        return True

    # ── Grant health ──
    elif choice == 3:
        if commander.supply <= 0:
            print("\n  No supply available!")
            return False

        nearby = [t for t in commander.get_nearby_tanks(squad)
                  if t.is_alive and t.hp < t.max_hp]
        if not nearby:
            print("\n  No nearby tanks need healing.")
            return False

        target = choose_tank_from_list(nearby,
                                       "Choose a tank to heal:")
        if target:
            amount = get_int_input(
                f"  How much HP to grant? "
                f"(1-{min(commander.supply, target.max_hp - target.hp)}): ",
                range(1, min(commander.supply,
                             target.max_hp - target.hp) + 1)
            )
            return commander.grant_health(target, amount, squad)
        return False

    # ── Set shield ──
    elif choice == 4:
        if commander.shield_charges <= 0:
            print("\n  No shield charges remaining!")
            return False

        nearby = [t for t in commander.get_nearby_tanks(squad)
                  if t.is_alive]
        if not nearby:
            print("\n  No nearby tanks to shield.")
            return False

        target = choose_tank_from_list(nearby,
                                       "Choose a tank to shield:")
        if target:
            return commander.set_shield(target, squad)
        return False

    # ── Show nearby details ──
    elif choice == 5:
        commander.show_nearby(squad)
        return False   # Does not consume the turn

    return False


# ─────────────────────────────────────────────
# FRIENDLY TANKS FIRE
# Each alive friendly tank automatically
# attacks the nearest alive enemy.
# ─────────────────────────────────────────────

def friendly_fire_phase(squad, enemies):
    """
    Each friendly tank attacks the nearest
    alive enemy. Returns list of newly destroyed
    enemy tanks this phase.
    """
    alive_enemies  = [e for e in enemies if e.is_alive]
    newly_destroyed = []

    if not alive_enemies:
        return newly_destroyed

    print("\n  ── Friendly tanks fire ─────────────────")

    for tank in squad:
        if not tank.is_alive:
            continue

        # Target nearest alive enemy (first in list)
        target = alive_enemies[0] if alive_enemies else None
        if not target:
            break

        # Apply small random variance to damage (+/- 20%)
        variance = random.uniform(0.8, 1.2)
        damage   = max(1, int(tank.attack * variance))

        print(f"\n  {tank.name} fires at {target.name} "
              f"for {damage} damage!")
        target.take_damage(damage)

        # If enemy was just destroyed, remove from alive list
        if not target.is_alive:
            alive_enemies.remove(target)
            newly_destroyed.append(target)

    return newly_destroyed


# ─────────────────────────────────────────────
# ENEMY TURN
# Each alive enemy moves toward its target
# and attacks if in range.
# ─────────────────────────────────────────────

def enemy_turn(enemies, squad, commander):
    """
    Each enemy attacks its preferred target.
    Raiders target the Commander directly.
    Returns True if Commander was attacked.
    """
    alive_enemies = [e for e in enemies if e.is_alive]

    if not alive_enemies:
        return False

    print("\n  ── Enemies attack ──────────────────────")
    commander_attacked = False

    for enemy in alive_enemies:
        if not enemy.is_alive:
            continue

        # Raiders target Commander — pass commander object
        if isinstance(enemy, Raider):
            if commander.is_alive:
                print(f"\n  {enemy.name} charges the Commander!")
                variance = random.uniform(0.8, 1.2)
                damage   = max(1, int(enemy.attack * variance))
                print(f"  {enemy.name} hits Commander for {damage}!")
                commander.take_damage(damage)
                commander_attacked = True
            else:
                # Commander gone — attack nearest tank
                enemy.perform_attack(squad)
        else:
            # All other enemies attack friendly tanks
            alive_squad = [t for t in squad if t.is_alive]
            if alive_squad:
                enemy.perform_attack(alive_squad)

    return commander_attacked


# ─────────────────────────────────────────────
# SUPPLY PHASE
# Awards supply for newly destroyed enemies.
# ─────────────────────────────────────────────

def supply_phase(commander, newly_destroyed):
    """Awards supply to the Commander for each destroyed enemy."""
    if not newly_destroyed:
        return

    print("\n  ── Supply earned ───────────────────────")
    for enemy in newly_destroyed:
        print(f"  {enemy.name} destroyed!", end=" ")
        commander.add_supply(enemy.supply_reward)


# ─────────────────────────────────────────────
# CHECK CONDITIONS
# Win/loss state checks after each turn.
# ─────────────────────────────────────────────

def check_loss(squad, commander):
    """
    Returns True if the game is lost.
    Loss conditions:
      1. Commander is destroyed
      2. All friendly tanks are destroyed
    """
    if not commander.is_alive:
        print("\n  *** COMMANDER DESTROYED — GAME OVER ***")
        return True

    if not any(t.is_alive for t in squad):
        print("\n  *** ALL FRIENDLY TANKS DESTROYED — GAME OVER ***")
        return True

    return False


def check_wave_clear(enemies):
    """Returns True if all enemies in this wave are destroyed."""
    return not any(e.is_alive for e in enemies)


def check_no_loss_bonus(squad):
    """Returns True if all friendly tanks survived the wave."""
    return all(t.is_alive for t in squad)


# ─────────────────────────────────────────────
# WAVE LOOP
# Runs one complete wave from spawn to clear.
# Returns True if the player survived the wave,
# False if the game was lost during the wave.
# ─────────────────────────────────────────────

def run_wave(wave_number, squad, commander, score):
    """
    Manages one full wave of combat.
    Returns (survived: bool, score: int)
    """
    print(f"\n")
    print_divider("═")
    print(f"  ██  WAVE {wave_number} BEGINS  ██")
    print_divider("═")

    # Spawn enemies for this wave
    enemies = spawn_wave(wave_number)
    turn    = 1

    input("\n  Press ENTER to begin the wave...")

    # ── Wave turn loop ──────────────────────
    while True:
        clear_screen()

        # Display current state
        print_header(wave_number, turn, score)
        print_battlefield(squad, enemies, commander)
        print_squad_status(squad, commander)
        print_enemy_status(enemies)
        commander.show_status()

        # ── Phase 1: Commander action ──
        print("\n  ── Your turn ───────────────────────────")
        action_taken = False
        while not action_taken:
            action_taken = commander_turn(commander, squad, enemies)

        # ── Phase 2: Friendly tanks fire ──
        newly_destroyed = friendly_fire_phase(squad, enemies)

        # ── Phase 3: Award supply for kills ──
        supply_phase(commander, newly_destroyed)
        score += len(newly_destroyed) * 10

        # ── Phase 4: Check wave cleared ──
        if check_wave_clear(enemies):
            print_divider()
            print(f"\n  *** WAVE {wave_number} CLEARED! ***")

            # Bonus supply if no friendly tanks lost
            if check_no_loss_bonus(squad):
                print("  Perfect wave — no friendly tanks lost!")
                commander.refresh_wave(bonus_supply=40)
            else:
                commander.refresh_wave(bonus_supply=0)

            score += wave_number * 50
            print(f"  Wave score bonus: +{wave_number * 50} points")
            print(f"  Total score: {score}")
            input("\n  Press ENTER to continue to the next wave...")
            return True, score

        # ── Phase 5: Enemies attack ──
        enemy_turn(enemies, squad, commander)

        # ── Phase 6: Check loss conditions ──
        if check_loss(squad, commander):
            return False, score

        # ── Pause briefly between turns ──
        print_divider()
        input("\n  Press ENTER for next turn...")
        turn += 1


# ─────────────────────────────────────────────
# MAIN GAME LOOP
# Runs the full game from wave 1 until loss.
# ─────────────────────────────────────────────

def run_game():
    """
    Entry point for the full game.
    Sets up the squad and Commander, then runs
    waves until the player is defeated.
    """
    clear_screen()

    # ── Title screen ──
    print_divider("═")
    print("  ██████  IRON COMMANDER  ██████")
    print("  A Terminal Tank Survival Strategy Game")
    print_divider("═")
    print("""
  You are the Commander. You cannot fire a weapon.
  But without you, your tanks will fall.

  MISSION:
    Survive as many waves of enemy tanks as possible.
    Move across the battlefield to keep your tanks
    alive using health supply and shields.

  SUPPLY:
    Earned by destroying enemies.
    Used to grant HP to your tanks.

  SHIELDS:
    3 charges per wave — refreshes each wave.
    Absorbs 50 damage before breaking.

  GAME OVER:
    Commander destroyed, or all friendly tanks lost.
    """)
    print_divider("═")
    input("  Press ENTER to deploy your squad...")

    # ── Build the squad ──
    squad = [
        ScoutTank(),
        AssaultTank(),
        HeavyTank(),
        ArtilleryTank()
    ]
    commander = Commander()
    commander.position = 1   # Start beside the Assault Tank

    score      = 0
    wave       = 1
    game_over  = False

    # ── Wave progression loop ──
    while not game_over:
        survived, score = run_wave(wave, squad, commander, score)

        if not survived:
            game_over = True
        else:
            wave += 1

            # Small HP restoration between waves
            # (not full heal — keeps pressure on)
            print("\n  Between-wave repairs underway...")
            for tank in squad:
                if tank.is_alive:
                    repair = int(tank.max_hp * 0.15)
                    tank.receive_health(repair)

    # ── Game over screen ──
    clear_screen()
    print_divider("═")
    print("  ██████  GAME OVER  ██████")
    print_divider("═")
    print(f"\n  You survived {wave - 1} wave(s).")
    print(f"  Final score: {score}")
    print_divider()
    commander.print_summary()
    print_divider()

    print("\n  FINAL SQUAD STATUS:")
    for tank in squad:
        status = "SURVIVED" if tank.is_alive else "DESTROYED"
        print(f"  {tank.name:<16} {status}  "
              f"HP: {tank.hp}/{tank.max_hp}")

    print_divider("═")
    print("  Thank you for playing Iron Commander.")
    print_divider("═")


# ─────────────────────────────────────────────
# QUICK TEST
# Tests all display functions and one simulated
# turn without needing player input.
# Command: python battlefield.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from tank import ScoutTank, AssaultTank, HeavyTank, ArtilleryTank

    print("=" * 56)
    print("  IRON COMMANDER — Battlefield Display Test")
    print("=" * 56)

    # Build test squad and enemies
    squad     = [ScoutTank(), AssaultTank(), HeavyTank(), ArtilleryTank()]
    commander = Commander()
    commander.position = 1
    enemies   = [Enforcer(), Raider(), SiegeTank()]

    # Damage some units so display shows variety
    squad[0].take_damage(30)
    squad[2].receive_shield(50)
    enemies[0].take_damage(60)

    # Test all display functions
    print_header(wave=2, turn=3, score=150)
    print_battlefield(squad, enemies, commander)
    print_squad_status(squad, commander)
    print_enemy_status(enemies)
    commander.show_status()

    # Test a simulated friendly fire phase
    print("\n--- Simulated Friendly Fire Phase ---")
    destroyed = friendly_fire_phase(squad, enemies)

    # Test supply phase
    print("\n--- Simulated Supply Phase ---")
    supply_phase(commander, destroyed)

    # Test enemy turn
    print("\n--- Simulated Enemy Turn ---")
    enemy_turn(enemies, squad, commander)

    # Test wave clear check
    for e in enemies:
        e.is_alive = False
    print(f"\n--- Wave Clear Check ---")
    print(f"  Wave cleared: {check_wave_clear(enemies)}")
    print(f"  No loss bonus: {check_no_loss_bonus(squad)}")

    print("\n" + "=" * 56)
    print("  Battlefield test complete.")
    print("  Run main.py to play the full game.")
    print("=" * 56)