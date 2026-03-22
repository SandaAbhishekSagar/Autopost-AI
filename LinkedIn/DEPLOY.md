# Deploying AutoPost AI (Flask web app)

The app lives in the **`LinkedIn/`** folder. Point your host’s **root directory** to `LinkedIn` (or deploy only that folder).

## Requirements

- Python **3.11+** (see `runtime.txt` if present)
- **OpenAI API key** (post generation; news search only if `NEWS_FETCH_METHOD` is `ai` or `both`)
- **LinkedIn access token** with `w_member_social` (and related scopes) for posting

## Health check

After deploy, verify:

```http
GET /health
```

Returns `{"status":"ok","service":"autopost-ai"}` — use this for Railway, Render, Fly.io, UptimeRobot, etc.

## Production server

- **Procfile** uses **Gunicorn** (not `flask run`). `PORT` is read from the environment automatically.
- **Local dev** (Windows/macOS): `python app.py` — Gunicorn is optional locally.

## Railway

1. New project → Deploy from GitHub → select this repo.
2. **Settings → Root Directory:** `LinkedIn`
3. **Variables** (minimum):

| Variable | Example / notes |
|----------|------------------|
| `OPENAI_API_KEY` | `sk-...` |
| `LINKEDIN_ACCESS_TOKEN` | OAuth token from LinkedIn app |
| `NEWS_FETCH_METHOD` | `blog` (recommended) |
| `OPENAI_MODEL` | `gpt-4o` |
| `PROFILE_NAME` | Your name |
| `PROFILE_TITLE` | Short headline |
| `BLOG_URL` | `https://www.abhisheksagarsanda.com/blog` |
| `BLOG_LINKEDIN_URL` | `https://www.linkedin.com/in/sandaabhisheksagar/` |

Optional (pipe `|` separates list items for metrics/credentials):

- `PROFILE_SUMMARY` — one-line or short paragraph professional summary
- `PROFILE_NOTABLE_METRICS` — e.g. `Metric one|Metric two|Metric three`
- `PROFILE_CREDENTIALS` — e.g. `TA Northeastern 2025|Hackathon winner`
- `BLOG_HASHTAGS` — e.g. `#AI,#RAG,#ConversationalAI`

If **`config.yaml` is missing**, the app builds config from env (see `agent.py` → `_create_config_from_env`).

4. Deploy. Railway sets `PORT` automatically.

## Render / Fly.io / similar

- **Build command:** `pip install -r requirements.txt`
- **Start command:** same as Procfile, or:

  ```bash
  gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
  ```

- Set the same env vars as above.

## Security

- Do **not** commit `config.yaml` with real keys (it is `.gitignore`d).
- Prefer **environment variables** on the host for all secrets.
- Rotate LinkedIn tokens before they expire.

## Troubleshooting

- **502 / app won’t start:** Check logs; ensure `gunicorn` installed (`requirements.txt`) and `app:app` matches `app.py`.
- **“Failed to initialize agent”:** Missing `OPENAI_API_KEY` or `LINKEDIN_ACCESS_TOKEN` in env when no valid `config.yaml`.
- **Blog posts empty:** Confirm `NEWS_FETCH_METHOD=blog` and that `https://www.abhisheksagarsanda.com/.netlify/functions/blog-list` returns JSON from the server (same domain as your site).
