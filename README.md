# news-digest

Daily multi-region news digest via ntfy.sh. Scheduled via Claude Code Routines.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key (claude-sonnet-4-6) |
| `NTFY_TOPIC` | Yes | ntfy.sh topic name |
| `PUBLIC_URL_BASE` | Yes | GitHub Pages base URL (e.g. `https://smatsu77.github.io/news-digest`) |
| `NTFY_SERVER` | No | Custom ntfy server (default: `https://ntfy.sh`) |
| `NTFY_TOKEN` | No | ntfy auth token |

## Local Run

```bash
pip install -r requirements.txt

# Validate RSS feeds first
python fetch.py

# Full pipeline (set env vars first)
python main.py
```

## GitHub Pages

Enable at: `Settings > Pages > Source: Deploy from branch: main /docs`

Your digest URL: `https://smatsu77.github.io/news-digest/latest.html`

## Claude Code Routine Setup

### Create the Routine

Go to https://claude.ai/code/routines and click **New Routine**, or use the Claude Code CLI:

```
/schedule
```

### Routine Settings

| Field | Value |
|-------|-------|
| Name | `morning-news-digest` |
| Repository | `https://github.com/smatsu77/news-digest` |
| Branch | `main` |
| Schedule | Weekday daily, `02:15 UTC` (= JST 11:15) |
| Model | `claude-sonnet-4-6` |

### Environment Variables (set in Routine UI)

- `ANTHROPIC_API_KEY` — your Anthropic API key
- `NTFY_TOPIC` — your ntfy topic
- `PUBLIC_URL_BASE` — `https://smatsu77.github.io/news-digest`

### Routine Prompt (paste verbatim)

```
You are running the daily news-digest pipeline.

Steps:
1. Run: pip install -r requirements.txt
2. Run: python main.py

Environment variables ANTHROPIC_API_KEY, NTFY_TOPIC, and PUBLIC_URL_BASE are already set in this environment.

If any RSS source fails to fetch, skip it and continue (fetch.py handles this automatically).
If ntfy fails, log the error but do not exit — the HTML was still generated and pushed.
Do not modify any source files. Just run the pipeline.
```

### Manual Trigger

```
/schedule run morning-news-digest
```

Or in the Claude.ai web UI: open the Routine → click **Run now**.

### View Logs

```
/schedule logs morning-news-digest
```

### Pause / Delete (to stop the Routine)

```
/schedule pause morning-news-digest    # pause without deleting
/schedule delete morning-news-digest   # permanent delete
```

> **Note:** Pro plan allows up to 5 Routine runs per day. This Routine runs once per weekday.

## Manual Steps You Need to Do

After code is pushed, perform these steps yourself:

1. **ntfy app** — Install the ntfy app on your phone and subscribe to your topic
2. **GitHub Pages** — Go to `https://github.com/smatsu77/news-digest/settings/pages`, set Source to `main` branch, `/docs` folder
3. **Create Routine** — Go to https://claude.ai/code/routines, create Routine with settings above
4. **Set env vars** — Enter `ANTHROPIC_API_KEY`, `NTFY_TOPIC`, `PUBLIC_URL_BASE` in the Routine UI
5. **Test run** — Click "Run now" in the Routine UI to verify notification arrives and link opens
6. **Confirm schedule** — Verify the Routine is active for weekday 02:15 UTC runs

## Adding More Sources

Edit the `SOURCES` list in `config.py`. Run `python fetch.py` to validate new URLs.
