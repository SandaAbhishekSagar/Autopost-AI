# AutoPost AI - LinkedIn Content Generator

An intelligent agent that generates professional LinkedIn posts from **your** blog articles (recommended) or from AI web search + tech RSS feeds. **Blog mode** pulls posts from [abhisheksagarsanda.com](https://www.abhisheksagarsanda.com/blog) via the site’s Netlify API. News modes use **OpenAI web search** and/or RSS.

## Features

- **AI Web Search**: Uses OpenAI's web search to find the latest AI/ML news in real-time
- **Smart Post Generation**: GPT-4 creates engaging, personalized LinkedIn posts
- **Modern Web UI**: Beautiful, responsive interface with dark mode, topic selection, and inline editing
- **News Value Scoring**: Automatically scores and ranks articles by impact and relevance
- **Profile Integration**: Incorporates your skills, experience, and expertise into posts
- **Topic Customization**: Select specific AI topics to search for from the UI
- **Post Editing**: Edit generated posts directly in the browser before posting
- **One-Click Publishing**: Post directly to LinkedIn from the web interface
- **Multi-Article Mode**: Combine multiple articles into storytelling posts
- **Dry-Run Mode**: Preview posts without publishing

## Quick Start

### 1. Install Dependencies

```bash
cd LinkedIn
pip install -r requirements.txt
```

### 2. Configure

Copy the example config and fill in your API keys:

```bash
cp config.example.yaml config.yaml
```

You need:
- **OpenAI API Key** — powers both news search and post generation
- **LinkedIn Access Token** — for publishing posts

### 3. Run the Web UI

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

### 4. Generate Posts

1. Select topics you're interested in (OpenAI, NVIDIA, Google AI, etc.)
2. Choose how many posts to generate
3. Click **Generate Posts**
4. Review, edit, and post to LinkedIn

## CLI Usage

```bash
# Generate and post
python agent.py

# Preview without posting
python agent.py --dry-run

# Preview multiple posts
python agent.py --preview 3

# Custom config file
python agent.py --config my_config.yaml
```

## Configuration

### Required API Keys

| Key | Purpose | Get it from |
|-----|---------|-------------|
| `OPENAI_API_KEY` | News search + post generation | [OpenAI Platform](https://platform.openai.com/) |
| `LINKEDIN_ACCESS_TOKEN` | Publishing to LinkedIn | [LinkedIn Developers](https://www.linkedin.com/developers/apps) |

### Environment Variables

You can set these instead of using `config.yaml`:

```bash
export OPENAI_API_KEY="sk-..."
export LINKEDIN_ACCESS_TOKEN="..."
export PROFILE_NAME="Your Name"
export PROFILE_TITLE="AI/ML Engineer"
export SEARCH_MODEL="gpt-4o-mini"
```

### Config File

```yaml
profile:
  name: "Your Name"
  title: "AI/ML Engineer"
  skills: ["Machine Learning", "Python", "LLMs"]
  experience_years: 5

news:
  search_model: "gpt-4o-mini"    # Model for web search
  topics:                          # Default search topics
    - "OpenAI"
    - "NVIDIA"
    - "Google AI"
    - "Anthropic"

post_generation:
  ai_model: "gpt-4"               # Model for writing posts
  openai_api_key: "YOUR_KEY"
  include_hashtags: true

linkedin:
  access_token: "YOUR_TOKEN"
```

## How It Works

**Blog mode (`news.fetch_method: blog`):**

1. Fetches your latest posts from your site’s blog API (`/.netlify/functions/blog-list`)
2. **Post generation**: GPT creates a LinkedIn post using the article + your **profile** (resume-style fields in `config.yaml`)
3. **Review & edit** in the web UI, then **publish** to LinkedIn

**News modes (`ai`, `scraping`, or `both`):**

1. OpenAI web search and/or RSS feeds → article pool
2. Optional **value scoring** (0–110) to pick the best articles
3. Post generation → LinkedIn

## Architecture (blog mode)

```
Blog API (Netlify) → Your articles → Post generation (OpenAI) → LinkedIn API
                                              ↑
                                    Profile / resume context
```

## Deployment

### Production server

The **Procfile** uses **Gunicorn** (see `requirements.txt`). For local development, use:

```bash
python app.py
```

### Railway / Render / Fly.io

1. Set the service **root directory** to **`LinkedIn`** (this repo nests the app one level down).
2. See **`DEPLOY.md`** for the full checklist, health endpoint (`GET /health`), and environment variables.

### Environment variables (production)

Minimum:

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Post generation |
| `LINKEDIN_ACCESS_TOKEN` | Publishing |
| `NEWS_FETCH_METHOD` | Use `blog` for your blog posts |
| `PORT` | Set automatically on most hosts |

Optional profile/blog overrides: `PROFILE_NAME`, `PROFILE_TITLE`, `PROFILE_SUMMARY`, `BLOG_URL`, `BLOG_LINKEDIN_URL`, `BLOG_HASHTAGS`, etc. See `DEPLOY.md`.

## Troubleshooting

### OpenAI API
- **No results**: Ensure your OpenAI account has access to web search models
- **Rate limits**: Switch `search_model` to `gpt-4o-mini` for lower cost
- **API key issues**: Verify key at [platform.openai.com](https://platform.openai.com/)

### LinkedIn API
- **401 Unauthorized**: Access token expired — regenerate it
- **403 Forbidden**: App needs `w_member_social` permission
- **429 Too Many Requests**: Add delays between posts

## Security

- Never commit `config.yaml` with real credentials
- Use environment variables in production
- Rotate API keys regularly

## License

MIT License

## Disclaimer

This tool is for educational and personal use. Ensure you comply with LinkedIn's Terms of Service, OpenAI's Usage Policies, and local regulations regarding automated social media posting.
