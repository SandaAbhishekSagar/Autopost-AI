"""
LinkedIn API Integration Module
Handles posting to LinkedIn using the LinkedIn API
"""

import requests
import logging
from typing import Dict, Optional
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInPoster:
    def __init__(self, config: Dict):
        self.config = config
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.access_token = config.get('access_token')
        self.base_url = "https://api.linkedin.com/v2"
        
        if not self.access_token:
            raise ValueError("LinkedIn access token is required in config.yaml")

    def get_user_profile(self) -> Optional[Dict]:
        """Get the authenticated user's profile"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get user's URN (Universal Resource Name)
            response = requests.get(
                f"{self.base_url}/userinfo",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None

    def post_to_linkedin(self, post_content: str, article_url: Optional[str] = None) -> bool:
        """
        Post content to LinkedIn
        
        Args:
            post_content: The text content of the post
            article_url: Optional URL to include in the post
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Try UGC Posts API first (for Community Management API)
        # Fall back to Share API (for Share on LinkedIn product)
        try:
            # First, get the user's URN
            person_urn = self._get_person_urn()
            if not person_urn:
                logger.error("Could not get person URN")
                return False
            
            # Try Share API first (works with "Share on LinkedIn" product - most common)
            # This is what most users will have enabled
            success = self._post_using_share_api(post_content, article_url)
            if success:
                return True
            
            # Fall back to UGC Posts API (requires Community Management API - more features)
            logger.info("Share API failed, trying UGC Posts API...")
            return self._post_using_ugc_api(post_content, article_url, person_urn)
                
        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {e}")
            return False

    def _post_using_ugc_api(self, post_content: str, article_url: Optional[str], person_urn: str) -> bool:
        """Post using UGC Posts API (requires Community Management API)"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            # Build the post payload
            payload = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": post_content
                        },
                        "shareMediaCategory": "ARTICLE" if article_url else "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Add article URL if provided
            if article_url:
                payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {
                        "status": "READY",
                        "description": {
                            "text": "Read the full article"
                        },
                        "originalUrl": article_url,
                        "title": {
                            "text": "AI/ML News Article"
                        }
                    }
                ]
            
            response = requests.post(
                f"{self.base_url}/ugcPosts",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info("Successfully posted to LinkedIn using UGC API!")
                return True
            else:
                logger.warning(f"UGC API failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.warning(f"UGC API error: {e}")
            return False

    def _post_using_share_api(self, post_content: str, article_url: Optional[str]) -> bool:
        """Post using Share API (works with 'Share on LinkedIn' product)"""
        try:
            # Get person URN for Share API
            person_urn = self._get_person_urn()
            if not person_urn:
                return False
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            # Build share payload (simpler format)
            payload = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": post_content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # For Share API, if we have a URL, append it to the text
            if article_url:
                post_content_with_url = f"{post_content}\n\n{article_url}"
                payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareCommentary"]["text"] = post_content_with_url
            
            response = requests.post(
                f"{self.base_url}/ugcPosts",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info("Successfully posted to LinkedIn using Share API!")
                return True
            else:
                logger.error(f"Failed to post to LinkedIn: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Share API error: {e}")
            return False

    def _get_person_urn(self) -> Optional[str]:
        """Get the person URN for the authenticated user"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get user info to extract person ID
            response = requests.get(
                f"{self.base_url}/userinfo",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            user_info = response.json()
            
            # Extract sub (user ID) and construct URN
            sub = user_info.get('sub')
            if sub:
                # URN format: urn:li:person:{id}
                return f"urn:li:person:{sub}"
            
            # Alternative: Try to get from /me endpoint
            response = requests.get(
                f"{self.base_url}/me",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                id_val = data.get('id')
                if id_val:
                    return f"urn:li:person:{id_val}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting person URN: {e}")
            return None

    def refresh_access_token(self) -> Optional[str]:
        """
        Refresh the access token if needed
        Note: This requires implementing OAuth flow
        """
        # This would require implementing the full OAuth 2.0 flow
        # For now, users need to manually refresh tokens
        logger.warning("Token refresh not implemented. Please manually update access_token in config.yaml")
        return None

