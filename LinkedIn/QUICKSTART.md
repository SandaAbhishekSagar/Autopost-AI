# Quick Start Guide

Get your LinkedIn AI/ML Auto-Poster up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Up Configuration

1. Copy the example config:
   ```bash
   cp config.example.yaml config.yaml
   ```

2. Edit `config.yaml` and fill in:
   - Your profile information (name, title, skills, etc.)
   - OpenAI API key (get from https://platform.openai.com/)
   - LinkedIn API credentials (see `setup_linkedin_api.md`)

## Step 3: Test with Dry Run

Before posting to LinkedIn, test the agent:

```bash
python agent.py --dry-run
```

This will:
- Fetch latest AI/ML news
- Generate a personalized post
- Show you the post **without** posting to LinkedIn

## Step 4: Preview Multiple Posts

See what posts would look like for different articles:

```bash
python agent.py --preview 3
```

## Step 5: Post to LinkedIn

Once you're happy with the generated posts:

```bash
python agent.py
```

## Step 6: Schedule Automatic Posting (Optional)

Run the scheduler to automatically post on a schedule:

```bash
python scheduler.py
```

Or run once immediately:

```bash
python scheduler.py --once
```

## Troubleshooting

### "OpenAI API key is required"
- Make sure you've added your OpenAI API key to `config.yaml`
- Get your key from: https://platform.openai.com/api-keys

### "LinkedIn access token is required"
- Follow the instructions in `setup_linkedin_api.md`
- You need to create a LinkedIn Developer app and get an access token

### "No articles found"
- Check your internet connection
- Verify RSS feeds are accessible
- Adjust keywords in `config.yaml` if they're too restrictive

### LinkedIn API Errors
- Make sure your access token is valid
- Check that your LinkedIn app has the required permissions
- See `setup_linkedin_api.md` for detailed setup instructions

## Next Steps

- Customize your profile in `config.yaml` to better reflect your expertise
- Adjust the post tone and style to match your personal brand
- Set up scheduling for automatic daily/weekly posts
- Monitor your posts and adjust keywords/content filters as needed

## Need Help?

- Check `README.md` for detailed documentation
- See `setup_linkedin_api.md` for LinkedIn API setup
- Review the configuration options in `config.yaml`

Happy posting! 🚀

