# AutoPost AI - LinkedIn Content Generator

An intelligent agent that automatically searches the web for the latest AI technology news and generates professional LinkedIn posts. Powered by **OpenAI's web search** — no RSS feeds, no API keys for news services, no web scraping.

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

1. **AI Web Search**: OpenAI's web search finds the latest AI news from across the internet
2. **Value Scoring**: Articles are scored by impact, relevance, and recency (0-110 scale)
3. **Post Generation**: GPT-4 creates a professional LinkedIn post incorporating the news and your profile
4. **Review & Edit**: Preview the post in the web UI, edit if needed
5. **Publish**: One-click posting to LinkedIn

## Architecture

```
OpenAI Web Search → News Articles → Value Scoring → Post Generation → LinkedIn API
                                                          ↑
                                                    Your Profile Info
```

No traditional scraping, RSS parsing, or third-party news APIs needed. OpenAI handles the web search, making the system simpler and more reliable.

## Deployment

### Railway

The app is configured for Railway deployment:

```bash
# Uses Procfile: web: python3 app.py
# Set environment variables in Railway dashboard
```

### Environment Variables for Production

Set these in your deployment platform:
- `OPENAI_API_KEY`
- `LINKEDIN_ACCESS_TOKEN`
- `PORT` (usually auto-set)
- `PROFILE_NAME`, `PROFILE_TITLE`, `PROFILE_SKILLS`

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
