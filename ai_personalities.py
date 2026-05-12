"""Tunable Risk AI personalities and board heuristics.

The game engine imports this module only for weights. Adjusting these values
changes AI behaviour without touching app.py or the UI.
"""

AI_PERSONALITIES = {
    "Balanced General": {
        "risk": 0.4,
        "attack_bias": 0.6,
        "defense_bias": 0.8,
        "continent_bias": 0.9,
        "card_hunter": 0.75,
        "mission_focus": 0.7,
        "opportunism": 0.6,
        "choke_bias": 0.8,
        "trade_eagerness": 0.3,
        "advance_bias": 0.5,
    },
    "Cautious Defender": {
        "risk": 0.3,
        "attack_bias": 0.45,
        "defense_bias": 0.9,
        "continent_bias": 0.95,
        "card_hunter": 0.5,
        "mission_focus": 0.95,
        "opportunism": 0.4,
        "choke_bias": 0.9,
        "trade_eagerness": 0.7,
        "advance_bias": 0.25,
    },
    "Aggressive Expansionist": {
        "risk": 0.8,
        "attack_bias": 0.9,
        "defense_bias": 0.3,
        "continent_bias": 0.8,
        "card_hunter": 0.9,
        "mission_focus": 0.7,
        "opportunism": 0.9,
        "choke_bias": 0.5,
        "trade_eagerness": 0.7,
        "advance_bias": 0.9,
    },
    "Continental Strategist": {
        "risk": 0.4,
        "attack_bias": 0.5,
        "defense_bias": 0.75,
        "continent_bias": 1.1,
        "card_hunter": 0.4,
        "mission_focus": 0.95,
        "opportunism": 0.5,
        "choke_bias": 0.9,
        "trade_eagerness": 0.4,
        "advance_bias": 0.6,
    },
    "Mission Fanatic": {
        "risk": 0.7,
        "attack_bias": 0.7,
        "defense_bias": 0.6,
        "continent_bias": 0.7,
        "card_hunter": 0.5,
        "mission_focus": 0.9,
        "opportunism": 0.6,
        "choke_bias": 0.6,
        "trade_eagerness": 0.6,
        "advance_bias": 0.75,
    },
    "Opportunist Assassin": {
        "risk": 0.75,
        "attack_bias": 0.8,
        "defense_bias": 0.4,
        "continent_bias": 0.8,
        "card_hunter": 1,
        "mission_focus": 0.75,
        "opportunism": 0.95,
        "choke_bias": 0.6,
        "trade_eagerness": 0.8,
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
    "alaska": 0.65,
    "kamchatka": 0.80,
    "central_america": 0.85,
    "brazil": 0.9,
    "venezuela": 0.9,
    "north_africa": 0.6,
    "east_africa": 0.5,
    "egypt": 0.7,
    "middle_east": 0.8,
    "ukraine": 0.7,
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
    "setup_overstack_penalty": 1.1,
    "reinforce_overstack_penalty": 0.6,

    # Pull idle rear armies toward useful borders, choke points and mission
    # fronts during fortification.
    "frontier_redeploy_bias": 1.1,
    "safe_stack_drain": 1.2,
    "friendly_path_fortify": 1.0,
}
