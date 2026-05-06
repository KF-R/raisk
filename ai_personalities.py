"""Tunable Risk AI personalities and board heuristics.

The game engine imports this module only for weights. Adjusting these values
changes AI behaviour without touching app.py or the UI.
"""

AI_PERSONALITIES = {
    "Balanced General": {
        "risk": 0.52,
        "attack_bias": 0.55,
        "defense_bias": 0.55,
        "continent_bias": 0.55,
        "card_hunter": 0.55,
        "mission_focus": 0.60,
        "opportunism": 0.55,
        "choke_bias": 0.55,
        "trade_eagerness": 0.45,
        "advance_bias": 0.55,
    },
    "Cautious Defender": {
        "risk": 0.24,
        "attack_bias": 0.28,
        "defense_bias": 0.95,
        "continent_bias": 0.70,
        "card_hunter": 0.24,
        "mission_focus": 0.55,
        "opportunism": 0.32,
        "choke_bias": 0.82,
        "trade_eagerness": 0.62,
        "advance_bias": 0.25,
    },
    "Aggressive Expansionist": {
        "risk": 0.86,
        "attack_bias": 0.96,
        "defense_bias": 0.25,
        "continent_bias": 0.42,
        "card_hunter": 0.90,
        "mission_focus": 0.58,
        "opportunism": 0.92,
        "choke_bias": 0.35,
        "trade_eagerness": 0.35,
        "advance_bias": 0.90,
    },
    "Continental Strategist": {
        "risk": 0.50,
        "attack_bias": 0.50,
        "defense_bias": 0.68,
        "continent_bias": 0.96,
        "card_hunter": 0.38,
        "mission_focus": 0.72,
        "opportunism": 0.48,
        "choke_bias": 0.78,
        "trade_eagerness": 0.46,
        "advance_bias": 0.55,
    },
    "Mission Fanatic": {
        "risk": 0.66,
        "attack_bias": 0.68,
        "defense_bias": 0.42,
        "continent_bias": 0.45,
        "card_hunter": 0.58,
        "mission_focus": 1.00,
        "opportunism": 0.65,
        "choke_bias": 0.40,
        "trade_eagerness": 0.52,
        "advance_bias": 0.70,
    },
    "Opportunist Assassin": {
        "risk": 0.72,
        "attack_bias": 0.78,
        "defense_bias": 0.34,
        "continent_bias": 0.30,
        "card_hunter": 0.92,
        "mission_focus": 0.82,
        "opportunism": 1.00,
        "choke_bias": 0.28,
        "trade_eagerness": 0.40,
        "advance_bias": 0.78,
    },
}

# Default personality by player colour / number.
DEFAULT_PERSONALITY_BY_PLAYER = {
    1: "Aggressive Expansionist",   # Crimson
    2: "Balanced General",          # Royal Blue
    3: "Continental Strategist",    # Rifle Green
    4: "Mission Fanatic",           # Imperial Gold
    5: "Cautious Defender",         # Prussian Black
    6: "Opportunist Assassin",      # Rose
}

# Manual map weights are deliberately transparent and easy to tune. Higher
# values make an AI more likely to reinforce/hold/advance into the territory.
CHOKE_VALUES = {
    "alaska": 0.6,
    "kamchatka": 0.80,
    "central_america": 0.80,
    "brazil": 0.9,
    "venezuela": 0.9,
    "north_africa": 0.4,
    "egypt": 0.7,
    "middle_east": 0.8,
    "ukraine": 0.75,
    "southern_europe": 0.5,
    "western_europe": 0.5,
    "afghanistan": 0.5,
    "siam": 0.95,
    "indonesia": 0.95,
    "greenland": 0.7,
    "iceland": 0.7,
}
