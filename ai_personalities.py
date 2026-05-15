"""Tunable Risk AI personalities and board heuristics.

The game engine imports this module only for weights. Adjusting these values
changes AI behaviour without touching app.py or the UI.
"""

AI_PERSONALITIES = {
    "Balanced General": {
        "risk": 0.5,
        "attack_bias": 0.55,
        "defense_bias": 0.55,
        "continent_bias": 0.9,
        "card_hunter": 0.75,
        "mission_focus": 0.6,
        "opportunism": 0.55,
        "choke_bias": 0.8,
        "trade_eagerness": 0.25,
        "advance_bias": 0.5,
    },
    "Cautious Defender": {
        "risk": 0.3,
        "attack_bias": 0.4,
        "defense_bias": 0.8,
        "continent_bias": 0.8,
        "card_hunter": 0.4,
        "mission_focus": 0.6,
        "opportunism": 0.3,
        "choke_bias": 0.8,
        "trade_eagerness": 0.6,
        "advance_bias": 0.25,
    },
    "Aggressive Expansionist": {
        "risk": 0.85,
        "attack_bias": 0.95,
        "defense_bias": 0.2,
        "continent_bias": 0.7,
        "card_hunter": 0.90,
        "mission_focus": 0.6,
        "opportunism": 0.9,
        "choke_bias": 0.5,
        "trade_eagerness": 0.25,
        "advance_bias": 0.90,
    },
    "Continental Strategist": {
        "risk": 0.50,
        "attack_bias": 0.5,
        "defense_bias": 0.5,
        "continent_bias": 1,
        "card_hunter": 0.3,
        "mission_focus": 0.85,
        "opportunism": 0.5,
        "choke_bias": 0.9,
        "trade_eagerness": 0.5,
        "advance_bias": 0.6,
    },
    "Mission Fanatic": {
        "risk": 0.7,
        "attack_bias": 0.7,
        "defense_bias": 0.4,
        "continent_bias": 0.7,
        "card_hunter": 0.5,
        "mission_focus": 1,
        "opportunism": 0.6,
        "choke_bias": 0.6,
        "trade_eagerness": 0.6,
        "advance_bias": 0.75,
    },
    "Opportunist Assassin": {
        "risk": 0.75,
        "attack_bias": 0.8,
        "defense_bias": 0.4,
        "continent_bias": 0.6,
        "card_hunter": 0.95,
        "mission_focus": 0.7,
        "opportunism": 0.95,
        "choke_bias": 0.5,
        "trade_eagerness": 0.60,
        "advance_bias": 0.8,
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


# Higher-level AI behaviour knobs used by app.py.  These are deliberately
# separate from personality flavour weights: they tune the evaluator's
# situational awareness and logistics, not a commander's temperament.
STRATEGIC_WEIGHTS = {
    # React to opponents taking continents/choke points and building pressure.
    "reactivity": 1.0,
    "enemy_continent_alert": 1.0,

    # Discourage repeated setup/reinforcement stacking once a territory is
    # adequately garrisoned for its local threat level.
    "setup_overstack_penalty": 1.15,
    "reinforce_overstack_penalty": 0.65,

    # Pull idle rear armies toward useful borders, choke points and mission
    # fronts during fortification.
    "frontier_redeploy_bias": 1.0,
    "safe_stack_drain": 1.0,
    "friendly_path_fortify": 1.0,
}
