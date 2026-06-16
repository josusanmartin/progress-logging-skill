# Progress Logging Skill

Deterministic progress logging and representation for measured work.

This repo spins the logging/dashboard scripts out of `problem-agnostic-optimization` into a narrower skill. It does not pick optimization candidates or define promotion rules. It makes agents keep a proper evidence surface:

- `work/progress.tsv` for measured score/performance rows
- `work/log.md` for explicit UTC token/time snapshots
- `work/state.json` for current state and latest usage snapshot
- `work/progress.svg` and `work/dashboard.html` for deterministic representation

## Use

Initialize:

```bash
python skills/progress-logging/scripts/init_progress.py --metric cycles --direction lower --candidate-number
```

After each measured result, record token/time usage first:

```bash
python skills/progress-logging/scripts/record_usage.py \
  --label cand_0007 \
  --wall-seconds 1080 \
  --tokens-total 4500 \
  --input-tokens 3200 \
  --cached-input-tokens 1400 \
  --output-tokens 900 \
  --reasoning-output-tokens 400
```

Then append the measured row:

```bash
python skills/progress-logging/scripts/record_progress.py \
  --candidate cand_0007 \
  --candidate-number 7 \
  --metric cycles=2226 \
  --decision promote \
  --tokens-total 4500 \
  --wall-seconds 1080 \
  --label "scheduled vector kernel"
```

Render:

```bash
python skills/progress-logging/scripts/render_progress.py --ylabel cycles --direction lower
```

## Validate

```bash
python -m pip install -r requirements-dev.txt
./scripts/validate.sh
python -m pytest -q
```
