# OAuth 2.0 Troubleshooting Guide

If you're getting errors with the OAuth callback, follow these steps:

## Common Error: "redirect_uri_mismatch"

This means the redirect URI you're using doesn't match what's registered in your LinkedIn app.

### Fix Steps:

1. **Go to LinkedIn Developer Portal:**
   - Visit: https://www.linkedin.com/developers/apps
   - Select your app: "AI/MI auto post"
   - Go to the **"Auth"** tab

2. **Add Redirect URI:**
   - Scroll down to **"Authorized redirect URLs for your app"**
   - Click **"+ Add redirect URL"**
   - Add: `http://localhost:8000/callback`
   - Click **"Update"**
   - **Important:** You may need to verify your app first (LinkedIn will prompt you)

3. **Verify the Redirect URI:**
   - Make sure it matches EXACTLY (including http vs https, trailing slashes, etc.)
   - Common formats:
     - ✅ `http://localhost:8000/callback`
     - ✅ `https://localhost:8000/callback`
     - ❌ `http://localhost:8000/callback/` (trailing slash)
     - ❌ `http://127.0.0.1:8000/callback` (different host)

## Using the OAuth Helper Script

I've created an OAuth helper script that handles the full flow:

```bash
python oauth_helper.py
```

This will:
1. Open your browser for authentication
2. Start a local server to receive the callback
3. Exchange the code for an access token
4. Save the token to your `config.yaml`

### Requirements:

Make sure you have the redirect URI registered first (see steps above).

## Alternative: Use Developer Token (Easier for Testing)

If OAuth is giving you trouble, you can use a Developer Token instead:

1. Go to LinkedIn Developer Portal → Your App → **"Auth"** tab
2. Scroll to **"Developer tokens"** section
3. Click **"Generate token"**
4. Copy the token to `config.yaml` as `access_token`

**Note:** Developer tokens expire after ~60 days, but they're much easier for testing!

## Common Errors and Solutions

### Error: "invalid_client"
- **Cause:** Client ID or Secret is incorrect
- **Fix:** Check your `config.yaml` - make sure Client ID and Secret are correct

### Error: "invalid_grant"
- **Cause:** Authorization code has expired or was already used
- **Fix:** Run the OAuth flow again (codes expire quickly)

### Error: "insufficient_scope"
- **Cause:** Your app doesn't have the required permissions
- **Fix:** Make sure "Share on LinkedIn" is enabled in Products tab

### Error: "redirect_uri_mismatch"
- **Cause:** Redirect URI doesn't match registered URI
- **Fix:** See steps above to add/verify redirect URI

### Error: Connection refused / Can't connect to localhost:8000
- **Cause:** Port 8000 might be in use or firewall blocking
- **Fix:** 
  - Try a different port: `python oauth_helper.py --redirect-uri http://localhost:8001/callback`
  - Make sure nothing else is using port 8000
  - Check firewall settings

## Manual OAuth Flow (If Script Doesn't Work)

1. **Get Authorization URL:**
   ```
   https://www.linkedin.com/oauth/v2/authorization?
     response_type=code&
     client_id=789qxqg2h2x3d2&
     redirect_uri=http://localhost:8000/callback&
     scope=w_member_social%20r_liteprofile%20openid%20profile
   ```

2. **Visit the URL** in your browser and authorize

3. **After authorization**, LinkedIn will redirect to your callback URL with a `code` parameter

4. **Extract the code** from the URL (it will look like: `http://localhost:8000/callback?code=AQT...`)

5. **Exchange code for token** using:
   ```bash
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -d "grant_type=authorization_code" \
     -d "code=YOUR_CODE_HERE" \
     -d "redirect_uri=http://localhost:8000/callback" \
     -d "client_id=789qxqg2h2x3d2" \
     -d "client_secret=YOUR_CLIENT_SECRET"
   ```

## Still Having Issues?

1. **Check LinkedIn App Status:**
   - Make sure your app is not in "Development" mode restrictions
   - Some features require app verification

2. **Verify Products:**
   - Go to "Products" tab
   - Make sure "Share on LinkedIn" is enabled

3. **Check Scopes:**
   - Required scopes: `w_member_social`, `r_liteprofile`, `openid`, `profile`
   - Make sure these are requested in the authorization URL

4. **Use Developer Token Instead:**
   - Much simpler for testing
   - No OAuth flow needed
   - Just generate in the Auth tab

## Quick Test

After setting up, test with:
```bash
python agent.py --dry-run
```

If you see authentication errors, double-check your access token in `config.yaml`.

