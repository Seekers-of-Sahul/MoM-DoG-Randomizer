"""Hand-written monster families for Archipelago "monster" items.

A family item gives the player one monster from that family. Which member depends on how far the player is:
the deepest stage of the family whose base level is <= the target level (see pick()), so a family received
early gives a weak form and the same item received late gives a strong one. Stages hold alternatives
(branches of the evolution tree); one is picked at random.

Each family:  name, weight (relative chance among monster items), terrain, stages (list of lists of monster ids).
  terrain: 'land', 'water', 'river', 'deep' - informational only. Water monsters are given anywhere
           (the player can fix them with a Wing Ring).
  Weights: common lines 3, strong or awkward lines 2, rare/odd monsters 1.
Base levels come from MONST.TBL (with the rebalance's Goblin line 1 > 8 > 25); keep in sync with BASE below.
The human class tree is tangled (Priest and Sorcerer link most lines); each family follows one natural line
and the shared classes are listed only where they belong in the fiction.
"""

FAMILIES = [
    # ---- humans ----
    ('Soldiers',      3, 'land', [[3], [4], [5, 8], [6, 9], [7]]),          # Soldier > Fighter > Knight/Swordsman > Paladin/Samurai > Dragon Slayer
    ('Barbarians',    3, 'land', [[13], [14, 10], [15], [16, 11]]),         # Barbarian > Berserker/Thief > Death Knight > Destroyer/Ninja
    ('Magicians',     3, 'land', [[17], [18], [19], [20]]),                 # Magician > Shaman > Wizard > High Wizard
    ('Clergy',        3, 'land', [[22], [23], [24, 26], [25]]),             # Ancient > Priest > Monk/Sorcerer > Lord
    ('Amazons',       3, 'land', [[27], [28], [29], [30]]),                 # Amazon > Huntress > Valkyrie > Avator
    ('Witches',       3, 'land', [[31], [32], [33], [34]]),                 # Witch > Mage > Mystic > Bishop
    ('Sisters',       2, 'land', [[35], [36], [37]]),                       # Neophyte > Priestess > Cleric
    # ---- celestial / demonic ----
    ('Demons',        2, 'land', [[38], [39], [40], [41], [42]]),           # Gremlin > Imp > Lesser > Greater Demon > Necron
    ('Angels',        2, 'land', [[44], [45], [46], [47, 48]]),             # Cherub > Blessed Angel > Angel Soldier > Angel Warrior/Archangel
    ('Fairies',       3, 'land', [[56], [57], [58], [59], [60]]),           # Fairy > Pixie > High Pixie > Pixie Warrior > Pixie Lord
    ('Elves',         3, 'land', [[50], [51, 55], [52], [53], [54]]),       # Elf > High Elf/Elf Lord > Master Elf > Dark Elf > Death Elf
    ('Djinn',         1, 'land', [[89], [90]]),                             # Genie > Efreeti
    # ---- undead ----
    ('Ghosts',        3, 'land', [[80], [81], [82], [83, 85], [84]]),       # Ghost > Apparition > Wraith > Phantom/Dark Wraith > Spectre
    ('Night Ladies',  2, 'land', [[86], [87], [88]]),                       # Banshee > Vampire > Succubus
    ('Bones',         3, 'land', [[91], [92], [93]]),                       # Skeleton > Zombie > Mummy
    ('Lich',          1, 'land', [[21]]),
    # ---- beasts ----
    ('Giants',        3, 'land', [[61], [62], [63], [64]]),                 # Troll > Giant > Cyclops > Colossus
    ('Frost Giants',  1, 'land', [[65], [66]]),                             # Ice Giant > Ice Colossus
    ('Steeds',        3, 'land', [[67], [68], [69], [70]]),                 # Unicorn > Pegasus > Griffin > Hippogriff
    ('Birds',         3, 'land', [[71], [72, 74], [73, 75]]),               # Roc > Firebird/Thunderbird > Phoenix/Cockatrice
    ('Hounds',        2, 'land', [[76], [77], [78]]),                       # Hell Hound > Hound > Cerberus
    ('Wolves',        2, 'land', [[126], [79]]),                            # Wolfwere > Werewolf
    ('Goblins',       3, 'land', [[127], [128], [129]]),                    # Goblin > Orc > Overlord
    ('Chimeras',      2, 'land', [[120, 121], [122], [123], [124]]),        # Harpy/Peryton > Chimera > Manticore > Sphinx
    ('Brutes',        1, 'land', [[125, 134], [131]]),                      # Minotaur/Slime > Wragnor
    ('Constructs',    1, 'land', [[130, 43]]),                              # Golem/Gargoyle (both lv 10+, no evolutions)
    # ---- dragons ----
    ('Fire Dragons',  2, 'land', [[94], [95], [96], [97], [98]]),           # Dragon > Salamander > Fire Dragon > Death Dragon > Tiamat
    ('Sky Dragons',   2, 'land', [[99], [100, 103], [101, 104], [102, 105]]),  # Wyvern > Green Dragon/Naga > Cloud Dragon/Kirin > Bahamut/Wyrmus
    ('Lizardmen',     1, 'land', [[106], [107]]),                           # Lizardman > King Dragon (lv 30)
    ('Dragon Knight', 1, 'land', [[12]]),
    ('Angel Knight',  1, 'land', [[49]]),
    # ---- water ----
    ('Sea Serpents',  2, 'water', [[108], [109], [110], [111, 112]]),       # Serpent > Sea Dragon > Dyicon > Leviathan/Hydra
    ('Cephalopods',   2, 'water', [[113], [114], [115], [116]]),            # Octopus > Tentacles > Giant Squid > Kraken
    ('Merfolk',       2, 'river', [[117], [118], [119]]),                   # Mermaid > Reef Mermaid > Siren
    ('Deep Ones',     1, 'deep',  [[132], [133, 135]]),                     # Chaos Crab > Feather Fin/Manta
]

# Base levels (MONST.TBL, after the rebalance). Enemy-only/story ids (0-2, 136-148) are never given.
BASE = {
    3: 1, 4: 5, 5: 9, 6: 15, 7: 20, 8: 9, 9: 15, 10: 5, 11: 15, 12: 9, 13: 1, 14: 5, 15: 10, 16: 16,
    17: 1, 18: 5, 19: 9, 20: 15, 21: 20, 22: 1, 23: 5, 24: 10, 25: 15, 26: 10, 27: 1, 28: 5, 29: 11, 30: 16,
    31: 1, 32: 5, 33: 10, 34: 15, 35: 1, 36: 5, 37: 10, 38: 1, 39: 6, 40: 13, 41: 20, 42: 20, 43: 13,
    44: 1, 45: 7, 46: 15, 47: 22, 48: 22, 49: 15, 50: 1, 51: 7, 52: 16, 53: 17, 54: 24, 55: 7,
    56: 1, 57: 5, 58: 10, 59: 15, 60: 20, 61: 1, 62: 7, 63: 15, 64: 23, 65: 15, 66: 22,
    67: 1, 68: 8, 69: 13, 70: 17, 71: 1, 72: 5, 73: 13, 74: 5, 75: 13, 76: 5, 77: 11, 78: 18, 79: 11,
    80: 1, 81: 4, 82: 7, 83: 11, 84: 16, 85: 11, 86: 1, 87: 8, 88: 15, 89: 8, 90: 16, 91: 1, 92: 9, 93: 16,
    94: 1, 95: 6, 96: 13, 97: 20, 98: 26, 99: 6, 100: 14, 101: 21, 102: 25, 103: 14, 104: 22, 105: 26,
    106: 6, 107: 30, 108: 1, 109: 8, 110: 14, 111: 20, 112: 22, 113: 1, 114: 7, 115: 13, 116: 19,
    117: 1, 118: 8, 119: 15, 120: 1, 121: 1, 122: 6, 123: 13, 124: 20, 125: 1, 126: 1, 127: 1, 128: 8,
    129: 25, 130: 10, 131: 8, 132: 8, 133: 11, 134: 1, 135: 11,
}

# Target level by story stage: roughly the level the player's monsters reach there (stage 0..28, extras 26-28).
STAGE_LEVEL = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24,
               24, 24, 24, 11, 15, 18]


def pick(rng, family, level):
    """Monster id and level to give for a family item at target `level`.
    Takes the deepest stage whose members all have base <= level (at least the first stage), then one member
    of it at random. The unit is created at max(base, level) like a summon."""
    stages = dict((f[0], f[3]) for f in FAMILIES)[family]
    best = stages[0]
    for st in stages[1:]:
        ok = [m for m in st if BASE[m] <= level]
        if not ok: break
        best = ok
    m = rng.choice(best)
    return m, max(BASE[m], level)


def item_pool(rng, n, allow=('land', 'water', 'river', 'deep')):
    """n family names drawn by weight (with repeats), restricted to the given terrains."""
    fams = [f for f in FAMILIES if f[2] in allow]
    return rng.choices([f[0] for f in fams], weights=[f[1] for f in fams], k=n)
