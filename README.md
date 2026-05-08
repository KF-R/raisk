# raisk: a Risk UI using Python,HTML,CSS,SVG,JS

### v0.1.4

## Run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000


## AI players

- Each player can be set to `Human` or `AI` in the new-game menu.
- Each AI player can be assigned one of six personalities.
- Each player colour has a default AI personality:
  - Crimson: Aggressive Expansionist
  - Royal Blue: Balanced General
  - Rifle Green: Continental Strategist
  - Imperial Gold: Mission Fanatic
  - Prussian Black: Cautious Defender
  - Rose: Opportunist Assassin
- AI personality weights and map choke-point weights live in `ai_personalities.py`.
- Browser UI automatically advances AI turns while leaving human turns interactive.
- AI currently handles initial deployment, reinforcement placement, card trading, attack selection, dice selection, conquest advancement, one allowed move/fortification, Global Domination priorities, and Secret Mission priorities.
- AI scoring accounts for risk profile, attack/defence bias, cards, opportunism, choke points, continent control, mission progress, and vulnerable opponents.

## Features

- Global Domination and Secret Missions victory modes.
- Secret Missions mode deals one unique mission card from a twelve-card mission deck to each player before initial deployment.
- The current player's mission is rendered as a small, discreet slip near the bottom of the UI and is not included for non-current players in `/api/state`.
- Secret mission victory checks cover territory-count goals, continent-pair goals, 18 territories with at least two armies each, and colour-destruction goals. - Pink maps to Rose; Yellow maps to Imperial Gold.
- Initial deployment rotates one army at a time: Player 1 places one army, then Player 2, and so on until all setup reserves are exhausted.
- Normal play begins automatically with Player 1's first Reinforce phase after setup placement completes.
- Move phase permits exactly one friendly transfer, or declining via Next Phase.
- Attack UI permits selectable attack dice, defender dice, and conquest advance size.
- Defeated players' cards transfer to the player who conquered their final territory.
- Shift-click to place ten reinforcements per click instead of the usual one

## SVG click-layer notes

- The supplied SVG keeps territory paths inside `<defs><g id="map">` and renders them through `<use>`, so browser clicks do not reliably reach the definition paths. The server duplicates the real path geometry into a transparent `#territory_hit_layer` above the rendered map.
- The transparent territory hit layer is precomputed once at startup.
- Client click handling targets `data-safe` on that concrete hit layer instead of relying on events from `<use>` shadow instances.
- The board toolbar includes a `colour territories` checkbox. When enabled, territory path fill colour follows owner colour. When disabled, only the army marker changes colour and the original map fill remains visible.
- `/api/svg` accepts `?owner_fills=1` or `?owner_fills=0`.
