"""
LinkedIn API Integration Module
Handles posting to LinkedIn with optional image attachment
"""

import requests
import logging
from typing import Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInPoster:
    def __init__(self, config: Dict):
        self.config = config
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.access_token = config.get('access_token')
        self.base_url = "https://api.linkedin.com/v2"
        self.rest_url = "https://api.linkedin.com/rest"

        if not self.access_token:
            raise ValueError("LinkedIn access token is required in config.yaml")

    def get_user_profile(self) -> Optional[Dict]:
        """Get the authenticated user's profile"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
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

    def post_to_linkedin(
        self,
        post_content: str,
        article_url: Optional[str] = None,
        image: Optional[Tuple[bytes, str]] = None
    ) -> bool:
        """
        Post content to LinkedIn, optionally with an image.

        Args:
            post_content: The text content of the post
            article_url: Optional URL to include in the post
            image: Optional (image_bytes, content_type) tuple for post image

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            person_urn = self._get_person_urn()
            if not person_urn:
                logger.error("Could not get person URN")
                return False

            # If we have an image, try to upload and post with image
            asset_urn = None
            if image:
                image_bytes, content_type = image
                asset_urn = self._upload_image(person_urn, image_bytes, content_type)
                if not asset_urn:
                    logger.warning("Image upload failed, posting without image")

            if asset_urn:
                success = self._post_with_image(post_content, article_url, person_urn, asset_urn)
            else:
                success = self._post_using_share_api(post_content, article_url)

            if success:
                return True

            logger.info("Share API failed, trying UGC Posts API...")
            return self._post_using_ugc_api(post_content, article_url, person_urn, asset_urn)

        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {e}")
            return False

    def _upload_image(
        self,
        person_urn: str,
        image_bytes: bytes,
        content_type: str
    ) -> Optional[str]:
        """Register upload, upload image, return asset URN"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0',
                'Linkedin-Version': '202502'
            }

            # Step 1: Register upload
            payload = {
                "registerUploadRequest": {
                    "owner": person_urn,
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "serviceRelationships": [
                        {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
                    ],
                    "supportedUploadMechanism": ["SYNCHRONOUS_UPLOAD"]
                }
            }

            resp = requests.post(
                f"{self.rest_url}/assets?action=registerUpload",
                headers=headers,
                json=payload,
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            value = data.get('value', {})
            upload_mechanism = value.get('uploadMechanism', {})
            upload_request = upload_mechanism.get('com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest', {})
            upload_url = upload_request.get('uploadUrl')
            asset_urn = value.get('asset')

            if not upload_url or not asset_urn:
                logger.error("Invalid registerUpload response")
                return None

            # Step 2: Upload image bytes
            upload_headers = {
                'Authorization': f'Bearer {self.access_token}',
            }
            if content_type:
                upload_headers['Content-Type'] = content_type

            put_resp = requests.put(upload_url, data=image_bytes, headers=upload_headers, timeout=30)
            put_resp.raise_for_status()

            logger.info(f"Image uploaded successfully: {asset_urn}")
            return asset_urn

        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return None

    def _post_with_image(
        self,
        post_content: str,
        article_url: Optional[str],
        person_urn: str,
        asset_urn: str
    ) -> bool:
        """Post with image using UGC Posts API"""
        try:
            if article_url:
                post_content = f"{post_content}\n\n{article_url}"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            payload = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": post_content},
                        "shareMediaCategory": "IMAGE",
                        "media": [
                            {
                                "status": "READY",
                                "media": asset_urn
                            }
                        ]
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }

            response = requests.post(
                f"{self.base_url}/ugcPosts",
                headers=headers,
                json=payload,
                timeout=15
            )

            if response.status_code in [200, 201]:
                logger.info("Successfully posted to LinkedIn with image!")
                return True
            logger.warning(f"UGC post with image failed: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"Post with image failed: {e}")
            return False

    def _post_using_ugc_api(
        self,
        post_content: str,
        article_url: Optional[str],
        person_urn: str,
        asset_urn: Optional[str] = None
    ) -> bool:
        """Post using UGC Posts API (ARTICLE or NONE, or IMAGE if asset_urn)"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            if asset_urn:
                if article_url:
                    post_content = f"{post_content}\n\n{article_url}"
                return self._post_with_image(post_content, article_url, person_urn, asset_urn)

            share_media = "ARTICLE" if article_url else "NONE"
            payload = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": post_content},
                        "shareMediaCategory": share_media
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }

            if article_url:
                payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {
                        "status": "READY",
                        "description": {"text": "Read the full article"},
                        "originalUrl": article_url,
                        "title": {"text": "AI/ML News Article"}
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
            logger.warning(f"UGC API failed: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.warning(f"UGC API error: {e}")
            return False

    def _post_using_share_api(
        self,
        post_content: str,
        article_url: Optional[str],
        asset_urn: Optional[str] = None
    ) -> bool:
        """Post using Share API (text only, or with article URL in text)"""
        try:
            person_urn = self._get_person_urn()
            if not person_urn:
                return False

            if asset_urn:
                return self._post_with_image(post_content, article_url, person_urn, asset_urn)

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            payload = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": post_content},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }

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
            logger.error(f"Failed to post: {response.status_code} - {response.text}")
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
            response = requests.get(
                f"{self.base_url}/userinfo",
                headers=headers,
                timeout=10
            )

            # 401 usually means your token is missing, expired, or does not match the app/scopes.
            if response.status_code == 401:
                logger.error(
                    "LinkedIn 401 Unauthorized from /v2/userinfo. "
                    "Your LINKEDIN_ACCESS_TOKEN is likely expired/invalid or lacks required scopes. "
                    "Make sure you generated a user access token with scopes: w_member_social openid profile."
                )
                logger.error(f"LinkedIn response body: {response.text[:500]}")
                return None
            if response.status_code == 403:
                logger.error(
                    "LinkedIn 403 Forbidden from /v2/userinfo. "
                    "Your token may be valid but missing permissions/scopes or the app is not approved."
                )
                logger.error(f"LinkedIn response body: {response.text[:500]}")
                return None

            response.raise_for_status()
            user_info = response.json()
            sub = user_info.get('sub')
            if sub:
                return f"urn:li:person:{sub}"
            response = requests.get(
                f"{self.base_url}/me",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                id_val = response.json().get('id')
                if id_val:
                    return f"urn:li:person:{id_val}"
            return None
        except Exception as e:
            logger.error(f"Error getting person URN: {e}")
            return None

    def refresh_access_token(self) -> Optional[str]:
        logger.warning("Token refresh not implemented. Update access_token in config.yaml")
        return None
