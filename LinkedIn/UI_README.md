# LinkedIn Auto-Poster Web UI

A beautiful, easy-to-use web interface for generating, reviewing, and posting LinkedIn content.

## Features

- 🎨 **Modern UI**: Clean, responsive design with gradient styling
- ✨ **One-Click Generation**: Generate posts with a single click
- 👀 **Preview Before Posting**: Review posts before publishing
- 📋 **Copy to Clipboard**: Easy copying for manual posting
- ✅ **Status Indicators**: See if your APIs are configured correctly
- 🚀 **Direct Posting**: Post directly to LinkedIn from the UI

## How to Use

### 1. Start the Web Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 2. Open in Browser

Open your browser and navigate to:
```
http://localhost:5000
```

### 3. Generate Posts

1. Select how many posts you want to generate (1-3)
2. Click **"Generate Post"** button
3. Review the generated posts

### 4. Post to LinkedIn

1. Review the generated post
2. Click **"Post to LinkedIn"** button
3. Confirm the action
4. Your post will be published!

### 5. Copy for Manual Posting

If you prefer to post manually:
1. Click **"Copy Text"** button
2. Paste into LinkedIn manually

## UI Features

- **Status Indicators**: Green/red dots show if OpenAI and LinkedIn APIs are configured
- **Article Information**: See the source article title, source, and link
- **Post Preview**: Full post content displayed in a scrollable area
- **Loading States**: Visual feedback during generation
- **Error Handling**: Clear error messages if something goes wrong

## Troubleshooting

### UI Not Loading
- Make sure Flask is installed: `pip install flask`
- Check that port 5000 is not in use
- Look at the terminal for error messages

### Posts Not Generating
- Check that your `config.yaml` has valid OpenAI API key
- Verify your internet connection
- Check the browser console for errors (F12)

### Can't Post to LinkedIn
- Verify your LinkedIn access token is valid
- Check that "Share on LinkedIn" product is enabled
- Look at the terminal logs for detailed error messages

## Stopping the Server

Press `Ctrl+C` in the terminal to stop the web server.

