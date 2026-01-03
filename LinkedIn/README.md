# LinkedIn AI/ML Auto-Poster Agent

An intelligent agent that automatically creates and posts LinkedIn content about the latest AI/ML news from major tech giants (OpenAI, NVIDIA, Google, Microsoft, Meta, Apple, Amazon, Anthropic, etc.), personalized to highlight your profile, skills, and expertise.

## Features

- 🤖 **AI-Powered Post Generation**: Uses GPT-4/GPT-3.5 to create engaging, personalized LinkedIn posts
- 📰 **Multi-Source News Fetching**: Aggregates AI/ML news from RSS feeds and NewsAPI, with focus on tech giants
- 🎯 **Smart Filtering**: Only posts relevant articles from OpenAI, NVIDIA, Google, Microsoft, Meta, and other major tech companies
- 🏢 **Tech Giants Focus**: Specifically targets news from OpenAI, NVIDIA, Google, Microsoft, Meta, Apple, Amazon, Anthropic, and other major AI companies
- 👤 **Profile Integration**: Automatically incorporates your skills, experience, and expertise into posts
- ⏰ **Scheduling Support**: Can be scheduled to run automatically
- 🔒 **Safe Testing**: Dry-run mode to preview posts before posting

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your Profile

Edit `config.yaml` and fill in:

- **Your Profile Information**: Name, title, skills, experience, expertise areas
- **LinkedIn API Credentials**: Client ID, Client Secret, and Access Token
- **OpenAI API Key**: For post generation
- **Post Preferences**: Tone, hashtags, posting schedule

### 3. Get LinkedIn API Credentials

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Create a new app or use an existing one
3. Request the following permissions:
   - `w_member_social` (to post on behalf of users)
   - `r_liteprofile` (to read profile)
4. Get your Client ID and Client Secret
5. Generate an Access Token (or implement OAuth flow for production)

**Note**: LinkedIn API access requires approval for certain permissions. For testing, you can use a personal access token.

### 4. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Add it to `config.yaml`

### 5. (Optional) Get NewsAPI Key

If you want to use NewsAPI for additional news sources:

1. Go to [NewsAPI.org](https://newsapi.org/)
2. Sign up for a free account
3. Get your API key
4. Add it to `config.yaml` and set `use_news_api: true`

## Usage

### Basic Usage

Run the agent to fetch news and post to LinkedIn:

```bash
python agent.py
```

### Preview Posts (Dry Run)

Test the agent without posting to LinkedIn:

```bash
python agent.py --dry-run
```

### Preview Multiple Posts

Generate and preview multiple posts:

```bash
python agent.py --preview 3
```

### Custom Config File

Use a different configuration file:

```bash
python agent.py --config my_config.yaml
```

## Configuration

### Profile Section

Customize your profile information that will be incorporated into posts:

```yaml
profile:
  name: "Your Name"
  title: "AI/ML Engineer | Data Scientist"
  skills:
    - "Machine Learning"
    - "Deep Learning"
  experience_years: 5
  expertise_areas:
    - "Neural Networks"
    - "LLMs"
```

### News Sources

Configure which news sources to use:

```yaml
news:
  rss_feeds:
    - "https://techcrunch.com/feed/"
  use_news_api: true
  news_api_key: "YOUR_KEY"
```

### Post Generation

Customize how posts are generated:

```yaml
post_generation:
  ai_model: "gpt-4"  # or "gpt-3.5-turbo"
  tone: "professional"  # professional, engaging, technical
  include_hashtags: true
  hashtags:
    - "#AI"
    - "#MachineLearning"
```

## Scheduling

### Manual Scheduling

Use cron (Linux/Mac) or Task Scheduler (Windows) to run the agent automatically:

```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/project && python agent.py
```

### Python Scheduling (Coming Soon)

The agent can be extended to use the `schedule` library for automatic posting.

## How It Works

1. **News Fetching**: The agent fetches latest AI/ML news from configured RSS feeds and/or NewsAPI
2. **Content Filtering**: Articles are filtered based on keywords, age, and relevance
3. **Post Generation**: GPT-4/GPT-3.5 generates a personalized LinkedIn post incorporating:
   - The news article content
   - Your profile information
   - Your skills and expertise
   - Professional insights
4. **Posting**: The generated post is published to your LinkedIn feed

## Example Output

```
🤖 Exciting development in AI/ML: [Article Title]

[AI-generated summary and insights]

As someone with 5+ years of experience in Machine Learning and Deep Learning, 
I find this particularly interesting because [personalized connection to your expertise].

What are your thoughts on this? Let's discuss in the comments!

#AI #MachineLearning #ArtificialIntelligence #TechNews #Innovation
```

## Troubleshooting

### LinkedIn API Errors

- **401 Unauthorized**: Your access token may have expired. Refresh it in the LinkedIn Developer portal.
- **403 Forbidden**: Check that your app has the required permissions approved.
- **429 Too Many Requests**: You're posting too frequently. Add delays between posts.

### OpenAI API Errors

- **Rate Limits**: If you hit rate limits, switch to `gpt-3.5-turbo` or add delays.
- **API Key Issues**: Verify your API key is correct and has sufficient credits.

### News Fetching Issues

- **No Articles Found**: Adjust your keywords or expand your news sources.
- **RSS Feed Errors**: Some feeds may be temporarily unavailable. The agent will skip them.

## Security Notes

- **Never commit `config.yaml` with real credentials** to version control
- Add `config.yaml` to `.gitignore`
- Use environment variables for sensitive data in production
- Regularly rotate API keys and access tokens

## License

MIT License - Feel free to use and modify for your needs.

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## Disclaimer

This tool is for educational and personal use. Ensure you comply with:
- LinkedIn's Terms of Service
- OpenAI's Usage Policies
- News sources' terms of use
- Local regulations regarding automated social media posting

Use responsibly and maintain authenticity in your posts.

