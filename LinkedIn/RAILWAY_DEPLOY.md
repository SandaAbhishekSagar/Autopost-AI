# Deploying to Railway

This guide will help you deploy the LinkedIn AI/ML Auto-Poster to Railway.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. Your `config.yaml` file with all API keys configured
3. GitHub account (recommended for easy deployment)

## Step 1: Prepare Your Repository

Make sure your repository has:
- ✅ `app.py` (Flask application)
- ✅ `requirements.txt` (Python dependencies)
- ✅ `Procfile` (Railway deployment config)
- ✅ `railway.json` (Railway configuration)
- ✅ All your Python modules (`agent.py`, `post_generator.py`, etc.)
- ✅ `templates/index.html` (Web UI)

**Important**: Your `config.yaml` should NOT be committed to Git (it's in `.gitignore`). You'll add it as environment variables in Railway.

## Step 2: Deploy to Railway

### Option A: Deploy from GitHub (Recommended)

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Connect to Railway**:
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will automatically detect it's a Python app

3. **Configure Environment Variables**:
   - In Railway dashboard, go to your project
   - Click on "Variables" tab
   - Add the following variables (extract from your `config.yaml`):

   **LinkedIn API:**
   ```
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_client_secret
   LINKEDIN_ACCESS_TOKEN=your_access_token
   ```

   **OpenAI API:**
   ```
   OPENAI_API_KEY=your_openai_key
   ```

   **Profile Info (optional, can keep in config.yaml if you prefer):**
   ```
   PROFILE_NAME=Abhishek Sagar Sanda
   PROFILE_TITLE=AI/ML Engineer | Research Software Engineer | Teaching Assistant
   ```

### Option B: Deploy from Local Directory

1. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Initialize Project**:
   ```bash
   railway init
   ```

4. **Set Environment Variables**:
   ```bash
   railway variables set LINKEDIN_CLIENT_ID=your_client_id
   railway variables set LINKEDIN_CLIENT_SECRET=your_client_secret
   railway variables set LINKEDIN_ACCESS_TOKEN=your_access_token
   railway variables set OPENAI_API_KEY=your_openai_key
   ```

5. **Deploy**:
   ```bash
   railway up
   ```

## Step 3: Update app.py for Environment Variables (Optional)

If you want to use environment variables instead of `config.yaml`, you can update `app.py` to read from environment variables. However, the current setup will work if you upload your `config.yaml` file.

**Alternative**: Create `config.yaml` in Railway:
- Use Railway's file system or
- Create it via environment variables and have the app generate it

## Step 4: Access Your App

Once deployed:
1. Railway will provide you with a URL (e.g., `https://your-app.railway.app`)
2. Open the URL in your browser
3. Your LinkedIn Auto-Poster UI should be live!

## Step 5: Configure Custom Domain (Optional)

1. In Railway dashboard, go to "Settings"
2. Click "Generate Domain" or add your custom domain
3. Update DNS settings if using custom domain

## Environment Variables Reference

Here are all the environment variables you might need:

```bash
# LinkedIn API
LINKEDIN_CLIENT_ID=789qxqg2h2x3d2
LINKEDIN_CLIENT_SECRET=your_secret
LINKEDIN_ACCESS_TOKEN=your_token

# OpenAI API
OPENAI_API_KEY=your_openai_key

# Flask (optional)
FLASK_DEBUG=False
PORT=5000  # Railway sets this automatically
```

## Troubleshooting

### App Not Starting
- Check Railway logs: `railway logs` or view in dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` includes all dependencies

### Config File Not Found
- Make sure `config.yaml` is in the root directory
- Or use environment variables instead

### Port Issues
- Railway automatically sets the `PORT` environment variable
- The app is configured to use `PORT` from environment

### API Errors
- Verify your API keys are correct in Railway environment variables
- Check that LinkedIn access token hasn't expired
- Review logs for specific error messages

## Updating Your Deployment

After making changes:
1. Push to GitHub (if using GitHub deployment)
2. Railway will automatically redeploy
3. Or run `railway up` if using CLI

## Security Notes

- ✅ Never commit `config.yaml` to Git (it's in `.gitignore`)
- ✅ Use Railway's environment variables for sensitive data
- ✅ Keep your API keys secure
- ✅ Regularly rotate access tokens

## Cost

Railway offers:
- Free tier with $5 credit/month
- Pay-as-you-go pricing
- Very affordable for this type of application

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

Happy deploying! 🚀

