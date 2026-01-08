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

try:
    from news_scorer import NewsScorer
    NEWS_SCORER_AVAILABLE = True
except ImportError:
    NEWS_SCORER_AVAILABLE = False
    # Logger is defined above, so this is safe
    pass  # Will log warning in __init__ if needed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LinkedInAIAgent:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the agent with configuration"""
        self.config = self._load_config(config_path)
        news_config = self.config.get('news', {})
        self.news_fetcher = NewsFetcher(news_config)
        self.post_generator = PostGenerator(self.config)
        self.linkedin_poster = LinkedInPoster(self.config.get('linkedin', {}))
        
        # Multi-article settings
        self.use_multiple_articles = news_config.get('use_multiple_articles', False)
        self.articles_per_post = news_config.get('articles_per_post', 3)
        
        if self.use_multiple_articles:
            logger.info(f"Multi-article storytelling mode ENABLED - will combine {self.articles_per_post} articles per post")
        else:
            logger.info("Single article mode - generating posts from individual articles")
        if NEWS_SCORER_AVAILABLE:
            self.news_scorer = NewsScorer()
            logger.info("News value scoring enabled - posting frequency recommendations available")
        else:
            self.news_scorer = None
            logger.warning("NewsScorer not available - posting frequency recommendations disabled")
        
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
        
        # News sources - Focus on OpenAI, NVIDIA, and Tech Giants
        config['news'] = {
            'sources': [
                'https://www.theverge.com/ai-artificial-intelligence',
                'https://techcrunch.com/tag/artificial-intelligence/',
                'https://venturebeat.com/ai/',
                'https://www.theverge.com/tag/openai',
                'https://www.theverge.com/tag/nvidia'
            ],
            'rss_feeds': [
                'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',
                'https://techcrunch.com/feed/',
                'https://www.theverge.com/rss/index.xml',
                'https://feeds.feedburner.com/venturebeat/SZYF',
                'https://www.wired.com/feed/rss'
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
            'ai_model': os.environ.get('OPENAI_MODEL', 'gpt-4'),  # gpt-4 recommended for longer, professional posts
            'openai_api_key': openai_api_key,
            'tone': os.environ.get('POST_TONE', 'professional'),
            'max_post_length': int(os.environ.get('MAX_POST_LENGTH', '3000')),  # Posts will be 800-2000 chars for professional quality
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
        
        # Content filtering - Focus on tech giants
        config['content'] = {
            'min_article_age_hours': int(os.environ.get('MIN_ARTICLE_AGE_HOURS', '0')),
            'max_article_age_hours': int(os.environ.get('MAX_ARTICLE_AGE_HOURS', '48')),
            'keywords_required': os.environ.get('KEYWORDS_REQUIRED', 'OpenAI,NVIDIA,Google,Microsoft,Meta,Apple,Amazon,Anthropic,GPT-4,ChatGPT,Gemini,Claude,Llama,Copilot').split(','),
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
            # Step 1: Fetch latest news (ranked by value if scorer available)
            logger.info("Fetching latest AI/ML news...")
            rank_by_value = self.news_scorer is not None
            # Fetch enough articles for multi-article mode if enabled
            limit = max(10, self.articles_per_post * 2) if self.use_multiple_articles else 10
            articles = self.news_fetcher.get_latest_news(limit=limit, rank_by_value=rank_by_value)
            
            if not articles:
                logger.warning("No articles found matching criteria")
                return False
            
            logger.info(f"Found {len(articles)} relevant articles")
            
            # Step 1.5: Analyze news value and provide posting frequency recommendation
            if self.news_scorer:
                self._display_news_analysis(articles)
            
            # Step 2: Generate post (single or multi-article based on config)
            if self.use_multiple_articles and len(articles) >= self.articles_per_post:
                # Multi-article storytelling mode
                selected_articles = articles[:self.articles_per_post]
                logger.info(f"Generating multi-article storytelling post from {len(selected_articles)} articles:")
                for i, art in enumerate(selected_articles, 1):
                    title = art.get('title', 'Unknown')[:60]
                    source = art.get('source', 'Unknown')
                    logger.info(f"  {i}. {title}... ({source})")
                
                post_content = self.post_generator.generate_multi_article_post(selected_articles)
                logger.info("Multi-article storytelling post generated successfully")
                
                # Use first article URL for LinkedIn post metadata
                article = selected_articles[0]
            else:
                # Single article mode (backward compatible)
                article = articles[0]  # Get the highest value one (or most recent)
                article_title = article.get('title', 'Unknown')
                if self.news_scorer and article.get('value_score'):
                    logger.info(f"Generating post for top article: {article_title} (Score: {article.get('value_score')}/110)")
                else:
                    logger.info(f"Generating post for: {article_title}")
                
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

    def _display_news_analysis(self, articles: List[Dict]) -> None:
        """Display news value analysis and posting frequency recommendations"""
        if not self.news_scorer or not articles:
            return
        
        try:
            # Get posting frequency recommendation
            freq_recommendation = self.news_scorer.get_posting_frequency_recommendation(articles)
            
            print("\n" + "="*80)
            print("📊 NEWS VALUE ANALYSIS & POSTING RECOMMENDATIONS")
            print("="*80)
            print(f"\n🎯 Recommended Posting Frequency: {freq_recommendation['recommended_frequency']}")
            print(f"💡 Reason: {freq_recommendation['reason']}")
            print(f"\n📈 News Quality Breakdown:")
            print(f"   • High-value articles (score ≥60): {freq_recommendation['high_value_count']}")
            print(f"   • Medium-value articles (score 40-59): {freq_recommendation['medium_value_count']}")
            print(f"   • Low-value articles (score <40): {freq_recommendation['low_value_count']}")
            
            # Show top articles
            if freq_recommendation.get('top_articles'):
                print(f"\n🏆 Top {len(freq_recommendation['top_articles'])} Articles by Value:")
                for i, article in enumerate(freq_recommendation['top_articles'], 1):
                    score = article.get('value_score', 0)
                    percentage = article.get('value_percentage', 0)
                    priority = article.get('value_priority', 'UNKNOWN')
                    recommendation = article.get('value_recommendation', '')
                    title = article.get('title', 'Unknown')[:60]
                    print(f"\n   {i}. {title}...")
                    print(f"      Score: {score}/110 ({percentage}%) | Priority: {priority}")
                    print(f"      Recommendation: {recommendation}")
                    if article.get('value_reasons'):
                        reasons = article.get('value_reasons', [])[:2]
                        print(f"      Why: {', '.join(reasons)}")
            
            print("\n" + "="*80 + "\n")
        except Exception as e:
            logger.warning(f"Error displaying news analysis: {e}")
    
    def preview_posts(self, num_posts: int = 3) -> List[Dict]:
        """
        Preview multiple posts without posting
        
        Args:
            num_posts: Number of posts to preview
            
        Returns:
            List of dictionaries with article(s) and post content
        """
        logger.info(f"Generating preview for {num_posts} posts...")
        
        # Get enough articles for multi-article mode if enabled
        if self.use_multiple_articles:
            articles_needed = num_posts * self.articles_per_post
        else:
            articles_needed = num_posts
        
        # Get articles ranked by value
        rank_by_value = self.news_scorer is not None
        articles = self.news_fetcher.get_latest_news(limit=articles_needed, rank_by_value=rank_by_value)
        
        # Display analysis if scorer available
        if self.news_scorer:
            self._display_news_analysis(articles)
        
        previews = []
        
        if self.use_multiple_articles and len(articles) >= self.articles_per_post:
            # Multi-article mode
            for i in range(num_posts):
                start_idx = i * self.articles_per_post
                end_idx = start_idx + self.articles_per_post
                
                if end_idx > len(articles):
                    break
                
                selected_articles = articles[start_idx:end_idx]
                
                print(f"\n📝 Generating Multi-Article Post {i+1}/{num_posts}")
                print(f"   Combining {len(selected_articles)} articles:")
                for j, art in enumerate(selected_articles, 1):
                    title = art.get('title', 'Unknown')[:60]
                    source = art.get('source', 'Unknown')
                    print(f"      {j}. {title}... ({source})")
                
                post_content = self.post_generator.generate_multi_article_post(selected_articles)
                previews.append({
                    'article': selected_articles[0],  # Use first article for metadata
                    'articles': selected_articles,  # Include all articles
                    'post': post_content
                })
        else:
            # Single article mode (backward compatible)
            for i, article in enumerate(articles[:num_posts], 1):
                # Show scoring for each article before generating post
                if self.news_scorer and article.get('value_score') is not None:
                    score = article.get('value_score', 0)
                    percentage = article.get('value_percentage', 0)
                    priority = article.get('value_priority', 'UNKNOWN')
                    recommendation = article.get('value_recommendation', '')
                    title = article.get('title', 'Unknown')[:70]
                    
                    print(f"\n📝 Generating Post {i}/{min(num_posts, len(articles))}")
                    print(f"   Article: {title}...")
                    print(f"   📊 Value Score: {score}/110 ({percentage}%) | Priority: {priority}")
                    print(f"   💡 Recommendation: {recommendation}")
                
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
                article = preview['article']
                print(f"\n{'='*80}")
                print(f"PREVIEW {i}/{len(previews)}")
                print(f"{'='*80}")
                print(f"Article: {article.get('title', 'Unknown')}")
                print(f"Source: {article.get('source', 'Unknown')}")
                print(f"URL: {article.get('url', 'N/A')}")
                
                # Display value scoring if available
                if agent.news_scorer and article.get('value_score') is not None:
                    score = article.get('value_score', 0)
                    percentage = article.get('value_percentage', 0)
                    priority = article.get('value_priority', 'UNKNOWN')
                    recommendation = article.get('value_recommendation', '')
                    print(f"\n📊 VALUE SCORING:")
                    print(f"   Score: {score}/110 ({percentage}%)")
                    print(f"   Priority: {priority}")
                    print(f"   Recommendation: {recommendation}")
                    if article.get('value_reasons'):
                        reasons = article.get('value_reasons', [])
                        print(f"   Why: {', '.join(reasons[:3])}")
                
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

