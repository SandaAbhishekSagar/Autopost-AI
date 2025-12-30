# LinkedIn API Setup Guide

This guide will help you set up the LinkedIn API credentials needed for the auto-poster agent.

## Step 1: Create a LinkedIn Developer App

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Click "Create app"
3. Fill in the required information:
   - **App name**: Choose a name (e.g., "AI/ML Auto-Poster")
   - **LinkedIn Page**: Select your LinkedIn page or create one
   - **Privacy Policy URL**: You can use a placeholder for testing
   - **App logo**: Optional
4. Accept the terms and create the app

## Step 2: Request Required Permissions

Based on your current setup, you already have:
- ✅ **Sign In with LinkedIn using OpenID Connect** (enabled)
- ✅ **Share on LinkedIn** (enabled - perfect!)

**Great news!** You already have **"Share on LinkedIn"** enabled, which is exactly what you need for posting! 🎉

**What "Share on LinkedIn" gives you:**
- Post text updates to your LinkedIn feed
- Share articles with previews
- Description: "Amplify your content by sharing it on LinkedIn"
- Tier: Default Tier

**Optional - Community Management API:**
- You can also request **"Community Management API"** for more advanced features (UGC Posts API)
- It's in the "Available products" section with a "Request access" button
- However, **"Share on LinkedIn" is sufficient** for the agent to work
- The code will automatically use the Share API which works with your enabled "Share on LinkedIn" product

**You're all set!** ✅ No need to request additional products - you can start using the agent right away.

## Step 3: Get Your Credentials

1. Go to the **"Auth"** tab in your app dashboard
2. You'll find:
   - **Client ID**: `789qxqg2h2x3d2` (copy this to `config.yaml` as `client_id`)
   - **Client Secret**: Click "Show" to reveal it, then copy to `config.yaml` as `client_secret`

## Step 4: Generate an Access Token

### Option A: Using Developer Token (Easiest for Testing)

For quick testing, use a developer token:

1. In your app dashboard, go to the **"Auth"** tab
2. Scroll down to the **"Developer tokens"** section
3. Click **"Generate token"**
4. Copy the generated token to `config.yaml` as `access_token`

**Note**: 
- Developer tokens are only valid for your own account
- They typically expire after 60 days
- Perfect for testing and development

### Option B: Using OAuth 2.0 (Recommended for Production)

For production use, implement the full OAuth 2.0 flow:

**Step 1: Register Redirect URI**
1. In the **"Auth"** tab, scroll to **"Authorized redirect URLs for your app"**
2. Click **"+ Add redirect URL"**
3. Add: `http://localhost:8000/callback`
4. Click **"Update"**

**Step 2: Run OAuth Helper**
Use the provided OAuth helper script (much easier!):

```bash
python oauth_helper.py
```

This will:
- Open your browser for authentication
- Handle the callback automatically
- Exchange the code for an access token
- Save the token to your `config.yaml`

**Manual OAuth Flow (if script doesn't work):**
1. Visit the authorization URL:
   ```
   https://www.linkedin.com/oauth/v2/authorization?
     response_type=code&
     client_id=789qxqg2h2x3d2&
     redirect_uri=http://localhost:8000/callback&
     scope=w_member_social%20r_liteprofile%20openid%20profile
   ```
2. After authorization, extract the code from the callback URL
3. Exchange the code for an access token (see `OAUTH_TROUBLESHOOTING.md` for details)

**Troubleshooting OAuth Errors:**
- See `OAUTH_TROUBLESHOOTING.md` for common errors and solutions
- Most common issue: redirect URI mismatch - make sure it's registered exactly as `http://localhost:8000/callback`

**For now, start with Option A (Developer Token) to test quickly!**

## Step 5: Test Your Setup

Run the agent in dry-run mode first:

```bash
python agent.py --dry-run
```

If you see errors about authentication, verify:
- Your Client ID and Secret are correct
- Your access token is valid
- Your app has the required permissions approved

## Common Issues

### "Invalid access token"
- Your token may have expired. Generate a new one.
- Make sure you're using the correct token format.

### "Insufficient permissions"
- Your app may not have been approved for the required permissions yet.
- Check the "Products" section in your app dashboard.

### "Rate limit exceeded"
- LinkedIn has rate limits. Wait before trying again.
- Consider adding delays between posts.

## Production Considerations

For production use:

1. **Implement OAuth 2.0 Flow**: Don't hardcode access tokens
2. **Token Refresh**: Implement automatic token refresh
3. **Error Handling**: Add robust error handling for API failures
4. **Rate Limiting**: Respect LinkedIn's rate limits
5. **Monitoring**: Add logging and monitoring for failed posts

## Additional Resources

- [LinkedIn API Documentation](https://docs.microsoft.com/en-us/linkedin/)
- [LinkedIn UGC Posts API](https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/ugc-post-api)
- [OAuth 2.0 Guide](https://docs.microsoft.com/en-us/linkedin/shared/authentication/authentication)

