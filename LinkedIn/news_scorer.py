"""
News Value Scorer Module
Analyzes and scores news articles to identify the most valuable content for posting
"""

import re
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NewsScorer:
    """Scores news articles based on value, impact, and posting worthiness"""
    
    # High-impact keywords that indicate major news
    HIGH_IMPACT_KEYWORDS = {
        'announcement': 10,
        'launch': 10,
        'release': 8,
        'breakthrough': 10,
        'new model': 9,
        'upgrade': 7,
        'partnership': 8,
        'acquisition': 9,
        'investment': 8,
        'funding': 7,
        'record': 8,
        'first': 9,
        'exclusive': 7,
        'major': 9,
        'significant': 8,
        'game-changer': 10,
        'revolutionary': 10,
        'billion': 9,
        '$1b': 10,
        '$2b': 10,
        'valuation': 7,
        'raised': 7,
        'secures': 8,
        'backed by': 7,
    }
    
    # Tech giant product keywords (higher value)
    TECH_GIANT_PRODUCTS = {
        'gpt-4': 10,
        'gpt-4 turbo': 10,
        'chatgpt': 9,
        'sora': 9,
        'dall-e': 8,
        'h100': 9,
        'a100': 8,
        'blackwell': 10,
        'gh200': 9,
        'gemini': 9,
        'gemini pro': 10,
        'gemini ultra': 10,
        'claude': 9,
        'claude 3': 10,
        'llama 3': 9,
        'llama 2': 7,
        'copilot': 8,
        'azure ai': 8,
        'bedrock': 8
    }
    
    # Major company names (higher value)
    MAJOR_COMPANIES = {
        'openai': 9,
        'nvidia': 9,
        'google': 8,
        'microsoft': 8,
        'meta': 8,
        'apple': 7,
        'amazon': 7,
        'anthropic': 8,
        'deepmind': 9
    }
    
    def __init__(self):
        pass
    
    def score_article(self, article: Dict) -> Dict:
        """
        Score an article based on multiple factors
        
        Returns:
            Dict with score, reasons, and recommendation
        """
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        text = f"{title} {description}"
        source = article.get('source', '').lower()
        
        score = 0
        reasons = []
        
        # 1. High-impact keywords (0-30 points)
        impact_score = 0
        for keyword, value in self.HIGH_IMPACT_KEYWORDS.items():
            if keyword in text:
                impact_score += value
                reasons.append(f"Contains high-impact keyword: '{keyword}'")
        score += min(impact_score, 30)  # Cap at 30
        
        # 2. Tech giant products (0-25 points)
        product_score = 0
        found_products = []
        for product, value in self.TECH_GIANT_PRODUCTS.items():
            if product in text:
                product_score += value
                found_products.append(product)
        if found_products:
            score += min(product_score, 25)  # Cap at 25
            reasons.append(f"Features major products: {', '.join(found_products[:3])}")
        
        # 3. Major company mentions (0-20 points)
        company_score = 0
        found_companies = []
        for company, value in self.MAJOR_COMPANIES.items():
            if company in text:
                company_score += value
                found_companies.append(company)
        if found_companies:
            score += min(company_score, 20)  # Cap at 20
            reasons.append(f"From major company: {', '.join(found_companies[:2])}")
        
        # 4. Recency bonus (0-15 points)
        recency_score = self._calculate_recency_score(article)
        score += recency_score
        if recency_score > 0:
            reasons.append(f"Recent news ({recency_score} points)")
        
        # 5. Source quality (0-10 points)
        source_score = self._calculate_source_score(source)
        score += source_score
        if source_score > 0:
            reasons.append(f"High-quality source")
        
        # 6. Technical depth (0-10 points)
        technical_score = self._calculate_technical_depth(text)
        score += technical_score
        if technical_score > 5:
            reasons.append("Contains technical details")
        
        # Determine recommendation
        recommendation = self._get_recommendation(score)
        
        return {
            'score': score,
            'max_score': 110,
            'percentage': round((score / 110) * 100, 1),
            'reasons': reasons[:5],  # Top 5 reasons
            'recommendation': recommendation,
            'priority': self._get_priority(score)
        }
    
    def _calculate_recency_score(self, article: Dict) -> int:
        """Calculate score based on how recent the article is"""
        published_at = article.get('published_at', '')
        if not published_at:
            return 0
        
        try:
            if 'T' in published_at:
                pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            else:
                pub_date = datetime.strptime(published_at, '%Y-%m-%d %H:%M:%S')
            
            now = datetime.now(pub_date.tzinfo) if hasattr(pub_date, 'tzinfo') and pub_date.tzinfo else datetime.now()
            age_hours = (now - pub_date).total_seconds() / 3600
            
            if age_hours < 6:
                return 15  # Very recent
            elif age_hours < 12:
                return 12  # Recent
            elif age_hours < 24:
                return 8   # Today
            elif age_hours < 48:
                return 5   # Yesterday
            else:
                return 2   # Older
        except (ValueError, TypeError, OSError):
            return 5  # Default if parsing fails
    
    def _calculate_source_score(self, source: str) -> int:
        """Calculate score based on source quality"""
        high_quality_sources = [
            'the verge', 'techcrunch', 'wired', 'venturebeat',
            'reuters', 'bloomberg', 'tech', 'arstechnica',
            'the information', 'axios'
        ]
        
        source_lower = source.lower()
        for quality_source in high_quality_sources:
            if quality_source in source_lower:
                return 10
        
        return 5  # Default for other sources
    
    def _calculate_technical_depth(self, text: str) -> int:
        """Calculate score based on technical depth"""
        technical_indicators = [
            'architecture', 'model', 'performance', 'benchmark',
            'training', 'inference', 'latency', 'throughput',
            'parameters', 'tokens', 'gpu', 'compute', 'flops',
            'transformer', 'neural', 'algorithm', 'framework'
        ]
        
        count = sum(1 for indicator in technical_indicators if indicator in text)
        return min(count * 2, 10)  # Max 10 points
    
    def _get_recommendation(self, score: int) -> str:
        """Get posting recommendation based on score"""
        if score >= 80:
            return "MUST POST - High-value breaking news"
        elif score >= 60:
            return "SHOULD POST - Important news worth sharing"
        elif score >= 40:
            return "CONSIDER POSTING - Decent news, but not critical"
        elif score >= 20:
            return "LOW PRIORITY - Only if you need content"
        else:
            return "SKIP - Not worth posting"
    
    def _get_priority(self, score: int) -> str:
        """Get priority level"""
        if score >= 80:
            return "HIGH"
        elif score >= 60:
            return "MEDIUM-HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        else:
            return "VERY LOW"
    
    def rank_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Rank articles by their value score
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of articles with scores, sorted by score (highest first)
        """
        scored_articles = []
        
        for article in articles:
            score_data = self.score_article(article)
            article_with_score = {
                **article,
                'value_score': score_data['score'],
                'value_percentage': score_data['percentage'],
                'value_reasons': score_data['reasons'],
                'value_recommendation': score_data['recommendation'],
                'value_priority': score_data['priority']
            }
            scored_articles.append(article_with_score)
        
        # Sort by score (highest first)
        scored_articles.sort(key=lambda x: x.get('value_score', 0), reverse=True)
        
        return scored_articles
    
    def get_posting_frequency_recommendation(self, articles: List[Dict]) -> Dict:
        """
        Recommend posting frequency based on news quality
        
        Args:
            articles: List of scored articles
            
        Returns:
            Dict with frequency recommendation and reasoning
        """
        if not articles:
            return {
                'recommended_frequency': '3-4 times per week',
                'reason': 'No high-value news available',
                'high_value_count': 0,
                'medium_value_count': 0,
                'low_value_count': 0
            }
        
        # Score all articles
        scored_articles = self.rank_articles(articles)
        
        # Count by priority
        high_value = [a for a in scored_articles if a.get('value_score', 0) >= 60]
        medium_value = [a for a in scored_articles if 40 <= a.get('value_score', 0) < 60]
        low_value = [a for a in scored_articles if a.get('value_score', 0) < 40]
        
        high_count = len(high_value)
        medium_count = len(medium_value)
        low_count = len(low_value)
        
        # Determine recommendation
        if high_count >= 3:
            frequency = "Daily (5-7 times per week)"
            reason = f"{high_count} high-value articles found - excellent time to post daily"
        elif high_count >= 2:
            frequency = "4-5 times per week"
            reason = f"{high_count} high-value articles - good opportunity for frequent posting"
        elif high_count >= 1 or medium_count >= 3:
            frequency = "3-4 times per week"
            reason = f"{high_count} high-value + {medium_count} medium-value articles - optimal posting frequency"
        elif medium_count >= 2:
            frequency = "2-3 times per week"
            reason = f"{medium_count} medium-value articles - moderate posting recommended"
        else:
            frequency = "1-2 times per week"
            reason = f"Limited high-value news ({high_count} high, {medium_count} medium) - post selectively"
        
        return {
            'recommended_frequency': frequency,
            'reason': reason,
            'high_value_count': high_count,
            'medium_value_count': medium_count,
            'low_value_count': low_count,
            'top_articles': scored_articles[:3]  # Top 3 articles
        }

