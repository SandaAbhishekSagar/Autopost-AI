"""
OAuth 2.0 Helper for LinkedIn Authentication
Handles the full OAuth flow to get an access token
"""

import requests
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import yaml
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    def do_GET(self):
        """Handle the OAuth callback"""
        # Parse the query string
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        
        if 'code' in query_params:
            code = query_params['code'][0]
            self.server.auth_code = code
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = """
            <html>
            <head><title>Authentication Success</title></head>
            <body>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <p>The access token will be saved automatically.</p>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
        elif 'error' in query_params:
            error = query_params['error'][0]
            error_description = query_params.get('error_description', ['Unknown error'])[0]
            self.server.auth_code = None
            self.server.auth_error = f"{error}: {error_description}"
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = f"""
            <html>
            <head><title>Authentication Error</title></head>
            <body>
                <h1>Authentication Failed</h1>
                <p>Error: {error}</p>
                <p>Description: {error_description}</p>
                <p>Please check your redirect URI settings in LinkedIn Developer portal.</p>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid request")
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


class LinkedInOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = "http://localhost:8000/callback"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        
    def get_authorization_url(self) -> str:
        """Generate the authorization URL"""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'w_member_social openid profile',  # Removed r_liteprofile (deprecated)
            'state': 'random_state_string'  # For security
        }
        
        url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"
        return url
    
    def exchange_code_for_token(self, code: str) -> Optional[dict]:
        """Exchange authorization code for access token"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(self.token_url, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            logger.error(f"Response: {response.text if 'response' in locals() else 'No response'}")
            return None
    
    def authenticate(self) -> Optional[str]:
        """Complete OAuth flow and return access token"""
        # Start local server for callback
        server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
        server.auth_code = None
        server.auth_error = None
        
        # Get authorization URL
        auth_url = self.get_authorization_url()
        logger.info(f"Opening browser for authentication...")
        logger.info(f"If browser doesn't open, visit: {auth_url}")
        
        # Open browser
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            logger.warning(f"Could not open browser automatically: {e}")
            logger.info(f"Please visit this URL manually: {auth_url}")
        
        # Wait for callback
        logger.info("Waiting for authentication...")
        logger.info("(Make sure you've added http://localhost:8000/callback to your LinkedIn app's redirect URIs)")
        
        server.timeout = 300  # 5 minutes timeout
        server.handle_request()
        
        if server.auth_error:
            logger.error(f"Authentication error: {server.auth_error}")
            return None
        
        if not server.auth_code:
            logger.error("No authorization code received")
            return None
        
        logger.info("Authorization code received, exchanging for access token...")
        
        # Exchange code for token
        token_data = self.exchange_code_for_token(server.auth_code)
        
        if token_data and 'access_token' in token_data:
            access_token = token_data['access_token']
            logger.info("✅ Successfully obtained access token!")
            logger.info(f"Token expires in: {token_data.get('expires_in', 'unknown')} seconds")
            return access_token
        else:
            logger.error("Failed to obtain access token")
            return None


def main():
    """Main function to run OAuth flow"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn OAuth 2.0 Authentication Helper')
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--redirect-uri',
        type=str,
        default='http://localhost:8000/callback',
        help='Redirect URI (must match LinkedIn app settings)'
    )
    
    args = parser.parse_args()
    
    # Load config
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return
    
    linkedin_config = config.get('linkedin', {})
    client_id = linkedin_config.get('client_id')
    client_secret = linkedin_config.get('client_secret')
    
    if not client_id or not client_secret:
        logger.error("Client ID and Client Secret are required in config.yaml")
        logger.info("Please add them to the 'linkedin' section of your config.yaml")
        return
    
    # Run OAuth flow
    oauth = LinkedInOAuth(client_id, client_secret, args.redirect_uri)
    access_token = oauth.authenticate()
    
    if access_token:
        # Update config with new token
        linkedin_config['access_token'] = access_token
        config['linkedin'] = linkedin_config
        
        # Save config
        try:
            with open(args.config, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"✅ Access token saved to {args.config}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            logger.info(f"Please manually add this to your config.yaml:")
            logger.info(f"  access_token: {access_token}")
    else:
        logger.error("Failed to obtain access token. Please check:")
        logger.error("1. Redirect URI is registered in LinkedIn app settings")
        logger.error("2. Client ID and Secret are correct")
        logger.error("3. Required permissions are approved")


if __name__ == "__main__":
    main()

