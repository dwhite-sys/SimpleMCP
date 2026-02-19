# kits/dnd_kit.py
# Dungeons & Dragons tools for SimpleMCP

import random
from utils import tool

# ------------------------------------------------------------
# Dice Rolling
# ------------------------------------------------------------

@tool
def roll_dice(dice: str) -> dict:
    """
    Roll dice using standard DnD notation, e.g. '2d6', '1d20', '4d6'.
    Returns each individual roll and the total.
    """
    try:
        dice = dice.strip().lower()
        num, sides = dice.split("d")
        num = int(num) if num else 1
        sides = int(sides)
        if num < 1 or sides < 1 or num > 100 or sides > 1000:
            return {"error": "Dice values out of range (max 100 dice, max d1000)."}
        rolls = [random.randint(1, sides) for _ in range(num)]
        return {
            "notation": dice,
            "rolls": rolls,
            "total": sum(rolls),
        }
    except Exception as e:
        return {"error": f"Invalid dice notation '{dice}': {e}. Use format like '2d6' or '1d20'."}


# ------------------------------------------------------------
# Character Stat Generation
# ------------------------------------------------------------

@tool
def generate_character_stats() -> dict:
    """
    Roll a full set of D&D 5e ability scores (STR, DEX, CON, INT, WIS, CHA)
    using the standard 4d6-drop-lowest method.
    Also calculates each ability modifier.
    """
    stat_names = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    stats = {}
    for stat in stat_names:
        rolls = [random.randint(1, 6) for _ in range(4)]
        total = sum(sorted(rolls)[1:])  # drop lowest
        modifier = (total - 10) // 2
        stats[stat] = {
            "rolls": rolls,
            "score": total,
            "modifier": modifier,
            "modifier_str": f"+{modifier}" if modifier >= 0 else str(modifier),
        }
    return {"ability_scores": stats}


# ------------------------------------------------------------
# Random Character Name
# ------------------------------------------------------------

_NAMES = {
    "human": ["Aldric", "Brenna", "Cedric", "Daria", "Edwyn", "Fiona", "Gareth", "Helena"],
    "elf": ["Aelindra", "Caladrel", "Erevan", "Faelyn", "Ithilwen", "Lyriel", "Soveliss", "Tindómë"],
    "dwarf": ["Balin", "Dolgrin", "Gurdis", "Helga", "Marta", "Rurik", "Thorin", "Ulfgar"],
    "halfling": ["Cora", "Eldon", "Garret", "Lila", "Merric", "Nora", "Osric", "Pippa"],
    "gnome": ["Alston", "Boddynock", "Dimble", "Ellyjobell", "Fonkin", "Gimble", "Namfoodle", "Zook"],
    "half-orc": ["Dench", "Feng", "Gell", "Henk", "Holg", "Imsh", "Keth", "Murg"],
    "tiefling": ["Akmenos", "Amnon", "Barakas", "Damakos", "Ekemon", "Iados", "Kairon", "Leucis"],
    "dragonborn": ["Arjhan", "Balasar", "Bharash", "Donaar", "Ghesh", "Heskan", "Kriv", "Nadarr"],
}

_SURNAMES = {
    "human": ["Ashwood", "Blackthorn", "Coldwater", "Dunmore", "Fairwind", "Ironforge", "Stormridge"],
    "elf": ["Brightleaf", "Dawnwhisper", "Moonshadow", "Silverbow", "Starweave", "Sunsong"],
    "dwarf": ["Battlehammer", "Copperkettle", "Deepdelve", "Ironmantle", "Stonehewer", "Thunderfist"],
    "halfling": ["Brushgather", "Goodbarrel", "Greenbottle", "High-hill", "Tealeaf", "Thistletop"],
    "gnome": ["Beren", "Daergel", "Folkor", "Garrick", "Nackle", "Murnig", "Ningel", "Raulnor"],
    "half-orc": ["Duskwalker", "Grimstone", "Ironjaw", "Razorclaw", "Shadowpeak", "Steelborn"],
    "tiefling": ["Crowe", "Inferno", "Mourne", "Night", "Rage", "Sorrow", "Thorn", "Void"],
    "dragonborn": ["Clethtinthiallor", "Daardendrian", "Fenkenkabradon", "Kepeshkmolik", "Patinajirrk"],
}

@tool
def random_character_name(race: str) -> dict:
    """
    Generate a random D&D character name for a given race.
    Supported races: human, elf, dwarf, halfling, gnome, half-orc, tiefling, dragonborn.
    """
    race = race.strip().lower()
    if race not in _NAMES:
        return {
            "error": f"Unknown race '{race}'.",
            "supported_races": list(_NAMES.keys()),
        }
    first = random.choice(_NAMES[race])
    last = random.choice(_SURNAMES[race])
    return {"race": race, "name": f"{first} {last}", "first": first, "last": last}


# ------------------------------------------------------------
# Spell Lookup
# ------------------------------------------------------------

_SPELLS = {
    "fireball": {
        "level": 3,
        "school": "Evocation",
        "casting_time": "1 action",
        "range": "150 feet",
        "components": "V, S, M (a tiny ball of bat guano and sulfur)",
        "duration": "Instantaneous",
        "description": (
            "A bright streak flashes from your pointing finger to a point you choose within range "
            "and then blossoms with a low roar into an explosion of flame. Each creature in a "
            "20-foot-radius sphere centered on that point must make a Dexterity saving throw. "
            "A target takes 8d6 fire damage on a failed save, or half as much on a successful one."
        ),
    },
    "magic missile": {
        "level": 1,
        "school": "Evocation",
        "casting_time": "1 action",
        "range": "120 feet",
        "components": "V, S",
        "duration": "Instantaneous",
        "description": (
            "You create three glowing darts of magical force. Each dart hits a creature of your "
            "choice that you can see within range. A dart deals 1d4+1 force damage to its target. "
            "The darts all strike simultaneously."
        ),
    },
    "cure wounds": {
        "level": 1,
        "school": "Evocation",
        "casting_time": "1 action",
        "range": "Touch",
        "components": "V, S",
        "duration": "Instantaneous",
        "description": (
            "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting "
            "ability modifier. This spell has no effect on undead or constructs."
        ),
    },
    "shield": {
        "level": 1,
        "school": "Abjuration",
        "casting_time": "1 reaction",
        "range": "Self",
        "components": "V, S",
        "duration": "1 round",
        "description": (
            "An invisible barrier of magical force appears and protects you. Until the start of "
            "your next turn, you have a +5 bonus to AC, including against the triggering attack, "
            "and you take no damage from magic missile."
        ),
    },
    "counterspell": {
        "level": 3,
        "school": "Abjuration",
        "casting_time": "1 reaction",
        "range": "60 feet",
        "components": "S",
        "duration": "Instantaneous",
        "description": (
            "You attempt to interrupt a creature in the process of casting a spell. If the creature "
            "is casting a spell of 3rd level or lower, its spell fails and has no effect. If it is "
            "casting a spell of 4th level or higher, make an ability check using your spellcasting "
            "ability with a DC equal to 10 + the spell's level. On a success, the spell fails."
        ),
    },
    "misty step": {
        "level": 2,
        "school": "Conjuration",
        "casting_time": "1 bonus action",
        "range": "Self",
        "components": "V",
        "duration": "Instantaneous",
        "description": (
            "Briefly surrounded by silvery mist, you teleport up to 30 feet to an unoccupied "
            "space that you can see."
        ),
    },
    "hold person": {
        "level": 2,
        "school": "Enchantment",
        "casting_time": "1 action",
        "range": "60 feet",
        "components": "V, S, M (a small, straight piece of iron)",
        "duration": "Concentration, up to 1 minute",
        "description": (
            "Choose a humanoid that you can see within range. The target must succeed on a Wisdom "
            "saving throw or be paralyzed for the duration. At the end of each of its turns, the "
            "target can make another Wisdom saving throw. On a success, the spell ends."
        ),
    },
    "detect magic": {
        "level": 1,
        "school": "Divination",
        "casting_time": "1 action (ritual)",
        "range": "Self",
        "components": "V, S",
        "duration": "Concentration, up to 10 minutes",
        "description": (
            "For the duration, you sense the presence of magic within 30 feet of you. If you sense "
            "magic in this way, you can use your action to see a faint aura around any visible "
            "creature or object in the area that bears magic, and you learn its school of magic."
        ),
    },
}

@tool
def lookup_spell(spell_name: str) -> dict:
    """
    Look up details for a D&D 5e spell by name.
    Returns level, school, casting time, range, components, duration, and description.
    """
    key = spell_name.strip().lower()
    spell = _SPELLS.get(key)
    if not spell:
        available = sorted(_SPELLS.keys())
        return {
            "error": f"Spell '{spell_name}' not found.",
            "available_spells": available,
        }
    return {"spell": spell_name.title(), **spell}


# ------------------------------------------------------------
# Monster Stat Block
# ------------------------------------------------------------

_MONSTERS = {
    "goblin": {
        "size": "Small", "type": "humanoid", "alignment": "neutral evil",
        "AC": 15, "HP": "7 (2d6)", "speed": "30 ft.",
        "STR": 8, "DEX": 14, "CON": 10, "INT": 10, "WIS": 8, "CHA": 8,
        "CR": "1/4", "XP": 50,
        "traits": ["Nimble Escape: Can Disengage or Hide as a bonus action."],
        "actions": ["Scimitar: +4 to hit, 1d6+2 slashing.", "Shortbow: +4 to hit, range 80/320 ft., 1d6+2 piercing."],
    },
    "skeleton": {
        "size": "Medium", "type": "undead", "alignment": "lawful evil",
        "AC": 13, "HP": "13 (2d8+4)", "speed": "30 ft.",
        "STR": 10, "DEX": 14, "CON": 15, "INT": 6, "WIS": 8, "CHA": 5,
        "CR": "1/4", "XP": 50,
        "traits": ["Damage Vulnerabilities: bludgeoning.", "Damage Immunities: poison.", "Condition Immunities: exhaustion, poisoned."],
        "actions": ["Shortsword: +4 to hit, 1d6+2 piercing.", "Shortbow: +4 to hit, range 80/320 ft., 1d6+2 piercing."],
    },
    "troll": {
        "size": "Large", "type": "giant", "alignment": "chaotic evil",
        "AC": 15, "HP": "84 (8d10+40)", "speed": "30 ft.",
        "STR": 18, "DEX": 13, "CON": 20, "INT": 7, "WIS": 9, "CHA": 7,
        "CR": "5", "XP": 1800,
        "traits": ["Keen Smell: Advantage on Perception checks using smell.", "Regeneration: Regains 10 HP at start of turn unless it took acid or fire damage."],
        "actions": ["Multiattack: Makes 3 attacks (1 bite, 2 claws).", "Bite: +7 to hit, 1d6+4 piercing.", "Claw: +7 to hit, 2d6+4 slashing."],
    },
    "dragon (young red)": {
        "size": "Large", "type": "dragon", "alignment": "chaotic evil",
        "AC": 18, "HP": "178 (17d10+85)", "speed": "40 ft., climb 40 ft., fly 80 ft.",
        "STR": 23, "DEX": 10, "CON": 21, "INT": 14, "WIS": 11, "CHA": 19,
        "CR": "10", "XP": 5900,
        "traits": ["Fire Immunity.", "Blindsight 30 ft., Darkvision 120 ft."],
        "actions": ["Multiattack: 1 bite + 2 claws.", "Bite: +10 to hit, 2d10+6 piercing + 1d6 fire.", "Claw: +10 to hit, 2d6+6 slashing.", "Fire Breath (Recharge 5–6): 30-ft. cone, DC 18 Dex save, 16d6 fire damage."],
    },
    "beholder": {
        "size": "Large", "type": "aberration", "alignment": "lawful evil",
        "AC": 18, "HP": "180 (19d10+76)", "speed": "0 ft., fly 20 ft. (hover)",
        "STR": 10, "DEX": 14, "CON": 18, "INT": 17, "WIS": 15, "CHA": 17,
        "CR": "13", "XP": 10000,
        "traits": ["Antimagic Cone: The central eye creates a 150-ft. cone of antimagic.", "Regional Effects: The lair warps reality."],
        "actions": ["Bite: +5 to hit, 4d6 piercing.", "Eye Rays: Shoots 3 random magical rays each turn (charm, paralyze, fear, slow, etc.)"],
    },
}

@tool
def get_monster_stats(monster_name: str) -> dict:
    """
    Get the stat block for a D&D 5e monster.
    Available monsters: goblin, skeleton, troll, dragon (young red), beholder.
    """
    key = monster_name.strip().lower()
    monster = _MONSTERS.get(key)
    if not monster:
        return {
            "error": f"Monster '{monster_name}' not found.",
            "available_monsters": list(_MONSTERS.keys()),
        }
    return {"monster": monster_name.title(), **monster}


# ------------------------------------------------------------
# Random Encounter Generator
# ------------------------------------------------------------

_ENCOUNTERS = {
    "forest": [
        "A pack of 1d4+2 wolves stalks you through the undergrowth.",
        "A green hag offers you a trade — her knowledge for a secret.",
        "2d6 goblins set up an ambush from the treetops.",
        "A wounded unicorn is trapped in a hunter's snare.",
        "A will-o'-wisp leads you in circles.",
        "A dryad demands you explain why you are in her grove.",
    ],
    "dungeon": [
        "1d6 skeletons animate as you enter the chamber.",
        "A mimic disguised as a treasure chest waits patiently.",
        "A gelatinous cube fills the corridor ahead.",
        "Rival adventurers claim this floor is already theirs.",
        "A trapped pit hides a long-dead adventurer's belongings.",
        "A ghost relives its final moments and begs for closure.",
    ],
    "city": [
        "A pickpocket bumps into you — roll a DC 14 Perception check.",
        "A town crier announces a bounty for your capture.",
        "A disguised assassin sits across from you at the tavern.",
        "The city guard demands to inspect your belongings.",
        "A merchant offers a suspicious 'deal of a lifetime'.",
        "A street urchin slips a cryptic note into your pocket.",
    ],
    "sea": [
        "A kraken tentacle rises alongside the ship.",
        "Pirates flying a black flag approach at full sail.",
        "A siren's song drifts across the fog.",
        "A sea hag surfaces and curses one crew member.",
        "A ghost ship passes silently, crewed by the undead.",
        "A water elemental rises from a sudden maelstrom.",
    ],
}

@tool
def random_encounter(environment: str) -> dict:
    """
    Generate a random encounter for a given environment.
    Supported environments: forest, dungeon, city, sea.
    """
    key = environment.strip().lower()
    options = _ENCOUNTERS.get(key)
    if not options:
        return {
            "error": f"Unknown environment '{environment}'.",
            "supported_environments": list(_ENCOUNTERS.keys()),
        }
    return {"environment": key, "encounter": random.choice(options)}


# ------------------------------------------------------------
# Condition Reference
# ------------------------------------------------------------

_CONDITIONS = {
    "blinded": "A blinded creature can't see and automatically fails any ability check that requires sight. Attack rolls against it have advantage, and its attack rolls have disadvantage.",
    "charmed": "A charmed creature can't attack the charmer or target them with harmful abilities or effects. The charmer has advantage on social checks against the creature.",
    "deafened": "A deafened creature can't hear and automatically fails any ability check requiring hearing.",
    "exhaustion": (
        "Exhaustion has 6 levels: 1-Disadvantage on ability checks, 2-Speed halved, "
        "3-Disadvantage on attack rolls and saving throws, 4-HP max halved, 5-Speed reduced to 0, "
        "6-Death. Each long rest removes one level."
    ),
    "frightened": "A frightened creature has disadvantage on ability checks and attack rolls while the source of its fear is within line of sight. It can't willingly move closer to the source.",
    "grappled": "A grappled creature's speed becomes 0. The condition ends if the grappler is incapacitated or if the creature is moved out of reach.",
    "incapacitated": "An incapacitated creature can't take actions or reactions.",
    "invisible": "An invisible creature is impossible to see without special senses. It has advantage on attack rolls; attacks against it have disadvantage.",
    "paralyzed": "A paralyzed creature is incapacitated, can't move or speak, automatically fails STR and DEX saves, attacks against it have advantage, and hits within 5 ft. are critical hits.",
    "petrified": "A petrified creature is transformed into stone, incapacitated, and has resistance to all damage. It automatically fails STR and DEX saves.",
    "poisoned": "A poisoned creature has disadvantage on attack rolls and ability checks.",
    "prone": "A prone creature's only movement option is crawling. It has disadvantage on attack rolls. Attacks against it have advantage if within 5 ft., otherwise disadvantage.",
    "restrained": "A restrained creature's speed becomes 0. Attack rolls against it have advantage; its attack rolls have disadvantage. It has disadvantage on DEX saving throws.",
    "stunned": "A stunned creature is incapacitated, can't move, and can only speak falteringly. It automatically fails STR and DEX saves; attacks against it have advantage.",
    "unconscious": "An unconscious creature is incapacitated, can't move or speak, is unaware of its surroundings, drops held items, falls prone, and automatically fails STR and DEX saves. Attacks have advantage and hits within 5 ft. are critical hits.",
}

@tool
def lookup_condition(condition: str) -> dict:
    """
    Look up the rules for a D&D 5e condition (e.g. 'blinded', 'paralyzed', 'poisoned').
    """
    key = condition.strip().lower()
    description = _CONDITIONS.get(key)
    if not description:
        return {
            "error": f"Condition '{condition}' not found.",
            "available_conditions": sorted(_CONDITIONS.keys()),
        }
    return {"condition": condition.title(), "description": description}


# ------------------------------------------------------------
# End of dnd_kit.py
# ------------------------------------------------------------
