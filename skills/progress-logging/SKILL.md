---
name: progress-logging
description: "Use when Codex needs deterministic progress logging and representation for any measured work: token usage snapshots, scores, performance metrics, candidate/result ledgers, progress SVGs, HTML dashboards, or handoff artifacts. Triggers include requests to track tokens, log benchmark or score progress, render a progress dashboard, keep a progress.tsv ledger, or make resource burn and metric movement visible without changing the underlying optimization strategy."
---

# Progress Logging

Maintain a deterministic progress surface for measured work. This skill records what happened; it does not choose optimization candidates or replace correctness/metric gates.

## Files

Default artifacts live in `work/`:

```text
work/progress.tsv
work/log.md
work/state.json
work/progress.svg
work/dashboard.html
```

## Initialize

Before the first measured result, run:

```bash
python skills/progress-logging/scripts/init_progress.py --metric score --direction lower
```

Use `--metric cycles`, `--metric latency`, `--metric accuracy`, or another authoritative metric name when known. Use `--direction higher` when larger values are better. Add `--candidate-number` if candidate names may contain unrelated digits.

## After Each Measured Result

Always try to capture token/time usage first. In Codex, call `get_goal` when available. Then record the explicit snapshot:

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

If some token fields are unavailable, omit only those fields. Do not invent missing token history or interpolate per-candidate usage.

Append exactly one measured-result row:

```bash
python skills/progress-logging/scripts/record_progress.py \
  --candidate cand_0007 \
  --metric cycles=2226 \
  --decision promote \
  --tokens-total 4500 \
  --wall-seconds 1080 \
  --label "dependency-list scheduled vector kernel"
```

Use `--score 0.992` for a default `score` column. Use `--metric name=value` for named metrics. Use `--metric-name cycles` for bug/crash rows with no numeric result. Use `--candidate-number 7` only when the TSV has a `candidate_number` column.

Render the visual artifacts:

```bash
python skills/progress-logging/scripts/render_progress.py \
  --ylabel cycles \
  --direction lower
```

## Rules

- `work/progress.tsv` is the score/performance ledger.
- `work/log.md` is the explicit token/time snapshot log.
- `work/state.json` stores the latest usage snapshot for dashboard headers.
- New progress rows must include `timestamp`, `candidate`, metric column, `decision`, `tokens_total`, `tokens_delta`, `wall_seconds`, and `label`.
- Timestamps must be UTC `YYYY-MM-DDTHH:MM:SSZ`.
- `wall_seconds` is cumulative elapsed wall time.
- Let `record_progress.py` compute `tokens_delta` from the previous cumulative total when possible.
- Missing early token history must stay unknown.
- The SVG/HTML dashboard is diagnostic; it must not replace correctness checks, benchmark authority, or promotion rules from another workflow.

## Script Map

| Need | Script |
|---|---|
| Initialize artifacts | `scripts/init_progress.py` |
| Record token/time usage | `scripts/record_usage.py` |
| Append score/performance row | `scripts/record_progress.py` |
| Render SVG and HTML | `scripts/render_progress.py` |
| Render only SVG | `scripts/progress_chart.py` |
| Render or serve dashboard | `scripts/progress_dashboard.py` |
