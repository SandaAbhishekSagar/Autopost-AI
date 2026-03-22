# Autopost-AI

AI-powered LinkedIn post generator with **blog mode** (pulls posts from [abhisheksagarsanda.com](https://www.abhisheksagarsanda.com/blog)) and optional tech-news modes.

## Project layout

| Path | Purpose |
|------|---------|
| **`LinkedIn/`** | Flask app, CLI agent, config — **this is what you deploy** |

## Quick start

```bash
cd LinkedIn
pip install -r requirements.txt
cp config.example.yaml config.yaml
# Edit config.yaml with OPENAI_API_KEY and LinkedIn credentials
python app.py
```

Open `http://localhost:5000`.

## Hosting

Set your platform’s **root directory to `LinkedIn`** (or deploy only that folder). See **`LinkedIn/DEPLOY.md`** for Railway, env vars, and health checks (`/health`).

## Documentation

- **`LinkedIn/README.md`** — features, CLI, configuration
- **`LinkedIn/DEPLOY.md`** — production deployment
