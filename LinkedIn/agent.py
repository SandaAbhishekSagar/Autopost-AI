"""
Main Agent Orchestrator
Coordinates news fetching, post generation, and LinkedIn posting
"""

import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
import sys
from news_fetcher import NewsFetcher
from post_generator import PostGenerator
from linkedin_poster import LinkedInPoster

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LinkedInAIAgent:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the agent with configuration"""
        self.config = self._load_config(config_path)
        self.news_fetcher = NewsFetcher(self.config.get('news', {}))
        self.post_generator = PostGenerator(self.config)
        self.linkedin_poster = LinkedInPoster(self.config.get('linkedin', {}))
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file or environment variables"""
        import os
        
        # If config file doesn't exist, try to create it from environment variables
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file {config_path} not found. Attempting to create from environment variables...")
            config = self._create_config_from_env()
            if config:
                # Save config to file for future use
                try:
                    with open(config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                    logger.info(f"Configuration created from environment variables and saved to {config_path}")
                except Exception as e:
                    logger.warning(f"Could not save config to file: {e}")
                return config
            else:
                logger.error(f"Configuration file {config_path} not found and could not create from environment variables!")
                logger.error("Please create config.yaml or set the required environment variables.")
                sys.exit(1)
        
        # Load from file
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def _create_config_from_env(self) -> Optional[Dict]:
        """Create configuration dictionary from environment variables"""
        import os
        
        config = {}
        
        # Profile information
        config['profile'] = {
            'name': os.environ.get('PROFILE_NAME', 'Your Name'),
            'title': os.environ.get('PROFILE_TITLE', 'AI/ML Engineer'),
            'skills': os.environ.get('PROFILE_SKILLS', 'Machine Learning,Deep Learning,Python').split(','),
            'experience_years': int(os.environ.get('PROFILE_EXPERIENCE_YEARS', '5')),
            'expertise_areas': os.environ.get('PROFILE_EXPERTISE', 'AI Research,MLOps').split(',')
        }
        
        # LinkedIn API credentials
        linkedin_client_id = os.environ.get('LINKEDIN_CLIENT_ID')
        linkedin_client_secret = os.environ.get('LINKEDIN_CLIENT_SECRET')
        linkedin_access_token = os.environ.get('LINKEDIN_ACCESS_TOKEN')
        
        if not linkedin_access_token:
            logger.warning("LINKEDIN_ACCESS_TOKEN not found in environment variables")
            return None
        
        config['linkedin'] = {
            'client_id': linkedin_client_id or '',
            'client_secret': linkedin_client_secret or '',
            'access_token': linkedin_access_token
        }
        
        # News sources
        config['news'] = {
            'sources': [
                'https://www.theverge.com/ai-artificial-intelligence',
                'https://techcrunch.com/tag/artificial-intelligence/',
                'https://venturebeat.com/ai/'
            ],
            'rss_feeds': [
                'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',
                'https://techcrunch.com/feed/'
            ],
            'use_news_api': os.environ.get('USE_NEWS_API', 'false').lower() == 'true',
            'news_api_key': os.environ.get('NEWS_API_KEY', '')
        }
        
        # Post generation settings
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            return None
        
        config['post_generation'] = {
            'ai_model': os.environ.get('OPENAI_MODEL', 'gpt-4'),
            'openai_api_key': openai_api_key,
            'tone': os.environ.get('POST_TONE', 'professional'),
            'max_post_length': int(os.environ.get('MAX_POST_LENGTH', '3000')),
            'include_hashtags': os.environ.get('INCLUDE_HASHTAGS', 'true').lower() == 'true',
            'hashtags': os.environ.get('HASHTAGS', '#AI,#MachineLearning,#ArtificialIntelligence,#TechNews').split(',')
        }
        
        # Schedule
        config['schedule'] = {
            'enabled': os.environ.get('SCHEDULE_ENABLED', 'true').lower() == 'true',
            'frequency': os.environ.get('SCHEDULE_FREQUENCY', 'daily'),
            'time': os.environ.get('SCHEDULE_TIME', '09:00'),
            'timezone': os.environ.get('SCHEDULE_TIMEZONE', 'UTC')
        }
        
        # Content filtering
        config['content'] = {
            'min_article_age_hours': int(os.environ.get('MIN_ARTICLE_AGE_HOURS', '0')),
            'max_article_age_hours': int(os.environ.get('MAX_ARTICLE_AGE_HOURS', '48')),
            'keywords_required': os.environ.get('KEYWORDS_REQUIRED', 'AI,machine learning,artificial intelligence').split(','),
            'keywords_excluded': os.environ.get('KEYWORDS_EXCLUDED', 'crypto,bitcoin').split(',')
        }
        
        return config

    def run(self, dry_run: bool = False) -> bool:
        """
        Main execution method
        
        Args:
            dry_run: If True, generate posts but don't post to LinkedIn
        
        Returns:
            bool: True if successful
        """
        logger.info("Starting LinkedIn AI/ML Auto-Poster Agent...")
        
        try:
            # Step 1: Fetch latest news
            logger.info("Fetching latest AI/ML news...")
            articles = self.news_fetcher.get_latest_news(limit=5)
            
            if not articles:
                logger.warning("No articles found matching criteria")
                return False
            
            logger.info(f"Found {len(articles)} relevant articles")
            
            # Step 2: Generate post for the most recent article
            article = articles[0]  # Get the most recent one
            logger.info(f"Generating post for: {article.get('title', 'Unknown')}")
            
            post_content = self.post_generator.generate_post(article)
            logger.info("Post generated successfully")
            
            # Display the post
            try:
                print("\n" + "="*80)
                print("GENERATED POST:")
                print("="*80)
                print(post_content)
                print("="*80 + "\n")
            except UnicodeEncodeError:
                # Handle Unicode encoding issues on Windows
                import io
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
                print("\n" + "="*80)
                print("GENERATED POST:")
                print("="*80)
                print(post_content)
                print("="*80 + "\n")
            
            # Step 3: Post to LinkedIn (unless dry run)
            if dry_run:
                logger.info("DRY RUN: Post not sent to LinkedIn")
                return True
            
            logger.info("Posting to LinkedIn...")
            success = self.linkedin_poster.post_to_linkedin(
                post_content=post_content,
                article_url=article.get('url')
            )
            
            if success:
                logger.info("✅ Successfully posted to LinkedIn!")
                return True
            else:
                logger.error("❌ Failed to post to LinkedIn")
                return False
                
        except Exception as e:
            logger.error(f"Error in agent execution: {e}", exc_info=True)
            return False

    def preview_posts(self, num_posts: int = 3) -> List[Dict]:
        """
        Preview multiple posts without posting
        
        Args:
            num_posts: Number of posts to preview
        
        Returns:
            List of dictionaries with article and post content
        """
        logger.info(f"Generating preview for {num_posts} posts...")
        
        articles = self.news_fetcher.get_latest_news(limit=num_posts)
        previews = []
        
        for article in articles:
            post_content = self.post_generator.generate_post(article)
            previews.append({
                'article': article,
                'post': post_content
            })
        
        return previews


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn AI/ML Auto-Poster Agent')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate posts without posting to LinkedIn'
    )
    parser.add_argument(
        '--preview',
        type=int,
        metavar='N',
        help='Preview N posts without posting'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    agent = LinkedInAIAgent(config_path=args.config)
    
    if args.preview:
        previews = agent.preview_posts(num_posts=args.preview)
        for i, preview in enumerate(previews, 1):
            try:
                print(f"\n{'='*80}")
                print(f"PREVIEW {i}/{len(previews)}")
                print(f"{'='*80}")
                print(f"Article: {preview['article'].get('title', 'Unknown')}")
                print(f"Source: {preview['article'].get('source', 'Unknown')}")
                print(f"URL: {preview['article'].get('url', 'N/A')}")
                print(f"\nGenerated Post:\n{preview['post']}")
                print(f"{'='*80}\n")
            except UnicodeEncodeError:
                import io
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
                print(f"\n{'='*80}")
                print(f"PREVIEW {i}/{len(previews)}")
                print(f"{'='*80}")
                print(f"Article: {preview['article'].get('title', 'Unknown')}")
                print(f"Source: {preview['article'].get('source', 'Unknown')}")
                print(f"URL: {preview['article'].get('url', 'N/A')}")
                print(f"\nGenerated Post:\n{preview['post']}")
                print(f"{'='*80}\n")
    else:
        success = agent.run(dry_run=args.dry_run)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

