from __future__ import annotations

from html import escape
from pathlib import Path
from random import choice, randint, shuffle
import re
import time
import uuid

from flask import Flask, jsonify, render_template, request, Response

app = Flask(__name__)

# Territory_owner is a player number, territory_strength is army count.
PLAYER_COLOURS = {
    0: {"name": "Unclaimed", "path": "#d9c8a8", "army": "none", "ink": "#2a2117"},
    1: {"name": "Crimson", "path": "#8f1d24", "army": "#b21f2d", "ink": "#fff2df"},
    2: {"name": "Royal Blue", "path": "#1e4f8f", "army": "#2563b8", "ink": "#fff2df"},
    3: {"name": "Rifle Green", "path": "#2f6a3f", "army": "#397d4a", "ink": "#fff2df"},
    4: {"name": "Imperial Gold", "path": "#d6aa32", "army": "#f0c541", "ink": "#23180d"},
    5: {"name": "Prussian Black", "path": "#232323", "army": "#111111", "ink": "#fff2df"},
    6: {"name": "Rose", "path": "#c46c9c", "army": "#e58abb", "ink": "#23180d"},
}

# safe_name, display_name, label_x, label_y, army_offset_x, army_offset_y, territory_owner, territory_strength, neighbours
BLANK_MAP_DATA = [
    ("alaska", "Alaska", 223, 213, 0, 0, 0, 0, ["northwest_territory", "alberta", "kamchatka"]),
    ("alberta", "Alberta", 287, 252, 0, 0, 0, 0, ["alaska", "northwest_territory", "ontario", "western_us"]),
    ("central_america", "Central\nAmerica", 295, 352, 0, 0, 0, 0, ["western_us", "eastern_us", "venezuela"]),
    ("eastern_us", "Eastern\nUS", 342, 312, 0, 0, 0, 0, ["ontario", "quebec", "western_us", "central_america"]),
    ("greenland", "Greenland", 433, 180, 0, 40, 0, 0, ["northwest_territory", "ontario", "quebec", "iceland"]),
    ("northwest_territory", "Northwest\nTerritory", 300, 199, 0, 0, 0, 0, ["alaska", "alberta", "ontario", "greenland"]),
    ("ontario", "Ontario", 336, 261, 0, 0, 0, 0, ["northwest_territory", "alberta", "western_us", "eastern_us", "quebec", "greenland"]),
    ("quebec", "Quebec", 387, 254, 0, 0, 0, 0, ["ontario", "eastern_us", "greenland"]),
    ("western_us", "Western\nUS", 290, 290, 0, 0, 0, 0, ["alberta", "ontario", "eastern_us", "central_america"]),

    ("argentina", "Argen-\ntina", 367, 518, 0, 0, 0, 0, ["peru", "brazil"]),
    ("brazil", "Brazil", 403, 447, 0, 0, 0, 0, ["venezuela", "peru", "argentina", "north_africa"]),
    ("venezuela", "Venezuela", 355, 402, 0, 0, 0, 0, ["central_america", "peru", "brazil"]),
    ("peru", "Peru", 353, 466, 0, 0, 0, 0, ["venezuela", "brazil", "argentina"]),

    ("great_britain", "Great\nBritain", 462, 262, 0, 0, 0, 0, ["iceland", "scandinavia", "northern_europe", "western_europe"]),
    ("iceland", "Iceland", 485, 225, 0, 0, 0, 0, ["greenland", "great_britain", "scandinavia"]),
    ("northern_europe", "Northern\nEurope", 540, 289, 0, 0, 0, 0, ["great_britain", "scandinavia", "ukraine", "southern_europe", "western_europe"]),
    ("scandinavia", "Scandi-\nnavia", 553, 203, 0, 0, 0, 0, ["iceland", "great_britain", "northern_europe", "ukraine"]),
    ("southern_europe", "Southern\nEurope", 549, 331, 0, 0, 0, 0, ["western_europe", "northern_europe", "ukraine", "middle_east", "egypt", "north_africa"]),
    ("ukraine", "Ukraine", 608, 262, 0, 0, 0, 0, ["scandinavia", "northern_europe", "southern_europe", "middle_east", "afghanistan", "ural"]),
    ("western_europe", "Western\nEurope", 480, 350, 0, 0, 0, 0, ["great_britain", "northern_europe", "southern_europe", "north_africa"]),

    ("congo", "Congo", 571, 498, 0, 0, 0, 0, ["north_africa", "east_africa", "south_africa"]),
    ("east_africa", "East\nAfrica", 603, 451, 0, 0, 0, 0, ["egypt", "north_africa", "congo", "south_africa", "madagascar", "middle_east"]),
    ("egypt", "Egypt", 574, 410, 0, 0, 0, 0, ["southern_europe", "north_africa", "east_africa", "middle_east"]),
    ("madagascar", "Mada-\ngascar", 638, 559, 0, 0, 0, 0, ["east_africa", "south_africa"]),
    ("north_africa", "North\nAfrica", 515, 430, 0, 0, 0, 0, ["brazil", "western_europe", "southern_europe", "egypt", "east_africa", "congo"]),
    ("south_africa", "South\nAfrica", 580, 550, 0, 0, 0, 0, ["congo", "east_africa", "madagascar"]),

    ("afghanistan", "Afgha-\nnistan", 674, 307, 0, 0, 0, 0, ["ukraine", "ural", "china", "india", "middle_east"]),
    ("china", "China", 757, 347, 0, 0, 0, 0, ["afghanistan", "ural", "siberia", "mongolia", "siam", "india"]),
    ("india", "India", 712, 382, 0, 0, 0, 0, ["middle_east", "afghanistan", "china", "siam"]),
    ("irkutsk", "Irkutsk", 758, 260, 0, 0, 0, 0, ["siberia", "yakutsk", "kamchatka", "mongolia"]),
    ("japan", "Japan", 853, 293, 0, 0, 0, 0, ["kamchatka", "mongolia"]),
    ("kamchatka", "Kamchatka", 820, 215, 0, 0, 0, 0, ["alaska", "yakutsk", "irkutsk", "mongolia", "japan"]),
    ("middle_east", "Middle\nEast", 627, 370, 0, 0, 0, 0, ["southern_europe", "ukraine", "afghanistan", "india", "east_africa", "egypt"]),
    ("mongolia", "Mongolia", 777, 296, 0, 0, 0, 0, ["siberia", "irkutsk", "kamchatka", "japan", "china"]),
    ("siam", "Siam", 766, 400, 0, 0, 0, 0, ["india", "china", "indonesia"]),
    ("siberia", "Siberia", 723, 215, 0, 0, 0, 0, ["ural", "china", "mongolia", "irkutsk", "yakutsk"]),
    ("ural", "Ural", 683, 240, 0, 0, 0, 0, ["ukraine", "afghanistan", "china", "siberia"]),
    ("yakutsk", "Yakutsk", 779, 194, 0, 0, 0, 0, ["siberia", "irkutsk", "kamchatka"]),

    ("eastern_australia", "Eastern\nAustralia", 854, 535, 0, 0, 0, 0, ["new_guinea", "western_australia"]),
    ("new_guinea", "New\nGuinea", 839, 464, 0, 0, 0, 0, ["indonesia", "western_australia", "eastern_australia"]),
    ("indonesia", "Indonesia", 755, 489, 0, 0, 0, 0, ["siam", "new_guinea", "western_australia"]),
    ("western_australia", "Western\nAustralia", 810, 558, 0, 0, 0, 0, ["indonesia", "new_guinea", "eastern_australia"]),
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
INITIAL_ARMIES = {2: 40, 3: 35, 4: 30, 5: 25, 6: 20}
CARD_TYPES = ["infantry", "cavalry", "artillery"]
CARD_ICONS = {"infantry": "♟", "cavalry": "♞", "artillery": "✹"}
TRADE_VALUES = [4, 6, 8, 10, 12, 15]

def new_empty_game() -> dict:
    return {
        "started": False,
        "phase": "pregame",
        "turn": 0,
        "current_player": 0,
        "players": {},
        "territories": {safe: {"owner": 0, "strength": 0} for safe in TERRITORY_ORDER},
        "selected": None,
        "pending_attack": None,
        "last_battle": None,
        "trade_count": 0,
        "log": ["Prepare the campaign table."],
    }


GAME = new_empty_game()


def log(message: str) -> None:
    GAME["log"].insert(0, f"{time.strftime('%H:%M:%S')} — {message}")
    del GAME["log"][60:]


def current_player() -> dict | None:
    pid = GAME["current_player"]
    return GAME["players"].get(str(pid))


def current_player_id() -> int:
    return int(GAME["current_player"] or 0)


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


def winner() -> dict | None:
    living = [p for p in GAME["players"].values() if not p.get("eliminated")]
    if GAME["started"] and len(living) == 1:
        return living[0]
    return None


def make_card() -> dict:
    typ = choice(CARD_TYPES)  # Original non-wild deck: 14/14/14, so equal chance by type.
    safe = choice(TERRITORY_ORDER)
    return {
        "id": uuid.uuid4().hex[:10],
        "type": typ,
        "icon": CARD_ICONS[typ],
        "territory": safe,
        "territory_name": territory_name(safe),
    }


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
    p["conquered_this_turn"] = False
    log(f"{p['name']} begins Reinforce and receives {gained} armies.")


def finish_turn_after_move() -> None:
    pid = current_player_id()
    p = GAME["players"][str(pid)]
    if p.get("conquered_this_turn"):
        card = make_card()
        p["cards"].append(card)
        log(f"{p['name']} draws a {card['type']} card for conquering territory.")

    next_pid = next_active_player(pid)
    if next_pid <= pid:
        GAME["turn"] += 1
    begin_turn(next_pid)


def advance_initial_deploy_turn() -> None:
    """Rotate initial setup one army at a time.

    Risk's opening placement is not player-by-player bulk deployment. After a
    player places one army, the next player with setup reserves gets exactly
    one placement opportunity. When all setup reserves are empty, normal play
    begins with player 1's first Reinforce phase.
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

    next_name = GAME["players"][str(GAME["current_player"])] ["name"]
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


def public_state() -> dict:
    players = []
    for pid_s in sorted(GAME["players"], key=lambda x: int(x)):
        p = GAME["players"][pid_s]
        pid = int(pid_s)
        terrs = player_territories(pid)
        players.append({
            "id": pid,
            "name": p["name"],
            "colour": PLAYER_COLOURS[pid],
            "reserve": p["reserve"],
            "cards": p["cards"],
            "card_count": len(p["cards"]),
            "territory_count": len(terrs),
            "army_count": player_total_armies(pid),
            "continent_bonus": continent_bonus(pid),
            "eliminated": p.get("eliminated", False),
            "conquered_this_turn": p.get("conquered_this_turn", False),
        })

    return {
        "started": GAME["started"],
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
        "trade_count": GAME["trade_count"],
        "next_trade_value": trade_value(),
        "must_trade": bool(current_player_id() and must_trade_cards(current_player_id()) and GAME["phase"] == "reinforce"),
        "winner": winner(),
        "log": GAME["log"],
    }


def map_data_from_state() -> list[tuple]:
    rows = []
    for safe, formatted_name, x, y, ax, ay, _owner, _strength, ns in BLANK_MAP_DATA:
        rows.append((safe, formatted_name, x, y, ax, ay, owner(safe), strength(safe), ns))
    return rows


STATIC_DIR = Path(__file__).resolve().parent / "static"
MAP_HEAD = (STATIC_DIR / "svg_map_head.xml").read_text(encoding="utf-8")
MAP_TAIL = (STATIC_DIR / "svg_map_tail.xml").read_text(encoding="utf-8")



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


def drop_initial_group_close(svg_tail: str) -> str:
    """Remove the closing tag for the army layer supplied at the top of the tail."""
    return re.sub(r'^\s*</g>\s*', '', svg_tail, count=1)


TERRITORY_SAFE_NAMES = set(TERRITORY_ORDER)
TERRITORY_HIT_LAYER = make_hit_layer(MAP_HEAD, TERRITORY_SAFE_NAMES)
MAP_TAIL_AFTER_ARMIES = drop_initial_group_close(MAP_TAIL)


def generate_svg(map_data: list[tuple], owner_fills: bool = True) -> str:
    territory_styles = [
        "  <style id=\"risk_runtime_styles\">",
        "    #territory_names, #territory_names * { pointer-events: none; }",
        "    #region_labels, #region_labels * { pointer-events: none; }",
        "    #continents, #continents * { pointer-events: none; }",
        "    #armies_deployed, #armies_deployed * { pointer-events: none; }",
        "    #territory_hit_layer { pointer-events: all; }",
        "    #territory_hit_layer .territory-hit { fill: #fff; fill-opacity: 0; stroke: none; pointer-events: all; cursor: pointer; }",
    ]
    if owner_fills:
        for safe_name, _formatted_name, _x, _y, _ax, _ay, terr_owner, _strength, _neighbours in map_data:
            colour = PLAYER_COLOURS.get(terr_owner, PLAYER_COLOURS[0])["path"]
            territory_styles.append(f"    #map #{safe_name} {{ fill: {colour}; }}")
    territory_styles.append("  </style>\n")

    territory_code = ""
    army_code = "  </g>\n\n  <g id=\"armies_deployed\">\n"

    for safe_name, formatted_name, x, y, army_offset_x, army_offset_y, terr_owner, terr_strength, _neighbours in map_data:
        label = escape(formatted_name).replace("\n", "</tspan><tspan x=\"0\" dy=\"1em\">")
        territory_code += f'    <text id="label_{safe_name}" transform="translate({x},{y})"><tspan>{label}</tspan></text>\n'

        if terr_owner != 0:
            if terr_strength <= 9:
                scale = 1
            elif terr_strength < 40:
                scale = 0.9 + terr_strength / 50
            else:
                scale = 1.8

            army = PLAYER_COLOURS.get(terr_owner, PLAYER_COLOURS[0])
            text_fill = army["ink"]
            army_code += (
                f'    <g id="ag_{safe_name}" transform-origin="{x + army_offset_x} {y - 16 + army_offset_y}" transform="scale({scale:.2f})">'
                f'<use id="army_{safe_name}" xlink:href="#army" href="#army" x="{x + army_offset_x}" y="{y - 16 + army_offset_y}" '
                f'fill="{army["army"]}" stroke="{("black" if terr_strength >= 3 else "none")}"/>'
                f'<text id="army_{safe_name}_count" letter-spacing="-1" fill="{text_fill}" x="{x + army_offset_x - 0.5}" y="{y - 18 + army_offset_y}">{terr_strength}</text></g>\n'
            )

    army_code += "  </g>\n\n" + TERRITORY_HIT_LAYER

    return MAP_HEAD + "\n".join(territory_styles) + territory_code + army_code + MAP_TAIL_AFTER_ARMIES


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def api_state():
    return jsonify(public_state())


@app.get("/api/svg")
def api_svg():
    owner_fills = request.args.get("owner_fills", "1").lower() not in {"0", "false", "no", "off"}
    return Response(generate_svg(map_data_from_state(), owner_fills=owner_fills), mimetype="image/svg+xml")


@app.post("/api/new")
def api_new():
    global GAME
    data = request.get_json(force=True) or {}
    names = [str(name).strip() for name in data.get("players", []) if str(name).strip()]
    if not 2 <= len(names) <= 6:
        return jsonify({"ok": False, "error": "Use between 2 and 6 players."}), 400

    GAME = new_empty_game()
    GAME["started"] = True
    GAME["phase"] = "initial_deploy"
    GAME["turn"] = 0

    for i, name in enumerate(names, start=1):
        GAME["players"][str(i)] = {
            "id": i,
            "name": name,
            "reserve": INITIAL_ARMIES[len(names)],
            "cards": [],
            "conquered_this_turn": False,
            "eliminated": False,
        }

    deck = TERRITORY_ORDER[:]
    shuffle(deck)
    for i, safe in enumerate(deck):
        pid = (i % len(names)) + 1
        set_owner(safe, pid)
        set_strength(safe, 1)
        GAME["players"][str(pid)]["reserve"] -= 1

    GAME["current_player"] = 1
    log(f"Territory cards dealt to {len(names)} commanders. Initial deployment begins.")
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
        set_strength(safe, strength(safe) + 1)
        p["reserve"] -= 1
        log(f"{p['name']} deploys 1 army to {territory_name(safe)}.")
        if phase == "initial_deploy":
            advance_initial_deploy_turn()
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
            log(f"{p['name']} moves {amount} armies from {territory_name(selected)} to {territory_name(safe)}.")
            GAME["selected"] = None
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
    if GAME["phase"] != "attack" or not GAME.get("pending_attack"):
        return jsonify({"ok": False, "error": "No attack is pending."}), 400

    pid = current_player_id()
    p = GAME["players"][str(pid)]
    attack = GAME["pending_attack"]
    src, dst = attack["from"], attack["to"]

    if owner(src) != pid or owner(dst) in (0, pid) or dst not in neighbours(src) or strength(src) <= 1:
        GAME["pending_attack"] = None
        return jsonify({"ok": False, "error": "Attack is no longer valid."}), 400

    max_attack = min(3, strength(src) - 1)
    attack_dice = int(data.get("attack_dice", max_attack))
    attack_dice = max(1, min(attack_dice, max_attack))
    max_defence = min(2, strength(dst))
    defence_dice = int(data.get("defence_dice", max_defence))
    defence_dice = max(1, min(defence_dice, max_defence))

    attacker_rolls = sorted([randint(1, 6) for _ in range(attack_dice)], reverse=True)
    defender_rolls = sorted([randint(1, 6) for _ in range(defence_dice)], reverse=True)

    attacker_losses = 0
    defender_losses = 0
    comparisons = []
    for a, d in zip(attacker_rolls, defender_rolls):
        if a > d:
            defender_losses += 1
            comparisons.append({"a": a, "d": d, "winner": "attacker"})
        else:
            attacker_losses += 1
            comparisons.append({"a": a, "d": d, "winner": "defender"})

    set_strength(src, strength(src) - attacker_losses)
    set_strength(dst, strength(dst) - defender_losses)
    conquered = False
    old_owner = owner(dst)
    advance = 0

    if strength(dst) <= 0:
        conquered = True
        advance_max = max(1, strength(src) - 1)
        advance_min = min(attack_dice, advance_max)
        try:
            requested_advance = int(data.get("advance_armies", advance_max))
        except (TypeError, ValueError):
            requested_advance = advance_max
        advance = max(advance_min, min(requested_advance, advance_max))
        set_owner(dst, pid)
        set_strength(dst, advance)
        set_strength(src, strength(src) - advance)
        p["conquered_this_turn"] = True
        GAME["pending_attack"] = None
        GAME["selected"] = src if strength(src) > 1 else None
        log(f"{p['name']} conquers {territory_name(dst)} and advances {advance} armies.")
        if old_owner:
            check_eliminations(conqueror_pid=pid)
    else:
        if strength(src) <= 1:
            GAME["pending_attack"] = None
            GAME["selected"] = None
            log(f"{p['name']}'s attack stalls at {territory_name(src)}.")
        else:
            GAME["pending_attack"]["max_attack_dice"] = min(3, strength(src) - 1)
            GAME["pending_attack"]["max_defence_dice"] = min(2, strength(dst))

    GAME["last_battle"] = {
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
    return jsonify({"ok": True, "state": public_state()})


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

    value = trade_value()
    p["cards"] = [c for c in p["cards"] if c["id"] not in ids]
    p["reserve"] += value
    GAME["trade_count"] += 1

    bonus_safe = next((c["territory"] for c in cards if owner(c["territory"]) == pid), None)
    if bonus_safe:
        set_strength(bonus_safe, strength(bonus_safe) + 2)
        log(f"{p['name']} trades cards for {value} armies and gains +2 on {territory_name(bonus_safe)}.")
    else:
        log(f"{p['name']} trades cards for {value} reserve armies.")
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
        GAME["phase"] = "attack"
        GAME["selected"] = None
        GAME["pending_attack"] = None
        GAME["last_battle"] = None
        log(f"{p['name']} advances to Attack.")
        return jsonify({"ok": True, "state": public_state()})

    if phase == "attack":
        GAME["phase"] = "move"
        GAME["selected"] = None
        GAME["pending_attack"] = None
        log(f"{p['name']} advances to Move.")
        return jsonify({"ok": True, "state": public_state()})

    if phase == "move":
        finish_turn_after_move()
        return jsonify({"ok": True, "state": public_state()})

    return jsonify({"ok": False, "error": "No phase transition is available."}), 400


@app.post("/api/debug/card")
def api_debug_card():
    # Handy during UI testing; remove or protect for production.
    if not GAME["started"]:
        return jsonify({"ok": False, "error": "No game."}), 400
    p = current_player()
    p["cards"].append(make_card())
    return jsonify({"ok": True, "state": public_state()})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
