from __future__ import annotations

from html import escape
from pathlib import Path
from itertools import combinations
from random import randint, random, shuffle
import re
import time
import uuid

from flask import Flask, jsonify, render_template, request, Response

from ai_personalities import AI_PERSONALITIES, CHOKE_VALUES, DEFAULT_PERSONALITY_BY_PLAYER, STRATEGIC_WEIGHTS

app = Flask(__name__)

# territory_owner is a player number, territory_strength is army count.
PLAYER_COLOURS = {
    0: {"name": "Unclaimed", "path": "#d9c8a8", "army": "none", "ink": "#2a2117"},
    1: {"name": "Crimson", "path": "#8f1d24", "army": "#b21f2d", "ink": "#fff2df"},
    2: {"name": "Royal Blue", "path": "#1e4f8f", "army": "#2563b8", "ink": "#fff2df"},
    3: {"name": "Rifle Green", "path": "#2f6a3f", "army": "#397d4a", "ink": "#fff2df"},
    4: {"name": "Imperial Gold", "path": "#d6aa32", "army": "#f0c541", "ink": "#23180d"},
    5: {"name": "Prussian Black", "path": "#504058", "army": "#111111", "ink": "#fff2df"},
    6: {"name": "Rose", "path": "#c46c9c", "army": "#e58abb", "ink": "#23180d"},
}

# safe_name, display_name, label_x, label_y, army_offset_x, army_offset_y, territory_owner, territory_strength, neighbours
BLANK_MAP_DATA = [
    ("alaska", "Alaska", 223, 213, 4, 0, 0, 0, ["northwest_territory", "alberta", "kamchatka"]),
    ("alberta", "Alberta", 287, 256, -1, -1, 0, 0, ["alaska", "northwest_territory", "ontario", "western_us"]),
    ("central_america", "Central\nAmerica", 298, 351, 7, 46, 0, 0, ["western_us", "eastern_us", "venezuela"]),
    ("eastern_us", "Eastern\nUS", 342, 316, -4, 2, 0, 0, ["ontario", "quebec", "western_us", "central_america"]),
    ("greenland", "Greenland", 433, 180, 0, 38, 0, 0, ["northwest_territory", "ontario", "quebec", "iceland"]),
    ("northwest_territory", "Northwest\nTerritory", 300, 200, -15, 2, 0, 0, ["alaska", "alberta", "ontario", "greenland"]),
    ("ontario", "Ontario", 336, 261, 1, 2, 0, 0, ["northwest_territory", "alberta", "western_us", "eastern_us", "quebec", "greenland"]),
    ("quebec", "Quebec", 387, 255, -5, 2, 0, 0, ["ontario", "eastern_us", "greenland"]),
    ("western_us", "Western\nUS", 285, 303, 6, -1, 0, 0, ["alberta", "ontario", "eastern_us", "central_america"]),

    ("argentina", "Argen-\ntina", 367, 515, -11, 49, 0, 0, ["peru", "brazil"]),
    ("brazil", "Brazil", 407, 463, 0, -1, 0, 0, ["venezuela", "peru", "argentina", "north_africa"]),
    ("venezuela", "Venezuela", 355, 403, -2, 2, 0, 0, ["central_america", "peru", "brazil"]),
    ("peru", "Peru", 367, 476, -23, 5, 0, 0, ["venezuela", "brazil", "argentina"]),

    ("great_britain", "Great\nBritain", 462, 262, 23, 47, 0, 0, ["iceland", "scandinavia", "northern_europe", "western_europe"]),
    ("iceland", "Iceland", 485, 225, 6, 2, 0, 0, ["greenland", "great_britain", "scandinavia"]),
    ("northern_europe", "Northern\nEurope", 538, 293, 12, 2, 0, 0, ["great_britain", "scandinavia", "ukraine", "southern_europe", "western_europe"]),
    ("scandinavia", "Scandi-\nnavia", 553, 203, -15, 48, 0, 0, ["iceland", "great_britain", "northern_europe", "ukraine"]),
    ("southern_europe", "Southern\nEurope", 549, 340, 6, 2, 0, 0, ["western_europe", "northern_europe", "ukraine", "middle_east", "egypt", "north_africa"]),
    ("ukraine", "Ukraine", 615, 260, -12, 45, 0, 0, ["scandinavia", "northern_europe", "southern_europe", "middle_east", "afghanistan", "ural"]),
    ("western_europe", "Western\nEurope", 480, 350, 22, -3, 0, 0, ["great_britain", "northern_europe", "southern_europe", "north_africa"]),

    ("congo", "Congo", 571, 501, 2, 0, 0, 0, ["north_africa", "east_africa", "south_africa"]),
    ("east_africa", "East\nAfrica", 606, 459, -6, -1, 0, 0, ["egypt", "north_africa", "congo", "south_africa", "madagascar", "middle_east"]),
    ("egypt", "Egypt", 578, 417, -4, 0, 0, 0, ["southern_europe", "north_africa", "east_africa", "middle_east"]),
    ("madagascar", "Mada-\ngascar", 638, 559, 9, 0, 0, 0, ["east_africa", "south_africa"]),
    ("north_africa", "North\nAfrica", 515, 432, -2, -3, 0, 0, ["brazil", "western_europe", "southern_europe", "egypt", "east_africa", "congo"]),
    ("south_africa", "South\nAfrica", 580, 562, 0, 0, 0, 0, ["congo", "east_africa", "madagascar"]),

    ("afghanistan", "Afgha-\nnistan", 674, 315, 0, 0, 0, 0, ["ukraine", "ural", "china", "india", "middle_east"]),
    ("china", "China", 757, 357, 0, 0, 0, 0, ["afghanistan", "ural", "siberia", "mongolia", "siam", "india"]),
    ("india", "India", 715, 394, 0, 0, 0, 0, ["middle_east", "afghanistan", "china", "siam"]),
    ("irkutsk", "Irkutsk", 758, 260, 11, 0, 0, 0, ["siberia", "yakutsk", "kamchatka", "mongolia"]),
    ("japan", "Japan", 853, 293, 0, 0, 0, 0, ["kamchatka", "mongolia"]),
    ("kamchatka", "Kamchatka", 843, 205, -5, 0, 0, 0, ["alaska", "yakutsk", "irkutsk", "mongolia", "japan"]),
    ("middle_east", "Middle\nEast", 627, 379, 0, 0, 0, 0, ["southern_europe", "ukraine", "afghanistan", "india", "east_africa", "egypt"]),
    ("mongolia", "Mongolia", 777, 303, 15, 0, 0, 0, ["siberia", "irkutsk", "kamchatka", "japan", "china"]),
    ("siam", "Siam", 771, 409, -2, 0, 0, 0, ["india", "china", "indonesia"]),
    ("siberia", "Siberia", 723, 215, -4, -3, 0, 0, ["ural", "china", "mongolia", "irkutsk", "yakutsk"]),
    ("ural", "Ural", 683, 250, -2, -2, 0, 0, ["ukraine", "afghanistan", "china", "siberia"]),
    ("yakutsk", "Yakutsk", 779, 194, 0, 0, 0, 0, ["siberia", "irkutsk", "kamchatka"]),

    ("eastern_australia", "Eastern\nAustralia", 855, 535, 16, 51, 0, 0, ["new_guinea", "western_australia"]),
    ("new_guinea", "New\nGuinea", 848, 468, 0, 0, 0, 0, ["indonesia", "western_australia", "eastern_australia"]),
    ("indonesia", "Indonesia", 754, 492, 0, 0, 0, 0, ["siam", "new_guinea", "western_australia"]),
    ("western_australia", "Western\nAustralia", 810, 559, 0, 0, 0, 0, ["indonesia", "new_guinea", "eastern_australia"]),
]

TERRITORY_ORDER = [row[0] for row in BLANK_MAP_DATA]
TERRITORY_INFO = {
    safe: {
        "safe_name": safe,
        "name": name.replace("\n", " "),
        "formatted_name": name,
        "x": x,
        "y": y,
        "army_offset_x": ax,
        "army_offset_y": ay,
        "neighbours": neighbours,
    }
    for safe, name, x, y, ax, ay, _owner, _strength, neighbours in BLANK_MAP_DATA
}

CONTINENTS = {
    "North America": ["alaska", "alberta", "central_america", "eastern_us", "greenland", "northwest_territory", "ontario", "quebec", "western_us"],
    "South America": ["argentina", "brazil", "venezuela", "peru"],
    "Europe": ["great_britain", "iceland", "northern_europe", "scandinavia", "southern_europe", "ukraine", "western_europe"],
    "Africa": ["congo", "east_africa", "egypt", "madagascar", "north_africa", "south_africa"],
    "Asia": ["afghanistan", "china", "india", "irkutsk", "japan", "kamchatka", "middle_east", "mongolia", "siam", "siberia", "ural", "yakutsk"],
    "Australia": ["eastern_australia", "new_guinea", "indonesia", "western_australia"],
}
CONTINENT_BONUS = {"North America": 5, "South America": 2, "Europe": 5, "Africa": 3, "Asia": 7, "Australia": 2}
TERRITORY_CONTINENT = {safe: continent for continent, terrs in CONTINENTS.items() for safe in terrs}
INITIAL_ARMIES = {2: 40, 3: 35, 4: 30, 5: 25, 6: 20}
CARD_TYPES = ["infantry", "cavalry", "artillery"]
CARD_ICONS = {"infantry": "♟", "cavalry": "♞", "artillery": "✹"}
TRADE_VALUES = [4, 6, 8, 10, 12, 15]
STAT_DEFAULTS = {
    "reinforcements_received": 0,
    "trade_armies": 0,
    "trade_bonus_armies": 0,
    "cards_drawn": 0,
    "cards_traded": 0,
    "attacks": 0,
    "territories_conquered": 0,
    "territories_lost": 0,
    "armies_lost": 0,
    "moves": 0,
}

MISSION_DECK = [
    {"id": "occupy_24", "kind": "occupy", "count": 24, "min_strength": 1, "text": "Occupy 24 Territories of your choice."},
    {"id": "na_africa", "kind": "continents", "continents": ["North America", "Africa"], "text": "Conquer the Continents of North America and Africa."},
    {"id": "na_australia", "kind": "continents", "continents": ["North America", "Australia"], "text": "Conquer the Continents of North America and Australia."},
    {"id": "asia_africa", "kind": "continents", "continents": ["Asia", "Africa"], "text": "Conquer the Continents of Asia and Africa."},
    {"id": "asia_south_america", "kind": "continents", "continents": ["Asia", "South America"], "text": "Conquer the Continents of Asia and South America."},
    {"id": "occupy_18_two", "kind": "occupy", "count": 18, "min_strength": 2, "text": "Conquer 18 Territories of your choice and Occupy each with at least 2 Armies."},
    {"id": "destroy_red", "kind": "destroy", "target": 1, "target_name": "Red", "text": "Destroy all Red Armies. If yours are the Red Armies, then: Occupy 24 Territories of your choice."},
    {"id": "destroy_blue", "kind": "destroy", "target": 2, "target_name": "Blue", "text": "Destroy all Blue Armies. If yours are the Blue Armies, then: Occupy 24 Territories of your choice."},
    {"id": "destroy_green", "kind": "destroy", "target": 3, "target_name": "Green", "text": "Destroy all Green Armies. If yours are the Green Armies, then: Occupy 24 Territories of your choice."},
    {"id": "destroy_yellow", "kind": "destroy", "target": 4, "target_name": "Yellow", "text": "Destroy all Yellow Armies. If yours are the Yellow Armies, then: Occupy 24 Territories of your choice."},
    {"id": "destroy_black", "kind": "destroy", "target": 5, "target_name": "Black", "text": "Destroy all Black Armies. If yours are the Black Armies, then: Occupy 24 Territories of your choice."},
    {"id": "destroy_pink", "kind": "destroy", "target": 6, "target_name": "Pink", "text": "Destroy all Pink Armies. If yours are the Pink Armies, then: Occupy 24 Territories of your choice."},
]
MISSION_BY_ID = {mission["id"]: mission for mission in MISSION_DECK}


def create_card_deck() -> list[dict]:
    """Build one reinforcement card per territory, with 14 of each type."""
    territories = TERRITORY_ORDER[:]
    types = (CARD_TYPES * ((len(territories) + len(CARD_TYPES) - 1) // len(CARD_TYPES)))[:len(territories)]
    shuffle(territories)
    shuffle(types)
    return [
        {
            "id": uuid.uuid4().hex[:10],
            "type": typ,
            "icon": CARD_ICONS[typ],
            "territory": safe,
            "territory_name": TERRITORY_INFO[safe]["name"],
        }
        for safe, typ in zip(territories, types)
    ]


def draw_card() -> dict | None:
    """Draw from the finite territory-card deck, recycling only traded discards."""
    if not GAME["card_deck"] and GAME["card_discard"]:
        GAME["card_deck"] = GAME["card_discard"][:]
        GAME["card_discard"] = []
        shuffle(GAME["card_deck"])
        log("The reinforcement-card discard pile is reshuffled into a new draw deck.")
    if not GAME["card_deck"]:
        return None
    return GAME["card_deck"].pop()


def discard_cards(cards: list[dict]) -> None:
    GAME["card_discard"].extend(cards)

def new_empty_game() -> dict:
    return {
        "started": False,
        "phase": "pregame",
        "mode": "global",
        "winner_id": 0,
        "turn": 0,
        "current_player": 0,
        "players": {},
        "territories": {safe: {"owner": 0, "strength": 0} for safe in TERRITORY_ORDER},
        "selected": None,
        "pending_attack": None,
        "last_battle": None,
        "battle_seq": 0,
        "trade_count": 0,
        "card_deck": create_card_deck(),
        "card_discard": [],
        "stats": {},
        "log": ["Prepare the campaign table."],
    }


GAME = new_empty_game()


def log(message: str) -> None:
    GAME["log"].insert(0, f"{time.strftime('%H:%M:%S')} — {message}")
    del GAME["log"][60:]


def ensure_stats(pid: int) -> dict:
    stats = GAME.setdefault("stats", {})
    key = str(pid)
    if key not in stats:
        stats[key] = STAT_DEFAULTS.copy()
    else:
        for field, default in STAT_DEFAULTS.items():
            stats[key].setdefault(field, default)
    return stats[key]


def add_stat(pid: int | None, field: str, amount: int = 1) -> None:
    if not pid or str(pid) not in GAME.get("players", {}):
        return
    stats = ensure_stats(int(pid))
    stats[field] = stats.get(field, 0) + int(amount)


def personality_name(pid: int) -> str:
    player = GAME["players"].get(str(pid), {})
    name = player.get("ai_personality") or DEFAULT_PERSONALITY_BY_PLAYER.get(pid, "Balanced General")
    return name if name in AI_PERSONALITIES else "Balanced General"


def personality(pid: int) -> dict:
    return AI_PERSONALITIES[personality_name(pid)]


def is_ai_player(pid: int) -> bool:
    return GAME["players"].get(str(pid), {}).get("kind") == "ai"

def current_player() -> dict | None:
    pid = GAME["current_player"]
    return GAME["players"].get(str(pid))


def current_player_id() -> int:
    return int(GAME["current_player"] or 0)


def clamp_int(value, lo: int, hi: int, default: int | None = None) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = lo if default is None else int(default)
    return max(lo, min(n, hi))


def clear_selection() -> None:
    GAME["selected"] = None
    GAME["pending_attack"] = None


def json_state():
    return jsonify({"ok": True, "state": public_state()})


def json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def owner(safe: str) -> int:
    return int(GAME["territories"][safe]["owner"])


def strength(safe: str) -> int:
    return int(GAME["territories"][safe]["strength"])


def set_strength(safe: str, value: int) -> None:
    GAME["territories"][safe]["strength"] = max(0, int(value))


def set_owner(safe: str, value: int) -> None:
    GAME["territories"][safe]["owner"] = int(value)


def territory_name(safe: str) -> str:
    return TERRITORY_INFO[safe]["name"]


def neighbours(safe: str) -> list[str]:
    return TERRITORY_INFO[safe]["neighbours"]


def active_player_ids() -> list[int]:
    return [int(pid) for pid, p in GAME["players"].items() if not p.get("eliminated")]


def player_territories(pid: int) -> list[str]:
    return [safe for safe in TERRITORY_ORDER if owner(safe) == pid]


def player_total_armies(pid: int) -> int:
    return sum(strength(safe) for safe in player_territories(pid))


def continent_bonus(pid: int) -> int:
    total = 0
    for continent, terrs in CONTINENTS.items():
        if terrs and all(owner(safe) == pid for safe in terrs):
            total += CONTINENT_BONUS[continent]
    return total


def reinforcement_count(pid: int) -> int:
    return max(3, len(player_territories(pid)) // 3) + continent_bonus(pid)


def next_active_player(pid: int) -> int:
    ids = sorted(active_player_ids())
    if not ids:
        return 0
    if pid not in ids:
        return ids[0]
    i = ids.index(pid)
    return ids[(i + 1) % len(ids)]


def check_eliminations(conqueror_pid: int | None = None) -> None:
    for pid_s, defeated in GAME["players"].items():
        pid = int(pid_s)
        if defeated.get("eliminated") or len(player_territories(pid)) != 0:
            continue

        defeated["eliminated"] = True
        defeated["eliminated_by"] = int(conqueror_pid or 0)
        transferred = 0
        if conqueror_pid and conqueror_pid != pid and str(conqueror_pid) in GAME["players"]:
            conqueror = GAME["players"][str(conqueror_pid)]
            transferred = len(defeated.get("cards", []))
            if transferred:
                conqueror["cards"].extend(defeated["cards"])
                defeated["cards"] = []

        if transferred:
            log(f"{defeated['name']} has been eliminated; {transferred} cards transfer to {GAME['players'][str(conqueror_pid)]['name']}.")
        else:
            log(f"{defeated['name']} has been eliminated.")

        convert_third_party_destroy_missions(pid, conqueror_pid)


def convert_third_party_destroy_missions(target_pid: int, conqueror_pid: int | None) -> None:
    if GAME.get("mode") != "missions":
        return
    for holder_s, player in GAME["players"].items():
        holder_pid = int(holder_s)
        if player.get("eliminated") or holder_pid == conqueror_pid:
            continue
        mission = MISSION_BY_ID.get(player.get("mission_id", ""))
        if mission and mission.get("kind") == "destroy" and int(mission.get("target", 0)) == target_pid:
            player["mission_id"] = "occupy_24"
            log(f"{player['name']}'s destroy mission converts to Occupy 24 territories because another commander eliminated {GAME['players'][str(target_pid)]['name']}.")


def completed_mission(pid: int) -> bool:
    if GAME.get("mode") != "missions":
        return False
    mission_id = GAME["players"].get(str(pid), {}).get("mission_id")
    mission = MISSION_BY_ID.get(mission_id or "")
    if not mission:
        return False

    owned = player_territories(pid)
    kind = mission["kind"]

    if kind == "occupy":
        min_strength = mission.get("min_strength", 1)
        return sum(1 for safe in owned if strength(safe) >= min_strength) >= mission["count"]

    if kind == "continents":
        return all(all(owner(safe) == pid for safe in CONTINENTS[continent]) for continent in mission["continents"])

    if kind == "destroy":
        target = mission["target"]
        # Keep games with fewer than six players playable: if the target colour is
        # the mission holder or is not in this game, use the card's fallback goal.
        if target == pid or str(target) not in GAME["players"]:
            return len(owned) >= 24
        target_player = GAME["players"].get(str(target), {})
        if target_player.get("eliminated") or len(player_territories(target)) == 0:
            return int(target_player.get("eliminated_by") or 0) == pid
        return False

    return False


def mission_for(pid: int) -> dict | None:
    if GAME.get("mode") != "missions" or not pid:
        return None
    return MISSION_BY_ID.get(GAME["players"].get(str(pid), {}).get("mission_id", ""))


def mission_text(pid: int) -> str | None:
    mission = mission_for(pid)
    if not mission:
        return None
    text = mission["text"]
    target = mission.get("target")
    if mission["kind"] == "destroy" and target and (target == pid or str(target) not in GAME["players"]):
        text += " Effective objective: Occupy 24 Territories of your choice."
    return text


def visible_mission(pid: int) -> dict | None:
    mission = mission_for(pid)
    text = mission_text(pid)
    if not mission or text is None:
        return None
    return {"id": mission["id"], "text": text, "complete": completed_mission(pid)}


def check_victory(pid: int | None = None) -> None:
    if not GAME["started"] or GAME.get("winner_id"):
        return

    if GAME.get("mode") == "missions" and GAME.get("phase") not in {"pregame", "initial_deploy"}:
        candidates = [pid] if pid else active_player_ids()
        for candidate in candidates:
            if candidate and completed_mission(candidate):
                GAME["winner_id"] = candidate
                log(f"{GAME['players'][str(candidate)]['name']} completes a secret mission and wins the campaign.")
                return

    living = [int(pid_s) for pid_s, p in GAME["players"].items() if not p.get("eliminated")]
    if GAME.get("mode") == "global" and len(living) == 1:
        GAME["winner_id"] = living[0]


def winner() -> dict | None:
    check_victory()
    winner_id = int(GAME.get("winner_id") or 0)
    return GAME["players"].get(str(winner_id)) if winner_id else None


def make_card() -> dict | None:
    return draw_card()


def trade_bonus_territories(pid: int, cards: list[dict]) -> list[str]:
    """Return all traded-card territories currently occupied by the player.

    Classic Risk grants two immediate armies on each matching territory card
    in the traded set.
    """
    matches: list[str] = []
    seen: set[str] = set()
    for card in cards:
        safe = card["territory"]
        if safe not in seen and owner(safe) == pid:
            matches.append(safe)
            seen.add(safe)
    return matches


def apply_trade_bonus(pid: int, cards: list[dict]) -> list[str]:
    matches = trade_bonus_territories(pid, cards)
    for safe in matches:
        set_strength(safe, strength(safe) + 2)
    if matches:
        add_stat(pid, "trade_bonus_armies", 2 * len(matches))
    return matches


def is_valid_trade(cards: list[dict]) -> bool:
    if len(cards) != 3:
        return False
    types = [c["type"] for c in cards]
    return len(set(types)) == 1 or set(types) == set(CARD_TYPES)


def trade_value() -> int:
    n = GAME["trade_count"]
    if n < len(TRADE_VALUES):
        return TRADE_VALUES[n]
    return TRADE_VALUES[-1] + 5 * (n - len(TRADE_VALUES) + 1)


def begin_turn(pid: int) -> None:
    GAME["phase"] = "reinforce"
    GAME["current_player"] = pid
    GAME["selected"] = None
    GAME["pending_attack"] = None
    GAME["last_battle"] = None
    p = GAME["players"][str(pid)]
    gained = reinforcement_count(pid)
    p["reserve"] += gained
    add_stat(pid, "reinforcements_received", gained)
    p["conquered_this_turn"] = False
    log(f"{p['name']} begins Reinforce and receives {gained} armies.")


def finish_turn_after_move() -> None:
    pid = current_player_id()
    p = GAME["players"][str(pid)]
    if p.get("conquered_this_turn"):
        card = draw_card()
        if card:
            p["cards"].append(card)
            add_stat(pid, "cards_drawn")
            log(f"{p['name']} draws a {card['type']} card for conquering territory.")
        else:
            log(f"{p['name']} earned a card, but the reinforcement deck is empty.")

    next_pid = next_active_player(pid)
    if next_pid <= pid:
        GAME["turn"] += 1
    begin_turn(next_pid)


def enter_attack_phase(player: dict) -> None:
    GAME["phase"] = "attack"
    clear_selection()
    GAME["last_battle"] = None
    log(f"{player['name']} advances to Attack.")


def enter_move_phase(player: dict) -> None:
    GAME["phase"] = "move"
    clear_selection()
    log(f"{player['name']} advances to Move.")


def advance_initial_deploy_turn() -> None:
    """Rotate initial setup one army at a time.

    After a player places one army, the next player with setup reserves gets 
    exactly one placement opportunity. When all setup reserves are empty, 
    normal play begins with player 1's first Reinforce phase.
    """
    if GAME["phase"] != "initial_deploy":
        return

    waiting = sorted(
        int(pid)
        for pid, p in GAME["players"].items()
        if p["reserve"] > 0 and not p.get("eliminated")
    )
    if not waiting:
        GAME["turn"] = 1
        log("Initial deployment is complete. Normal play begins.")
        begin_turn(1)
        return

    previous = current_player_id()
    for candidate in waiting:
        if candidate > previous:
            GAME["current_player"] = candidate
            break
    else:
        GAME["current_player"] = waiting[0]

    next_name = GAME["players"][str(GAME["current_player"])]["name"]
    log(f"Initial deployment passes to {next_name}.")



def must_trade_cards(pid: int) -> bool:
    p = GAME["players"][str(pid)]
    cards = p["cards"]
    if len(cards) < 5:
        return False
    # With three card types and no wild cards, five cards always contain either 3 same or 1 each.
    return True


def valid_attackers(pid: int) -> list[str]:
    result = []
    for safe in player_territories(pid):
        if strength(safe) > 1 and any(owner(n) not in (0, pid) for n in neighbours(safe)):
            result.append(safe)
    return result


def valid_attack_targets(from_safe: str, pid: int) -> list[str]:
    if not from_safe or owner(from_safe) != pid or strength(from_safe) <= 1:
        return []
    return [n for n in neighbours(from_safe) if owner(n) not in (0, pid)]


def valid_movers(pid: int) -> list[str]:
    result = []
    for safe in player_territories(pid):
        if strength(safe) > 1 and any(owner(n) == pid for n in neighbours(safe)):
            result.append(safe)
    return result


def valid_move_targets(from_safe: str, pid: int) -> list[str]:
    """Legal move-phase destinations: adjacent territories owned by the same player. """

    if not from_safe or owner(from_safe) != pid or strength(from_safe) <= 1:
        return []
    return [n for n in neighbours(from_safe) if owner(n) == pid]


def valid_clicks() -> dict:
    pid = current_player_id()
    phase = GAME["phase"]
    selected = GAME.get("selected")
    clicks = {"primary": [], "secondary": [], "selected": selected, "attackers": [], "targets": []}

    if not pid or phase == "pregame":
        return clicks
    p = GAME["players"][str(pid)]

    if phase in {"initial_deploy", "reinforce"}:
        if p["reserve"] > 0:
            clicks["primary"] = player_territories(pid)
    elif phase == "attack":
        attackers = valid_attackers(pid)
        clicks["attackers"] = attackers
        clicks["primary"] = attackers
        if selected:
            targets = valid_attack_targets(selected, pid)
            clicks["targets"] = targets
            clicks["secondary"] = targets
    elif phase == "move":
        movers = valid_movers(pid)
        clicks["primary"] = movers
        if selected:
            clicks["secondary"] = valid_move_targets(selected, pid)
    return clicks


def player_cards_for_client(pid: int) -> list[dict]:
    if GAME.get("winner_id"):
        return GAME["players"].get(str(pid), {}).get("cards", [])
    if pid == current_player_id() and not is_ai_player(pid):
        return GAME["players"].get(str(pid), {}).get("cards", [])
    return []


def effective_mission_text(pid: int) -> str | None:
    return mission_text(pid)


def public_winner() -> dict | None:
    wid = int(GAME.get("winner_id") or 0)
    if not wid or str(wid) not in GAME["players"]:
        return None
    p = GAME["players"][str(wid)]
    return {"id": wid, "name": p["name"], "colour": PLAYER_COLOURS[wid]}


def card_summary(cards: list[dict]) -> dict:
    by_type = {typ: 0 for typ in CARD_TYPES}
    for card in cards:
        by_type[card["type"]] = by_type.get(card["type"], 0) + 1
    return {
        "count": len(cards),
        "by_type": by_type,
        "cards": cards,
    }


def victory_summary() -> dict | None:
    winner_data = public_winner()
    if not winner_data:
        return None
    commanders = []
    for pid_s in sorted(GAME["players"], key=lambda x: int(x)):
        pid = int(pid_s)
        p = GAME["players"][pid_s]
        commanders.append({
            "id": pid,
            "name": p["name"],
            "kind": p.get("kind", "human"),
            "ai_personality": p.get("ai_personality"),
            "colour": PLAYER_COLOURS[pid],
            "eliminated": p.get("eliminated", False),
            "eliminated_by": p.get("eliminated_by", 0),
            "territory_count": len(player_territories(pid)),
            "army_count": player_total_armies(pid),
            "reserve": p.get("reserve", 0),
            "continent_bonus": continent_bonus(pid),
            "mission": effective_mission_text(pid),
            "mission_complete": completed_mission(pid),
            "stats": ensure_stats(pid),
            "cards": card_summary(p.get("cards", [])),
        })
    return {
        "mode": GAME.get("mode", "global"),
        "turn": GAME.get("turn", 0),
        "winner": winner_data,
        "commanders": commanders,
    }


def public_state() -> dict:
    players = []
    for pid_s in sorted(GAME["players"], key=lambda x: int(x)):
        p = GAME["players"][pid_s]
        pid = int(pid_s)
        terrs = player_territories(pid)
        players.append({
            "id": pid,
            "name": p["name"],
            "kind": p.get("kind", "human"),
            "ai_personality": p.get("ai_personality"),
            "colour": PLAYER_COLOURS[pid],
            "reserve": p["reserve"],
            "cards": player_cards_for_client(pid),
            "card_count": len(p["cards"]),
            "card_faces_hidden": bool(len(p["cards"]) and not player_cards_for_client(pid)),
            "territory_count": len(terrs),
            "army_count": player_total_armies(pid),
            "continent_bonus": continent_bonus(pid),
            "eliminated": p.get("eliminated", False),
            "conquered_this_turn": p.get("conquered_this_turn", False),
        })

    return {
        "started": GAME["started"],
        "mode": GAME.get("mode", "global"),
        "phase": GAME["phase"],
        "turn": GAME["turn"],
        "current_player": current_player_id(),
        "current": next((p for p in players if p["id"] == current_player_id()), None),
        "players": players,
        "territories": {
            safe: {
                "owner": owner(safe),
                "strength": strength(safe),
                "name": territory_name(safe),
                "neighbours": neighbours(safe),
            }
            for safe in TERRITORY_ORDER
        },
        "valid_clicks": valid_clicks(),
        "pending_attack": GAME.get("pending_attack"),
        "last_battle": GAME.get("last_battle"),
        "selected": GAME.get("selected"),
        "current_mission": None if is_ai_player(current_player_id()) else visible_mission(current_player_id()),
        "trade_count": GAME["trade_count"],
        "next_trade_value": trade_value(),
        "must_trade": bool(current_player_id() and must_trade_cards(current_player_id()) and GAME["phase"] == "reinforce"),
        "winner": public_winner(),
        "victory_summary": victory_summary(),
        "ai_personalities": list(AI_PERSONALITIES.keys()),
        "default_ai_personalities": DEFAULT_PERSONALITY_BY_PLAYER,
        "log": GAME["log"],
    }


def map_data_from_state() -> list[tuple]:
    return [
        (safe, formatted_name, x, y, ax, ay, owner(safe), strength(safe), ns)
        for safe, formatted_name, x, y, ax, ay, _owner, _strength, ns in BLANK_MAP_DATA
    ]


STATIC_DIR = Path(__file__).resolve().parent / "static"
MAP_HEAD = (STATIC_DIR / "svg_map_head.xml").read_text(encoding="utf-8")
MAP_TAIL = (STATIC_DIR / "svg_map_tail.xml").read_text(encoding="utf-8")


def split_svg_tail(svg_tail: str) -> tuple[str, str]:
    """Split the static tail before the final board group close.

    Runtime overlays that must be visually top-most still need to remain inside
    the transformed board group. The static tail contains continent labels and
    then closes that group, so insert top overlays immediately before the close.
    """
    marker = "\n</g>\n</svg>"
    if marker not in svg_tail:
        raise RuntimeError("svg_map_tail.xml no longer has the expected final group close")
    before, _after = svg_tail.rsplit(marker, 1)
    return before + "\n", marker.lstrip("\n")


MAP_TAIL_BEFORE_TOP_OVERLAYS, MAP_TAIL_CLOSE = split_svg_tail(MAP_TAIL)


def extract_map_paths(map_head: str) -> list[str]:
    """Return source path elements from the SVG map definition.

    The board SVG keeps territory paths inside <defs><g id="map"> and renders
    them through <use>. Portable click handling needs real geometry, so a static
    transparent hit layer is generated from those same paths.
    """
    match = re.search(r'''<g\s+id\s*=\s*["']map["'][^>]*>(.*?)</g>''', map_head, flags=re.S)
    return re.findall(r'<path\b[^>]*>', match.group(1), flags=re.S) if match else []


def make_hit_layer(map_head: str, safe_names: set[str]) -> str:
    paths = []
    for raw in extract_map_paths(map_head):
        id_match = re.search(r'\bid="([^"]+)"', raw)
        if not id_match or id_match.group(1) not in safe_names:
            continue
        safe = id_match.group(1)
        # Remove source styling/id and preserve geometry/transform. The data-safe
        # attribute is the event contract used by the client.
        path = re.sub(r'\s(?:fill|stroke)="[^"]*"', '', raw)
        path = re.sub(r'\sid="[^"]*"', '', path)
        path = path.replace('<path', f'<path id="hit_{safe}" class="territory-hit" data-safe="{safe}"', 1)
        paths.append("    " + path)
    if not paths:
        return ""
    return (
        '  <g id="territory_hit_layer" aria-label="Interactive territory hit layer">\n'
        + "\n".join(paths)
        + '\n  </g>\n'
    )


TERRITORY_SAFE_NAMES = set(TERRITORY_ORDER)
TERRITORY_HIT_LAYER = make_hit_layer(MAP_HEAD, TERRITORY_SAFE_NAMES)


def owner_fill_styles(map_data: list[tuple], owner_fills: bool) -> str:
    if not owner_fills:
        return ""
    rules = (
        f"  #map > path#{safe_name} {{ fill: {PLAYER_COLOURS.get(terr_owner, PLAYER_COLOURS[0])['path']}; }}"
        for safe_name, _formatted_name, _x, _y, _ax, _ay, terr_owner, _strength, _neighbours in map_data
    )
    return "\n".join([' <style id="risk_owner_fill_styles">', *rules, " </style>"])


def svg_head_for(map_data: list[tuple], owner_fills: bool) -> str:
    return MAP_HEAD.replace("<!-- RISK_OWNER_FILL_STYLES -->", owner_fill_styles(map_data, owner_fills))


ATTACK_OVERLAY = (
    '  <g id="attack_overlay" pointer-events="none" aria-hidden="true">\n'
    '    <use id="attack_arrow_use" xlink:href="#attack_arrow_shape" href="#attack_arrow_shape" visibility="hidden" opacity="0.58"/>\n'
    '  </g>\n\n'
)

REINFORCEMENT_OVERLAY = (
    '  <g id="reinforcement_overlay" pointer-events="none" aria-hidden="true">\n'
    '    <use id="reinforcement_arrow_use" xlink:href="#reinforcement_arrow_shape" href="#reinforcement_arrow_shape" visibility="hidden" opacity="0.36"/>\n'
    '  </g>\n\n'
)


REGION_LABEL_ATTRS = (
    'font-family="Helvetica,Arial,sans-serif" font-size="12" font-style="normal" '
    'font-weight="700" letter-spacing="0.5" text-anchor="middle" fill="#000" stroke="none"'
)
ARMY_LABEL_ATTRS = 'font-family="Helvetica,Arial,sans-serif" font-size="12" font-weight="700" text-anchor="middle" stroke="none"'


def label_tspans(name: str) -> str:
    return escape(name).replace("\n", "</tspan><tspan x=\"0\" dy=\"1em\">")


def army_scale(count: int) -> float:
    if count <= 9:
        return 1.0
    if count < 40:
        return 0.9 + count / 50
    return 1.8


def region_label_svg(safe_name: str, formatted_name: str, x: int, y: int) -> str:
    return (
        f'    <text id="label_{safe_name}" transform="translate({x},{y})">'
        f'<tspan>{label_tspans(formatted_name)}</tspan></text>'
    )


def army_marker_svg(safe_name: str, x: int, y: int, ax: int, ay: int, owner_id: int, count: int) -> str:
    army = PLAYER_COLOURS.get(owner_id, PLAYER_COLOURS[0])
    army_x = x + ax
    army_y = y - 16 + ay
    count_x = army_x - 0.5
    count_y = y - 18 + ay
    stroke = "black" if count >= 3 else "none"
    return (
        f'    <g id="ag_{safe_name}" transform-origin="{army_x} {army_y}" transform="scale({army_scale(count):.2f})">'
        f'<use id="army_{safe_name}" xlink:href="#army" href="#army" x="{army_x}" y="{army_y}" '
        f'fill="{army["army"]}" stroke="{stroke}"/>'
        f'<text id="army_{safe_name}_count" {ARMY_LABEL_ATTRS} letter-spacing="-1" fill="{army["ink"]}" '
        f'x="{count_x}" y="{count_y}">{count}</text></g>'
    )


def generate_svg(map_data: list[tuple], owner_fills: bool = True) -> str:
    labels = [f'  <g id="region_labels" {REGION_LABEL_ATTRS}>']
    armies = ['  <g id="armies_deployed">']

    for safe_name, formatted_name, x, y, ax, ay, terr_owner, terr_strength, _neighbours in map_data:
        labels.append(region_label_svg(safe_name, formatted_name, x, y))
        if terr_owner:
            armies.append(army_marker_svg(safe_name, x, y, ax, ay, terr_owner, terr_strength))

    labels.append('  </g>\n')
    armies.append('  </g>\n')
    return "".join((
        svg_head_for(map_data, owner_fills),
        MAP_TAIL_BEFORE_TOP_OVERLAYS,
        TERRITORY_HIT_LAYER,
        ATTACK_OVERLAY,
        REINFORCEMENT_OVERLAY,
        "\n".join(labels), "\n",
        "\n".join(armies), "\n",
        MAP_TAIL_CLOSE,
    ))

@app.get("/")
def index():
    return render_template(
        "index.html",
        ai_personalities=list(AI_PERSONALITIES.keys()),
        default_ai_personalities=DEFAULT_PERSONALITY_BY_PLAYER,
    )


@app.get("/api/state")
def api_state():
    return jsonify(public_state())


@app.get("/api/svg")
def api_svg():
    owner_fills = request.args.get("owner_fills", "1").lower() not in {"0", "false", "no", "off"}
    return Response(generate_svg(map_data_from_state(), owner_fills=owner_fills), mimetype="image/svg+xml")


def valid_trade_sets(cards: list[dict]) -> list[tuple[dict, dict, dict]]:
    return [combo for combo in combinations(cards, 3) if is_valid_trade(list(combo))]


def choose_trade_set(pid: int) -> list[dict] | None:
    cards = GAME["players"][str(pid)]["cards"]
    sets = valid_trade_sets(cards)
    if not sets:
        return None

    def score(combo: tuple[dict, dict, dict]) -> float:
        owned_bonus = sum(1 for card in combo if owner(card["territory"]) == pid)
        type_spread = len({card["type"] for card in combo})
        return owned_bonus * 3 + type_spread + random() * 0.1

    return list(max(sets, key=score))


def apply_card_trade(pid: int, cards: list[dict]) -> str:
    p = GAME["players"][str(pid)]
    ids = {card["id"] for card in cards}
    value = trade_value()
    p["cards"] = [card for card in p["cards"] if card["id"] not in ids]
    discard_cards(cards)
    p["reserve"] += value
    add_stat(pid, "trade_armies", value)
    add_stat(pid, "cards_traded", len(cards))
    GAME["trade_count"] += 1

    bonus_safes = apply_trade_bonus(pid, cards)
    if bonus_safes:
        names = ", ".join(territory_name(safe) for safe in bonus_safes)
        plural = "territories" if len(bonus_safes) > 1 else "territory"
        message = f"{p['name']} trades cards for {value} armies and gains the matching-territory +2 on {plural}: {names}."
    else:
        message = f"{p['name']} trades cards for {value} reserve armies."
    log(message)
    return message


def enemy_neighbours(safe: str, pid: int) -> list[str]:
    return [n for n in neighbours(safe) if owner(n) not in (0, pid)]


def friendly_neighbours(safe: str, pid: int) -> list[str]:
    return [n for n in neighbours(safe) if owner(n) == pid]


def enemy_pressure(safe: str, pid: int) -> int:
    return sum(strength(n) for n in enemy_neighbours(safe, pid))


def friendly_support(safe: str, pid: int) -> int:
    return sum(strength(n) for n in friendly_neighbours(safe, pid))


def border_count(safe: str, pid: int) -> int:
    return len(enemy_neighbours(safe, pid))


def continent_ratio(pid: int, continent: str) -> float:
    terrs = CONTINENTS[continent]
    return sum(1 for safe in terrs if owner(safe) == pid) / len(terrs)


def territory_continent_value(pid: int, safe: str) -> float:
    continent = TERRITORY_CONTINENT.get(safe)
    if not continent:
        return 0.0
    ratio = continent_ratio(pid, continent)
    return ratio * ratio * CONTINENT_BONUS[continent]


def strategic_weight(name: str, default: float = 1.0) -> float:
    return float(STRATEGIC_WEIGHTS.get(name, default))


def continent_owner_counts(continent: str) -> dict[int, int]:
    counts: dict[int, int] = {}
    for safe in CONTINENTS[continent]:
        pid = owner(safe)
        if pid:
            counts[pid] = counts.get(pid, 0) + 1
    return counts


def strongest_enemy_continent_ratio(pid: int, continent: str) -> float:
    terrs = CONTINENTS[continent]
    if not terrs:
        return 0.0
    counts = continent_owner_counts(continent)
    return max((count / len(terrs) for enemy, count in counts.items() if enemy != pid), default=0.0)


def opponent_continent_pressure(pid: int, safe: str) -> float:
    """How urgent it is to contest this territory because another player is building a continent."""
    continent = TERRITORY_CONTINENT.get(safe)
    if not continent:
        return 0.0
    enemy_ratio = strongest_enemy_continent_ratio(pid, continent)
    if enemy_ratio < 0.34:
        return 0.0
    bonus = CONTINENT_BONUS[continent]
    local_enemy_armies = sum(strength(n) for n in enemy_neighbours(safe, pid))
    return strategic_weight("enemy_continent_alert") * (enemy_ratio ** 2) * bonus + 0.08 * local_enemy_armies


def enemy_continent_progress_value(target_pid: int, safe: str) -> float:
    if not target_pid:
        return 0.0
    continent = TERRITORY_CONTINENT.get(safe)
    if not continent:
        return 0.0
    terrs = CONTINENTS[continent]
    ratio = sum(1 for terr in terrs if owner(terr) == target_pid) / len(terrs)
    if ratio < 0.45:
        return 0.0
    return ratio * ratio * CONTINENT_BONUS[continent]


def future_attack_options(safe: str, pid: int) -> float:
    """Value of occupying or reinforcing a front with useful outward attacks."""
    value = 0.0
    local_strength = max(1, strength(safe))
    for n in enemy_neighbours(safe, pid):
        defender = max(1, strength(n))
        value += max(0.0, (local_strength - 1) / defender - 0.9)
        value += 0.25 * CHOKE_VALUES.get(n, 0.0)
    return value


def frontier_value(pid: int, safe: str) -> float:
    return (
        1.15 * border_count(safe, pid)
        + 0.13 * enemy_pressure(safe, pid)
        + 1.9 * CHOKE_VALUES.get(safe, 0.0)
        + 0.28 * territory_continent_value(pid, safe)
        + 0.55 * mission_deploy_value(pid, safe)
        + 0.65 * opponent_continent_pressure(pid, safe)
        + 0.45 * future_attack_options(safe, pid)
    )


def garrison_need(pid: int, safe: str) -> float:
    """Soft target garrison; above this, extra armies are candidates for redeployment."""
    borders = border_count(safe, pid)
    if borders == 0:
        # Interior territories should not keep large stacks unless they are
        # unusually important mission/choke locations.
        return 1.0 + 0.35 * CHOKE_VALUES.get(safe, 0.0) + 0.12 * mission_deploy_value(pid, safe)
    return (
        1.0
        + 0.55 * borders
        + 0.24 * enemy_pressure(safe, pid)
        + 0.95 * CHOKE_VALUES.get(safe, 0.0)
        + 0.18 * territory_continent_value(pid, safe)
        + 0.22 * mission_deploy_value(pid, safe)
        + 0.24 * opponent_continent_pressure(pid, safe)
    )


def overstack_penalty(pid: int, safe: str, setup: bool = False) -> float:
    excess = max(0.0, strength(safe) - garrison_need(pid, safe))
    if border_count(safe, pid) == 0:
        excess += max(0.0, strength(safe) - 2.0) * strategic_weight("safe_stack_drain")
    key = "setup_overstack_penalty" if setup else "reinforce_overstack_penalty"
    return strategic_weight(key) * excess


def mission_continents(pid: int) -> list[str]:
    mission = MISSION_BY_ID.get(GAME["players"].get(str(pid), {}).get("mission_id", ""))
    if GAME.get("mode") != "missions" or not mission:
        return []
    if mission["kind"] == "continents":
        return list(mission["continents"])
    return []


def destroy_target(pid: int) -> int | None:
    mission = MISSION_BY_ID.get(GAME["players"].get(str(pid), {}).get("mission_id", ""))
    if GAME.get("mode") != "missions" or not mission or mission["kind"] != "destroy":
        return None
    target = int(mission["target"])
    if target == pid or str(target) not in GAME["players"]:
        return None
    return target


def mission_deploy_value(pid: int, safe: str) -> float:
    if GAME.get("mode") != "missions":
        return 0.0
    mission = MISSION_BY_ID.get(GAME["players"].get(str(pid), {}).get("mission_id", ""))
    if not mission:
        return 0.0
    kind = mission["kind"]
    if kind == "occupy":
        if mission.get("min_strength", 1) >= 2 and strength(safe) < 2:
            return 5.0
        return 0.75 if border_count(safe, pid) else 0.25
    if kind == "continents":
        continent = TERRITORY_CONTINENT.get(safe)
        if continent in mission["continents"]:
            return 3.0 + 2.0 * continent_ratio(pid, continent)
        if any(n in sum((CONTINENTS[c] for c in mission["continents"]), []) for n in neighbours(safe)):
            return 0.8
    if kind == "destroy":
        target = destroy_target(pid)
        if target is None:
            return 0.75 if len(player_territories(pid)) < 24 else 0.0
        return 3.0 if any(owner(n) == target for n in neighbours(safe)) else 0.0
    return 0.0


def mission_attack_value(pid: int, dst: str) -> float:
    if GAME.get("mode") != "missions":
        return 0.0
    mission = MISSION_BY_ID.get(GAME["players"].get(str(pid), {}).get("mission_id", ""))
    if not mission:
        return 0.0
    kind = mission["kind"]
    if kind == "occupy":
        value = 2.0
        if mission.get("min_strength", 1) >= 2:
            value += 1.0
        return value
    if kind == "continents":
        continent = TERRITORY_CONTINENT.get(dst)
        if continent in mission["continents"]:
            return 5.0 + 3.0 * continent_ratio(pid, continent)
        return 0.0
    if kind == "destroy":
        target = destroy_target(pid)
        if target is None:
            return 2.0
        return 7.5 if owner(dst) == target else 0.0
    return 0.0


def would_break_enemy_continent(target_pid: int, dst: str) -> float:
    if not target_pid:
        return 0.0
    continent = TERRITORY_CONTINENT.get(dst)
    if not continent:
        return 0.0
    if all(owner(safe) == target_pid for safe in CONTINENTS[continent]):
        return CONTINENT_BONUS[continent]
    return 0.0


def choose_scored(scored: list[tuple[float, object]], top_n: int = 3):
    if not scored:
        return None
    scored = sorted(scored, key=lambda item: item[0], reverse=True)
    top = scored[:max(1, min(top_n, len(scored)))]
    # Favour the top score but keep a little variation between games.
    return max(top, key=lambda item: item[0] + random() * 0.25)[1]


def deploy_score(pid: int, safe: str, setup: bool = False) -> float:
    w = personality(pid)
    pressure = enemy_pressure(safe, pid)
    opportunity = sum(max(0, strength(safe) - strength(n) + 1) for n in enemy_neighbours(safe, pid))
    if setup:
        opportunity = min(opportunity, 4) * 0.45
    under_defended = max(0.0, garrison_need(pid, safe) - strength(safe))
    reactive = opponent_continent_pressure(pid, safe) + 0.22 * enemy_pressure(safe, pid)
    return (
        1.0
        + w["defense_bias"] * (1.3 * border_count(safe, pid) + 0.28 * pressure + 1.15 * under_defended)
        + w["attack_bias"] * (0.26 if setup else 0.38) * opportunity
        + w["continent_bias"] * territory_continent_value(pid, safe)
        + w["mission_focus"] * mission_deploy_value(pid, safe)
        + w["choke_bias"] * 1.9 * CHOKE_VALUES.get(safe, 0.0)
        + strategic_weight("reactivity") * reactive
        - overstack_penalty(pid, safe, setup=setup)
        + random() * 0.08
    )


def choose_deploy_territory(pid: int, setup: bool = False) -> str | None:
    owned = player_territories(pid)
    if not owned:
        return None
    return choose_scored([(deploy_score(pid, safe, setup=setup), safe) for safe in owned])


def deploy_one_ai_army(pid: int, setup: bool = False) -> str:
    p = GAME["players"][str(pid)]
    safe = choose_deploy_territory(pid, setup=setup)
    if not safe or p["reserve"] <= 0:
        return "No deployment available."
    set_strength(safe, strength(safe) + 1)
    p["reserve"] -= 1
    log(f"{p['name']} deploys 1 army to {territory_name(safe)}.")
    if setup:
        advance_initial_deploy_turn()
    check_victory(pid)
    return f"deployed to {territory_name(safe)}"


def deploy_all_ai_reserves(pid: int) -> str:
    p = GAME["players"][str(pid)]
    placed = []
    while p["reserve"] > 0:
        safe = choose_deploy_territory(pid, setup=False)
        if not safe:
            break
        set_strength(safe, strength(safe) + 1)
        p["reserve"] -= 1
        placed.append(safe)
    if placed:
        summary = ", ".join(territory_name(safe) for safe in placed[:5])
        extra = "…" if len(placed) > 5 else ""
        log(f"{p['name']} deploys {len(placed)} reserve armies ({summary}{extra}).")
    return f"deployed {len(placed)} reserve armies"


def attack_candidate_score(pid: int, src: str, dst: str) -> float:
    w = personality(pid)
    attack_armies = max(0, strength(src) - 1)
    defence = max(1, strength(dst))
    odds = attack_armies / defence
    target_pid = owner(dst)
    target_territories = len(player_territories(target_pid)) if target_pid else 0
    elimination = 9.0 if target_pid and target_territories == 1 else (3.0 if target_pid and target_territories <= 3 else 0.0)
    card_value = 3.0 if not GAME["players"][str(pid)].get("conquered_this_turn") and defence <= max(1, attack_armies) else 0.0
    source_exposure = max(0, enemy_pressure(src, pid) - (strength(src) - 1))
    enemy_strategy = enemy_continent_progress_value(target_pid, dst)
    return (
        w["attack_bias"] * 3.4 * odds
        + w["mission_focus"] * mission_attack_value(pid, dst)
        + w["continent_bias"] * (territory_continent_value(pid, dst) + would_break_enemy_continent(target_pid, dst) + 0.7 * enemy_strategy)
        + w["card_hunter"] * card_value
        + w["opportunism"] * (elimination + max(0, 2.0 - defence) + 0.55 * len(GAME["players"].get(str(target_pid), {}).get("cards", [])))
        + w["choke_bias"] * CHOKE_VALUES.get(dst, 0.0)
        + strategic_weight("reactivity") * 0.45 * enemy_strategy
        - w["defense_bias"] * 0.35 * source_exposure
        + random() * 0.12
    )


def choose_attack(pid: int) -> tuple[str, str] | None:
    w = personality(pid)
    candidates = []
    for src in valid_attackers(pid):
        for dst in valid_attack_targets(src, pid):
            attack_armies = strength(src) - 1
            defence = max(1, strength(dst))
            odds = attack_armies / defence
            score = attack_candidate_score(pid, src, dst)
            threshold = 3.15 - 1.45 * w["risk"]
            mission_bonus = mission_attack_value(pid, dst)
            if odds >= (1.10 + 1.15 * (1.0 - w["risk"])) or score >= threshold + mission_bonus * 0.35:
                candidates.append((score, (src, dst)))
    if not candidates:
        return None
    # Cautious players often stop after earning their one card.
    if GAME["players"][str(pid)].get("conquered_this_turn") and w["risk"] < 0.38 and random() > w["risk"]:
        return None
    return choose_scored(candidates)


def ai_attack_dice(pid: int, src: str, dst: str) -> int:
    max_attack = min(3, strength(src) - 1)
    if max_attack <= 1:
        return 1
    w = personality(pid)
    odds = (strength(src) - 1) / max(1, strength(dst))
    if w["risk"] < 0.32 and odds < 2.5:
        return min(max_attack, 2)
    return max_attack


def ai_advance_armies(pid: int, src: str, dst: str, attack_dice: int) -> int:
    max_advance = max(1, strength(src) - 1)
    min_advance = min(attack_dice, max_advance)
    w = personality(pid)
    target_pressure = enemy_pressure(dst, pid)
    source_pressure = enemy_pressure(src, pid)
    forward_pull = frontier_value(pid, dst) - frontier_value(pid, src)
    if source_pressure == 0 and target_pressure > 0:
        return max_advance
    if w["advance_bias"] >= 0.75 or mission_attack_value(pid, dst) >= 5 or forward_pull > 2.0:
        return max_advance
    if w["advance_bias"] <= 0.35 and source_pressure > target_pressure + 2:
        return min_advance
    desired = round(min_advance + (max_advance - min_advance) * w["advance_bias"])
    if target_pressure > source_pressure or forward_pull > 0.8:
        desired += 1
    return max(min_advance, min(max_advance, desired))


def roll_dice(count: int) -> list[int]:
    return sorted((randint(1, 6) for _ in range(count)), reverse=True)


def compare_rolls(attacker_rolls: list[int], defender_rolls: list[int]) -> tuple[int, int, list[dict]]:
    attacker_losses = defender_losses = 0
    comparisons = []
    for a, d in zip(attacker_rolls, defender_rolls):
        attacker_wins = a > d
        defender_losses += int(attacker_wins)
        attacker_losses += int(not attacker_wins)
        comparisons.append({"a": a, "d": d, "winner": "attacker" if attacker_wins else "defender"})
    return attacker_losses, defender_losses, comparisons


def update_pending_attack_limits(src: str, dst: str) -> None:
    if GAME.get("pending_attack"):
        GAME["pending_attack"].update({
            "max_attack_dice": min(3, strength(src) - 1),
            "max_defence_dice": min(2, strength(dst)),
        })


def resolve_pending_attack(attack_dice=None, defence_dice=None, advance_armies=None) -> tuple[bool, str]:
    if GAME["phase"] != "attack" or not GAME.get("pending_attack"):
        return False, "No attack is pending."

    pid = current_player_id()
    p = GAME["players"][str(pid)]
    attack = GAME["pending_attack"]
    src, dst = attack["from"], attack["to"]

    if owner(src) != pid or owner(dst) in (0, pid) or dst not in neighbours(src) or strength(src) <= 1:
        GAME["pending_attack"] = None
        return False, "Attack is no longer valid."

    attack_dice = clamp_int(attack_dice, 1, min(3, strength(src) - 1), attack.get("max_attack_dice", 1))
    defence_dice = clamp_int(defence_dice, 1, min(2, strength(dst)), attack.get("max_defence_dice", 1))
    attacker_rolls = roll_dice(attack_dice)
    defender_rolls = roll_dice(defence_dice)
    attacker_losses, defender_losses, comparisons = compare_rolls(attacker_rolls, defender_rolls)

    defending_pid = owner(dst)
    add_stat(pid, "attacks")
    add_stat(pid, "armies_lost", attacker_losses)
    add_stat(defending_pid, "armies_lost", defender_losses)

    set_strength(src, strength(src) - attacker_losses)
    set_strength(dst, strength(dst) - defender_losses)
    conquered = False
    old_owner = owner(dst)
    advance = 0

    if strength(dst) <= 0:
        conquered = True
        advance_max = max(1, strength(src) - 1)
        advance_min = min(attack_dice, advance_max)
        advance = clamp_int(advance_armies, advance_min, advance_max, advance_max)
        set_owner(dst, pid)
        set_strength(dst, advance)
        set_strength(src, strength(src) - advance)
        p["conquered_this_turn"] = True
        GAME["pending_attack"] = None
        GAME["selected"] = src if strength(src) > 1 else None
        add_stat(pid, "territories_conquered")
        add_stat(old_owner, "territories_lost")
        log(f"{p['name']} conquers {territory_name(dst)} and advances {advance} armies.")
        if old_owner:
            check_eliminations(conqueror_pid=pid)
        check_victory(pid)
    elif strength(src) <= 1:
        GAME["pending_attack"] = None
        GAME["selected"] = None
        log(f"{p['name']}'s attack stalls at {territory_name(src)}.")
    else:
        update_pending_attack_limits(src, dst)

    GAME["battle_seq"] = GAME.get("battle_seq", 0) + 1
    GAME["last_battle"] = {
        "battle_id": GAME["battle_seq"],
        "from": src,
        "to": dst,
        "from_name": territory_name(src),
        "to_name": territory_name(dst),
        "attacker_rolls": attacker_rolls,
        "defender_rolls": defender_rolls,
        "attacker_losses": attacker_losses,
        "defender_losses": defender_losses,
        "comparisons": comparisons,
        "conquered": conquered,
        "advance": advance,
        "old_owner": old_owner,
    }
    if not conquered:
        log(f"Battle: {territory_name(src)} rolls {attacker_rolls}; {territory_name(dst)} rolls {defender_rolls}. Losses {attacker_losses}/{defender_losses}.")
    return True, "attack resolved"

def choose_move(pid: int) -> tuple[str, str, int] | None:
    w = personality(pid)
    candidates = []
    for src in valid_movers(pid):
        movable_total = strength(src) - 1
        if movable_total <= 0:
            continue
        source_need = garrison_need(pid, src)
        source_excess = max(0.0, strength(src) - source_need)
        if border_count(src, pid) == 0:
            source_excess += max(0.0, strength(src) - 2.0) * strategic_weight("safe_stack_drain")
        if source_excess <= 0.35:
            continue
        source_frontier = frontier_value(pid, src)
        for dst in valid_move_targets(src, pid):
            target_need = garrison_need(pid, dst)
            target_gap = max(0.0, target_need - strength(dst))
            target_frontier = frontier_value(pid, dst)
            pull = target_frontier - 0.55 * source_frontier + 1.25 * target_gap
            score = (
                strategic_weight("friendly_path_fortify") * pull
                + strategic_weight("frontier_redeploy_bias") * 0.85 * max(0.0, target_frontier - source_frontier)
                + w["defense_bias"] * max(0, enemy_pressure(dst, pid) - enemy_pressure(src, pid)) * 0.45
                + w["choke_bias"] * (CHOKE_VALUES.get(dst, 0.0) - CHOKE_VALUES.get(src, 0.0)) * 1.8
                + w["mission_focus"] * (mission_deploy_value(pid, dst) - 0.35 * mission_deploy_value(pid, src))
                + random() * 0.05
            )
            if score > 0.65:
                fraction = 0.35 + 0.45 * w["advance_bias"]
                if border_count(src, pid) == 0 and border_count(dst, pid) > 0:
                    fraction += 0.18
                amount = max(1, round(min(movable_total, source_excess) * fraction))
                candidates.append((score, (src, dst, min(movable_total, amount))))
    return choose_scored(candidates)


def perform_ai_move(pid: int, move: tuple[str, str, int] | None) -> str:
    if not move:
        log(f"{GAME['players'][str(pid)]['name']} declines to move armies.")
        return "declined move"
    src, dst, amount = move
    amount = max(1, min(amount, strength(src) - 1))
    set_strength(src, strength(src) - amount)
    set_strength(dst, strength(dst) + amount)
    add_stat(pid, "moves")
    log(f"{GAME['players'][str(pid)]['name']} moves {amount} armies from {territory_name(src)} to {territory_name(dst)}.")
    check_victory(pid)
    return f"moved {amount} from {territory_name(src)} to {territory_name(dst)}"


def ai_step_once() -> tuple[bool, str]:
    if not GAME["started"]:
        return False, "Start a game first."
    if GAME.get("winner_id"):
        return True, "game over"
    pid = current_player_id()
    if not pid or not is_ai_player(pid):
        return False, "Current player is not an AI commander."

    p = GAME["players"][str(pid)]
    phase = GAME["phase"]

    if phase == "initial_deploy":
        if p["reserve"] > 0:
            return True, deploy_one_ai_army(pid, setup=True)
        advance_initial_deploy_turn()
        return True, "advanced setup deployment"

    if phase == "reinforce":
        trade_set = choose_trade_set(pid)
        should_trade = trade_set and (must_trade_cards(pid) or (len(p["cards"]) >= 3 and personality(pid)["trade_eagerness"] > 0.5 and p["reserve"] <= 1))
        if should_trade:
            return True, apply_card_trade(pid, trade_set)
        if p["reserve"] > 0:
            return True, deploy_all_ai_reserves(pid)
        enter_attack_phase(p)
        return True, "advanced to attack"

    if phase == "attack":
        if GAME.get("pending_attack"):
            src = GAME["pending_attack"]["from"]
            dst = GAME["pending_attack"]["to"]
            attack_dice = ai_attack_dice(pid, src, dst)
            defence_dice = min(2, strength(dst))
            advance = ai_advance_armies(pid, src, dst, attack_dice)
            ok, msg = resolve_pending_attack(attack_dice, defence_dice, advance)
            return ok, msg

        chosen = choose_attack(pid)
        if chosen:
            src, dst = chosen
            GAME["selected"] = src
            GAME["pending_attack"] = {
                "from": src,
                "to": dst,
                "max_attack_dice": min(3, strength(src) - 1),
                "max_defence_dice": min(2, strength(dst)),
            }
            log(f"{p['name']} prepares to attack {territory_name(dst)} from {territory_name(src)}.")
            return True, f"prepared attack from {territory_name(src)} to {territory_name(dst)}"

        enter_move_phase(p)
        return True, "advanced to move"

    if phase == "move":
        perform_ai_move(pid, choose_move(pid))
        if not GAME.get("winner_id"):
            finish_turn_after_move()
        return True, "finished move"

    return False, "AI cannot act in this phase."

@app.post("/api/new")
def api_new():
    global GAME
    data = request.get_json(force=True) or {}
    raw_players = data.get("players", [])
    configs = []
    for i, item in enumerate(raw_players, start=1):
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            kind = str(item.get("kind", "human")).strip().lower()
            ai_persona = str(item.get("ai_personality") or DEFAULT_PERSONALITY_BY_PLAYER.get(i, "Balanced General")).strip()
        else:
            name = str(item).strip()
            kind = "human"
            ai_persona = DEFAULT_PERSONALITY_BY_PLAYER.get(i, "Balanced General")
        if not name:
            continue
        if kind not in {"human", "ai"}:
            kind = "human"
        if ai_persona not in AI_PERSONALITIES:
            ai_persona = DEFAULT_PERSONALITY_BY_PLAYER.get(i, "Balanced General")
        configs.append({"name": name, "kind": kind, "ai_personality": ai_persona})

    if not 2 <= len(configs) <= 6:
        return jsonify({"ok": False, "error": "Use between 2 and 6 players."}), 400
    mode = str(data.get("mode", "global")).strip().lower()
    if mode not in {"global", "missions"}:
        return jsonify({"ok": False, "error": "Choose Global Domination or Secret Missions."}), 400

    GAME = new_empty_game()
    GAME["started"] = True
    GAME["mode"] = mode
    GAME["phase"] = "initial_deploy"
    GAME["turn"] = 0

    for i, cfg in enumerate(configs, start=1):
        GAME["players"][str(i)] = {
            "id": i,
            "name": cfg["name"],
            "kind": cfg["kind"],
            "ai_personality": cfg["ai_personality"],
            "reserve": INITIAL_ARMIES[len(configs)],
            "cards": [],
            "mission_id": None,
            "conquered_this_turn": False,
            "eliminated": False,
        }
        ensure_stats(i)

    if mode == "missions":
        mission_deck = MISSION_DECK[:]
        shuffle(mission_deck)
        for i in range(1, len(configs) + 1):
            GAME["players"][str(i)]["mission_id"] = mission_deck.pop()["id"]

    deck = TERRITORY_ORDER[:]
    shuffle(deck)
    for i, safe in enumerate(deck):
        pid = (i % len(configs)) + 1
        set_owner(safe, pid)
        set_strength(safe, 1)
        GAME["players"][str(pid)]["reserve"] -= 1

    GAME["current_player"] = 1
    mode_name = "Secret Missions" if mode == "missions" else "Global Domination"
    ai_count = sum(1 for cfg in configs if cfg["kind"] == "ai")
    ai_note = f" with {ai_count} AI commanders" if ai_count else ""
    log(f"{mode_name}: territory cards dealt to {len(configs)} commanders{ai_note}. Initial deployment begins.")
    return jsonify({"ok": True, "state": public_state()})


@app.post("/api/click")
def api_click():
    data = request.get_json(force=True) or {}
    safe = data.get("territory")
    if safe not in TERRITORY_INFO or not GAME["started"]:
        return jsonify({"ok": False, "error": "Invalid territory."}), 400

    pid = current_player_id()
    p = GAME["players"].get(str(pid))
    if not p:
        return jsonify({"ok": False, "error": "No current player."}), 400

    phase = GAME["phase"]

    if phase in {"initial_deploy", "reinforce"}:
        if owner(safe) != pid:
            return jsonify({"ok": False, "error": "You may only deploy to your own territories."}), 400
        if p["reserve"] <= 0:
            return jsonify({"ok": False, "error": "No reserve armies remain."}), 400
        deploy_amount = 1
        if phase == "reinforce":
            try:
                deploy_amount = int(data.get("amount", 1))
            except (TypeError, ValueError):
                deploy_amount = 1
            deploy_amount = max(1, min(10, deploy_amount, p["reserve"]))
        set_strength(safe, strength(safe) + deploy_amount)
        p["reserve"] -= deploy_amount
        army_word = "army" if deploy_amount == 1 else "armies"
        log(f"{p['name']} deploys {deploy_amount} {army_word} to {territory_name(safe)}.")
        if phase == "initial_deploy":
            advance_initial_deploy_turn()
        check_victory(pid)
        return jsonify({"ok": True, "state": public_state()})

    if phase == "attack":
        if owner(safe) == pid:
            if safe in valid_attackers(pid):
                GAME["selected"] = safe
                GAME["pending_attack"] = None
                return jsonify({"ok": True, "state": public_state()})
            return jsonify({"ok": False, "error": "Choose a territory with at least 2 armies and an enemy neighbour."}), 400

        selected = GAME.get("selected")
        if selected and safe in valid_attack_targets(selected, pid):
            max_attack = min(3, strength(selected) - 1)
            max_defence = min(2, strength(safe))
            GAME["pending_attack"] = {
                "from": selected,
                "to": safe,
                "max_attack_dice": max_attack,
                "max_defence_dice": max_defence,
            }
            log(f"{p['name']} prepares to attack {territory_name(safe)} from {territory_name(selected)}.")
            return jsonify({"ok": True, "state": public_state()})
        return jsonify({"ok": False, "error": "Select one of the highlighted enemy territories."}), 400

    if phase == "move":
        selected = GAME.get("selected")
        if owner(safe) != pid:
            return jsonify({"ok": False, "error": "Move phase only uses your own territories."}), 400
        if selected and safe in valid_move_targets(selected, pid):
            try:
                amount = int(data.get("amount"))
            except (TypeError, ValueError):
                return jsonify({"ok": False, "error": "Move cancelled or invalid amount."}), 400
            if amount < 1:
                return jsonify({"ok": False, "error": "Move at least one army, or use Next phase to decline moving."}), 400
            amount = min(amount, strength(selected) - 1)
            set_strength(selected, strength(selected) - amount)
            set_strength(safe, strength(safe) + amount)
            add_stat(pid, "moves")
            log(f"{p['name']} moves {amount} armies from {territory_name(selected)} to {territory_name(safe)}.")
            GAME["selected"] = None
            check_victory(pid)
            if not GAME.get("winner_id"):
                finish_turn_after_move()
            return jsonify({"ok": True, "state": public_state()})
        if safe in valid_movers(pid):
            GAME["selected"] = safe
            return jsonify({"ok": True, "state": public_state()})
        return jsonify({"ok": False, "error": "Choose a highlighted origin or destination."}), 400

    return jsonify({"ok": False, "error": "This phase does not accept map clicks."}), 400


@app.post("/api/attack/roll")
def api_attack_roll():
    data = request.get_json(force=True) or {}
    ok, message = resolve_pending_attack(
        data.get("attack_dice"),
        data.get("defence_dice"),
        data.get("advance_armies"),
    )
    if not ok:
        return json_error(message)
    return json_state()


@app.post("/api/attack/stop")
def api_attack_stop():
    GAME["pending_attack"] = None
    GAME["selected"] = None
    return jsonify({"ok": True, "state": public_state()})


@app.post("/api/cards/trade")
def api_trade_cards():
    data = request.get_json(force=True) or {}
    if GAME["phase"] != "reinforce":
        return jsonify({"ok": False, "error": "Cards can only be traded during reinforce."}), 400
    pid = current_player_id()
    p = GAME["players"][str(pid)]
    ids = set(data.get("card_ids", []))
    cards = [c for c in p["cards"] if c["id"] in ids]
    if not is_valid_trade(cards):
        return jsonify({"ok": False, "error": "Trade must be three matching cards or one of each type."}), 400

    apply_card_trade(pid, cards)
    check_victory(pid)
    return jsonify({"ok": True, "state": public_state()})


@app.post("/api/phase/next")
def api_next_phase():
    if not GAME["started"]:
        return jsonify({"ok": False, "error": "Start a game first."}), 400
    phase = GAME["phase"]
    pid = current_player_id()
    p = GAME["players"][str(pid)]

    if phase == "initial_deploy":
        remaining = sum(
            player.get("reserve", 0)
            for player in GAME["players"].values()
            if not player.get("eliminated")
        )
        if remaining > 0:
            return jsonify({"ok": False, "error": "Initial deployment must rotate one army at a time. Click one owned territory for the current player."}), 400
        advance_initial_deploy_turn()
        return jsonify({"ok": True, "state": public_state()})

    if phase == "reinforce":
        if must_trade_cards(pid):
            return jsonify({"ok": False, "error": "You have five or more cards and must trade a set."}), 400
        if p["reserve"] > 0:
            return jsonify({"ok": False, "error": f"Deploy {p['reserve']} reserve armies before attacking."}), 400
        enter_attack_phase(p)
        return json_state()

    if phase == "attack":
        enter_move_phase(p)
        return json_state()

    if phase == "move":
        check_victory(pid)
        if not GAME.get("winner_id"):
            finish_turn_after_move()
        return jsonify({"ok": True, "state": public_state()})

    return jsonify({"ok": False, "error": "No phase transition is available."}), 400



@app.post("/api/ai/step")
def api_ai_step():
    ok, message = ai_step_once()
    if not ok:
        return json_error(message)
    return jsonify({"ok": True, "message": message, "state": public_state()})



if __name__ == "__main__":
    app.run(debug=True, port=5000)
