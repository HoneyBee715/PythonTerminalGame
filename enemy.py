# enemy.py
# Iron Commander — Enemy Tank Classes
# Phase 3: Core build — Step 2

# We import the base Tank class from tank.py
# Just like an /COPY in RPGLE — brings in the shared structure
from tank import Tank


# ─────────────────────────────────────────────
# BASE ENEMY CLASS
# Inherits everything from Tank, then adds:
#   - supply_reward  : how many supply points the
#                      Commander earns when this
#                      enemy is destroyed
#   - choose_target(): each enemy type overrides
#                      this to pick its own target
#                      from the friendly squad
# ─────────────────────────────────────────────

class EnemyTank(Tank):
    def __init__(self, name, hp, attack, symbol, supply_reward):
        super().__init__(
            name   = name,
            hp     = hp,
            attack = attack,
            symbol = symbol
        )
        self.supply_reward = supply_reward  # Supply earned on kill
        self.is_enemy      = True           # Flag so game loop can tell sides apart

    # ── CHOOSE TARGET ─────────────────────────
    # Base version — targets the nearest alive friendly.
    # Each subclass overrides this with its own logic.
    # friendly_tanks is the list of all friendly Tank objects.
    def choose_target(self, friendly_tanks):
        alive = [t for t in friendly_tanks if t.is_alive]
        if not alive:
            return None
        # Default: pick the first alive tank (nearest by list position)
        return alive[0]

    # ── ATTACK TARGET ─────────────────────────
    # Calls choose_target to find who to hit,
    # then applies damage to that unit.
    # Returns the target that was attacked (or None).
    def perform_attack(self, friendly_tanks):
        target = self.choose_target(friendly_tanks)
        if target is None:
            print(f"  {self.name} has no targets to attack.")
            return None

        print(f"  {self.name} attacks {target.name} for {self.attack} damage!")
        target.take_damage(self.attack)
        return target

    # ── STATUS DISPLAY ─────────────────────────
    # Overrides parent status() to mark as enemy
    def status(self):
        shield_str = f" SH:{self.shield}" if self.shield > 0 else ""
        return f"[{self.symbol}|HP:{self.hp}/{self.max_hp}{shield_str}]"


# ─────────────────────────────────────────────
# ENEMY TYPE 1 — RAIDER
# Fast and dangerous. Ignores friendly tanks and
# goes straight for the Commander. Priority threat
# that must be dealt with immediately.
# Appears from wave 3 onward.
# ─────────────────────────────────────────────

class Raider(EnemyTank):
    """Targets the Commander directly. Highest priority threat."""
    def __init__(self):
        super().__init__(
            name          = "Raider",
            hp            = 50,
            attack        = 20,
            symbol        = "RDR",
            supply_reward = 15
        )
        self.speed = 2  # Moves faster — future use in wave system

    def choose_target(self, friendly_tanks, commander=None):
        # Raider always targets the Commander if one is provided
        # Falls back to nearest friendly tank if Commander is gone
        if commander and commander.is_alive:
            return commander
        alive = [t for t in friendly_tanks if t.is_alive]
        return alive[0] if alive else None


# ─────────────────────────────────────────────
# ENEMY TYPE 2 — ENFORCER
# Standard enemy unit. Targets the nearest
# friendly tank. The most common enemy type,
# appearing from wave 1.
# ─────────────────────────────────────────────

class Enforcer(EnemyTank):
    """Standard enemy. Targets the nearest friendly tank."""
    def __init__(self):
        super().__init__(
            name          = "Enforcer",
            hp            = 100,
            attack        = 30,
            symbol        = "ENF",
            supply_reward = 25
        )

    def choose_target(self, friendly_tanks, commander=None):
        # Targets first alive friendly tank (nearest by position)
        alive = [t for t in friendly_tanks if t.is_alive]
        return alive[0] if alive else None


# ─────────────────────────────────────────────
# ENEMY TYPE 3 — SIEGE TANK
# Slow but devastating. Seeks out the heaviest
# and most armored friendly unit to neutralize
# the squad's biggest defender.
# Appears from wave 7 onward.
# ─────────────────────────────────────────────

class SiegeTank(EnemyTank):
    """Targets the friendly tank with the highest max HP."""
    def __init__(self):
        super().__init__(
            name          = "Siege Tank",
            hp            = 180,
            attack        = 55,
            symbol        = "SGE",
            supply_reward = 50
        )
        self.speed = 0  # Slowest enemy on the battlefield

    def choose_target(self, friendly_tanks, commander=None):
        # Seeks the alive tank with the highest max_hp
        # That is usually the Heavy Tank
        alive = [t for t in friendly_tanks if t.is_alive]
        if not alive:
            return None
        return max(alive, key=lambda t: t.max_hp)


# ─────────────────────────────────────────────
# ENEMY TYPE 4 — HUNTER
# Cunning and opportunistic. Finds whichever
# friendly tank is most damaged and closes in
# for the kill. Forces the Commander to prioritize
# healing carefully.
# Appears from wave 5 onward.
# ─────────────────────────────────────────────

class Hunter(EnemyTank):
    """Targets the most damaged friendly tank — lowest HP percentage."""
    def __init__(self):
        super().__init__(
            name          = "Hunter",
            hp            = 70,
            attack        = 40,
            symbol        = "HNT",
            supply_reward = 30
        )

    def choose_target(self, friendly_tanks, commander=None):
        # Finds the alive tank with the lowest HP percentage
        # Example: Scout at 10/60 (16%) beats Heavy at 50/200 (25%)
        alive = [t for t in friendly_tanks if t.is_alive]
        if not alive:
            return None
        return min(alive, key=lambda t: t.hp / t.max_hp if t.max_hp > 0 else 0)


# ─────────────────────────────────────────────
# WAVE SPAWN HELPER
# Returns a list of enemy tanks for a given wave.
# Wave difficulty increases as the game progresses:
#   Waves 1-2  : Enforcers only
#   Wave 3+    : Raiders introduced
#   Wave 5+    : Hunters introduced
#   Wave 7+    : Siege Tanks introduced
# Each wave also increases enemy count by 1.
# ─────────────────────────────────────────────

import random

def spawn_wave(wave_number):
    """
    Builds and returns a list of enemy tanks for the given wave.
    wave_number: integer starting at 1
    """
    enemies = []

    # Base enemy count grows with each wave (min 2, max 8)
    enemy_count = min(2 + wave_number, 8)

    # Build the pool of available enemy types for this wave
    available = [Enforcer]  # Always available from wave 1

    if wave_number >= 3:
        available.append(Raider)

    if wave_number >= 5:
        available.append(Hunter)

    if wave_number >= 7:
        available.append(SiegeTank)

    # Spawn enemies — always include at least one Enforcer
    enemies.append(Enforcer())

    for _ in range(enemy_count - 1):
        enemy_class = random.choice(available)
        enemies.append(enemy_class())

    print(f"\n  Wave {wave_number} incoming — {len(enemies)} enemy unit(s)!")
    for e in enemies:
        print(f"    {e.name} | HP: {e.hp} | ATK: {e.attack} "
              f"| Reward: +{e.supply_reward} supply")

    return enemies


# ─────────────────────────────────────────────
# QUICK TEST
# Run this file directly to verify all enemy
# classes and wave spawning work correctly.
# Command: python enemy.py
# ─────────────────────────────────────────────

if __name__ == "__main__":

    # Import friendly tanks for targeting tests
    from tank import ScoutTank, AssaultTank, HeavyTank, ArtilleryTank

    print("=" * 55)
    print("  IRON COMMANDER — Enemy Class Test")
    print("=" * 55)

    # ── Create all enemy types ──
    print("\n--- Enemy Unit Stats ---")
    enemies = [Raider(), Enforcer(), SiegeTank(), Hunter()]
    for e in enemies:
        print(f"  {e}")

    # ── Create a friendly squad for targeting tests ──
    scout     = ScoutTank()
    assault   = AssaultTank()
    heavy     = HeavyTank()
    artillery = ArtilleryTank()
    squad     = [scout, assault, heavy, artillery]

    # Damage some tanks so targeting logic has something to work with
    scout.take_damage(45)      # Scout at 15/60  (25% HP)
    assault.take_damage(30)    # Assault at 90/120 (75% HP)

    print("\n--- Friendly Squad HP Before Targeting Test ---")
    for t in squad:
        print(f"  {t.name:<16} {t.hp_bar()}")

    # ── Targeting logic tests ──
    print("\n--- Targeting Logic Test ---")

    raider   = Raider()
    enforcer = Enforcer()
    siege    = SiegeTank()
    hunter   = Hunter()

    r_target = raider.choose_target(squad)
    e_target = enforcer.choose_target(squad)
    s_target = siege.choose_target(squad)
    h_target = hunter.choose_target(squad)

    print(f"  Raider   targets → {r_target.name if r_target else 'None'}"
          f" (goes for Commander — falls back to nearest)")
    print(f"  Enforcer targets → {e_target.name if e_target else 'None'}"
          f" (nearest friendly)")
    print(f"  Siege    targets → {s_target.name if s_target else 'None'}"
          f" (highest max HP)")
    print(f"  Hunter   targets → {h_target.name if h_target else 'None'}"
          f" (lowest HP percentage)")

    # ── Attack test ──
    print("\n--- Attack Test (Enforcer attacks squad) ---")
    enforcer.perform_attack(squad)

    # ── Destruction and supply reward test ──
    print("\n--- Supply Reward Test ---")
    total_supply = 0
    test_enemies = [Raider(), Enforcer(), Hunter(), SiegeTank()]
    for e in test_enemies:
        e.hp = 0
        e.is_alive = False
        total_supply += e.supply_reward
        print(f"  {e.name} destroyed → +{e.supply_reward} supply")
    print(f"  Total supply earned: {total_supply} points")

    # ── Wave spawn tests ──
    print("\n--- Wave Spawn Tests ---")
    for wave in [1, 3, 5, 7]:
        print(f"\n  Spawning wave {wave}:")
        wave_enemies = spawn_wave(wave)

    print("\n" + "=" * 55)
    print("  Enemy class test complete.")
    print("=" * 55)