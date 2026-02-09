# AGENT.md

## Project intent

This repo analyzes **Shanghai weather and air quality** to test common claims (hotter summers, changing rainfall, improving or worsening air quality). The output is **clear, explainable charts** presented in two modes: guided storytelling and free data exploration.

The project favors clarity, simple methods, and shareable visuals over complex modeling or infrastructure.

---

## Working environment (WSL)

- This repo is developed and run **inside WSL**.
- Assume file paths, tooling, and commands are executed in Linux.
- Do not optimize for Windows path assumptions (e.g. `\\wsl.localhost\...`).

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

## Data policy

- Input data is already cleaned and trusted
- **Source-of-truth stays in CSV** (easy to inspect and replace)
- **Derived JSON is allowed** for chart-ready payloads (smaller/faster), e.g. monthly rollups
- Weather and AQI data live in static files under `public/data/`

Agents may reorganize the repo freely (including moving the top-level cleaned CSV) as long as structure remains clear and minimal.

---

## Allowed restructuring

Agents may:

- Move cleaned data into `public/data/`
- Add `public/data/derived/` for pre-aggregated outputs
- Split logic between data loading, transforms, and chart primitives
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

```text
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
