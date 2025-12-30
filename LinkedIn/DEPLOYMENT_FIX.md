# Railway Deployment Fix

## Issue
Railway's Railpack couldn't detect Python because it was looking in a `LinkedIn/` subdirectory.

## Solution

The files have been updated to help Railway detect Python properly:

1. **`runtime.txt`** - Specifies Python version
2. **`nixpacks.toml`** - Nixpacks configuration for Python
3. **`railway.toml`** - Railway configuration
4. **`Procfile`** - Process file for Railway

## If Files Are in a Subdirectory

If your repository structure has files in a `LinkedIn/` folder, you have two options:

### Option 1: Move Files to Root (Recommended)

Move all files from `LinkedIn/` to the repository root:

```bash
# If you're in the LinkedIn directory
cd ..
mv LinkedIn/* .
mv LinkedIn/.gitignore . 2>/dev/null || true
rmdir LinkedIn
```

### Option 2: Configure Railway Root Directory

In Railway dashboard:
1. Go to your project settings
2. Find "Root Directory" setting
3. Set it to `LinkedIn/`

## Verify Your Structure

Your repository root should have:
- ✅ `app.py`
- ✅ `requirements.txt`
- ✅ `Procfile`
- ✅ `runtime.txt`
- ✅ `agent.py`
- ✅ `post_generator.py`
- ✅ `linkedin_poster.py`
- ✅ `news_fetcher.py`
- ✅ `templates/index.html`
- ✅ All other Python files

## Redeploy

After fixing the structure:
1. Commit and push changes
2. Railway will automatically redeploy
3. Check the logs to verify it detects Python

## Alternative: Use Railway CLI

If web deployment doesn't work:

```bash
railway login
railway init
railway link
railway up
```

This will use the local files and deploy them correctly.

