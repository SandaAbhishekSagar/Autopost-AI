"""
Image Helper Module
Fetches or generates images for LinkedIn posts.
Tries article og:image first, falls back to DALL-E generation.
"""

import re
import logging
import requests
from typing import Optional, Tuple
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_image_for_post(
    article_url: Optional[str],
    article_title: str,
    post_content: str,
    openai_api_key: Optional[str] = None
) -> Optional[Tuple[bytes, str]]:
    """
    Get an image for a LinkedIn post. Tries article og:image first, then DALL-E.

    Args:
        article_url: URL of the source article (for og:image)
        article_title: Article title (for DALL-E prompt)
        post_content: Post text (for DALL-E context)
        openai_api_key: OpenAI API key for DALL-E fallback

    Returns:
        Tuple of (image_bytes, content_type) or None
    """
    # Strategy 1: Fetch og:image from article URL
    if article_url:
        img = _fetch_og_image(article_url)
        if img:
            return img

    # Strategy 2: Generate with DALL-E
    if openai_api_key:
        img = _generate_image_dalle(article_title, post_content, openai_api_key)
        if img:
            return img

    return None


def _fetch_og_image(url: str) -> Optional[Tuple[bytes, str]]:
    """Fetch Open Graph image from article URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; AutoPostAI/1.0; +https://github.com/autopost-ai)'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        html = resp.text

        # Extract og:image - common patterns
        patterns = [
            r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
            r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:image["\']',
            r'"og:image":\s*["\']([^"\']+)["\']',
        ]
        img_url = None
        for pat in patterns:
            m = re.search(pat, html, re.I)
            if m:
                img_url = m.group(1)
                break

        if not img_url:
            return None

        # Resolve relative URLs
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"

        # Download image
        img_resp = requests.get(img_url, headers=headers, timeout=15)
        img_resp.raise_for_status()
        content_type = img_resp.headers.get('Content-Type', 'image/jpeg')
        if ';' in content_type:
            content_type = content_type.split(';')[0].strip()

        # LinkedIn supports JPG, PNG, GIF
        if content_type not in ('image/jpeg', 'image/jpg', 'image/png', 'image/gif'):
            content_type = 'image/jpeg'

        logger.info(f"Fetched og:image from article ({len(img_resp.content)} bytes)")
        return (img_resp.content, content_type)

    except Exception as e:
        logger.debug(f"Could not fetch og:image from {url}: {e}")
        return None


def _generate_image_dalle(
    article_title: str,
    post_content: str,
    api_key: str
) -> Optional[Tuple[bytes, str]]:
    """Generate image using DALL-E based on post content"""
    try:
        client = OpenAI(api_key=api_key)
        # Use first ~200 chars of post for context
        context = (post_content[:200] + '...') if len(post_content) > 200 else post_content

        prompt = f"""Professional, modern image for a LinkedIn post about: {article_title}
Style: Clean tech/innovation visual, suitable for professional social media.
Avoid: Text overlays, logos, watermarks. Use abstract tech imagery, AI/innovation themes."""

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1
        )
        img_url = response.data[0].url
        if not img_url:
            return None

        img_resp = requests.get(img_url, timeout=30)
        img_resp.raise_for_status()
        logger.info(f"Generated image with DALL-E ({len(img_resp.content)} bytes)")
        return (img_resp.content, 'image/png')

    except Exception as e:
        logger.warning(f"DALL-E image generation failed: {e}")
        return None
