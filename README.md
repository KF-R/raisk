# Risk Flask UI

A minimalist Flask app serving a hot-seat Risk interface with a dynamically generated inline SVG board.

## Run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:5000


## Notes
- The board state is controlled by only two values per territory:
```python
territory_owner     # player number, 0 means unclaimed
territory_strength  # number of armies
```
- The  SVG keeps territory paths inside `<defs><g id="map">` and renders them through `<use>`, so browser clicks do not reliably reach the definition paths. The server duplicates the real path geometry into a transparent `#territory_hit_layer` above the rendered map.
- Client click handling targets `data-safe` on that concrete hit layer instead of relying on events from `<use>` shadow instances.
- The board toolbar includes a `colour territories` checkbox. When enabled, territory path fill colour follows owner colour. When disabled, only the army marker changes colour and the original map fill remains visible.
- `/api/svg` accepts `?owner_fills=1` or `?owner_fills=0`.

## Implemented flow

- 2–6 hot-seat players
- Random territory-card deal for initial ownership
- One-army-at-a-time initial deployment rotation
- Player table: territories, cards, reserves, armies, continent bonus
- Reinforce, attack, move turn cycle
- Risk-style card trades: three of a kind or one of each; escalating values 4/6/8/10/12/15/+5
- Selectable attacker and defender dice within Risk limits
- Automatic roll resolution and territory conquest
- Conquest card draw at end of turn

