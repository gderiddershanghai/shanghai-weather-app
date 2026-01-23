# AGENT.md

## Project intent

This repo analyzes **Shanghai weather and air quality** to test common claims (hotter summers, changing rainfall, improving or worsening air quality). The output is **clear, explainable charts** presented in two modes: guided storytelling and free data exploration.

The project favors clarity, simple methods, and shareable visuals over complex modeling or infrastructure.

---

## Application modes

### 1) Story mode (scrollytelling)

- Walks the user through a fixed narrative
- Each section introduces one claim, one chart, and one takeaway
- Uses scroll-driven activation to transition charts and annotations
- Optimized for reading and sharing

### 2) Explore mode (interactive)

- Lets users freely inspect the data
- Supports filtering by time range, metric, and thresholds
- Uses the same charts as Story mode, without narrative constraints

Both modes must reuse the same data, chart primitives, and scales.

---

## Data assumptions

- Input data is already cleaned and trusted
- Weather and AQI data live in static files (CSV or JSON)
- Precomputed or derived datasets are allowed if they simplify rendering

Agents may **reorganize the repo freely**, including moving cleaned data files, as long as structure remains clear and minimal.

---

## Allowed restructuring

Agents may:

- Move cleaned data into a dedicated `public/data/` directory
- Split logic cleanly between data, charts, modes, and layout
- Rename files for clarity and consistency
- Add small helper modules when reuse is clear

---

## What not to do

- Do **not** modify or rely on `.ipynb` files
- Do **not** introduce backends, databases, or build-heavy frameworks
- Do **not** add complex statistical models or opaque transformations
- Do **not** duplicate chart logic between Story and Explore modes

---

## Expected folder structure (target)
public/
data/
weather_shanghai.csv
aqi_shanghai.csv
derived/

src/
app/
index.js
routes.js
state/

modes/
story/
explore/

viz/
charts/
data/
encodings/

components/
styles/

This structure is a guideline, not a constraint. Simpler is acceptable if clarity is preserved.

---

## Code expectations

- Prefer small, readable modules over abstraction
- Charts should be reusable and parameter-driven
- Transformations should be explicit and easy to explain
- Default to D3 primitives; avoid magic helpers

---

## Output expectations

- Every change should improve clarity or reduce duplication
- Visuals should support short, concrete claims
- The app should work as a static site with no build step

This file defines **agent behavior** and should not be treated as user-facing documentation.
