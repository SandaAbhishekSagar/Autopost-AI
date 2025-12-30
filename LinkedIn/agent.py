"""
Main Agent Orchestrator
Coordinates news fetching, post generation, and LinkedIn posting
"""

import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional
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
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_path} not found!")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)

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

