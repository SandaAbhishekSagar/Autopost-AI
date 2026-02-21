"""
Flask Web Application for LinkedIn AI Auto-Poster
Provides a modern web UI for generating, reviewing, editing, and posting LinkedIn content.
Now powered by OpenAI web search instead of traditional news scraping.
"""

from flask import Flask, render_template, request, jsonify
import logging
import os
from agent import LinkedInAIAgent
from image_helper import get_image_for_post

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

agent = None


def init_agent():
    """Initialize the LinkedIn agent"""
    global agent
    try:
        agent = LinkedInAIAgent()
        return True
    except Exception as e:
        logger.error(f"Error initializing agent: {e}")
        return False


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/generate', methods=['POST'])
def generate_post():
    """Generate post previews using AI web search for news"""
    try:
        data = request.json or {}
        num_posts = min(data.get('num_posts', 1), 5)
        topics = data.get('topics', None)

        if not agent:
            if not init_agent():
                return jsonify({'error': 'Failed to initialize agent. Check your configuration.'}), 500

        previews = agent.preview_posts(num_posts=num_posts, topics=topics)

        posts = []
        for preview in previews:
            if 'articles' in preview:
                articles = preview['articles']
                article = preview['article']
                post_data = {
                    'article': {
                        'title': f"Multi-Article Story: {len(articles)} articles combined",
                        'source': ', '.join(set(a.get('source', 'Unknown') for a in articles)),
                        'url': article.get('url', ''),
                        'description': f"Combined {len(articles)} articles into a storytelling post"
                    },
                    'content': preview['post'],
                    'articles': [
                        {
                            'title': a.get('title', 'Unknown'),
                            'source': a.get('source', 'Unknown'),
                            'url': a.get('url', '')
                        }
                        for a in articles
                    ]
                }
            else:
                article = preview['article']
                post_data = {
                    'article': {
                        'title': article.get('title', 'Unknown'),
                        'source': article.get('source', 'Unknown'),
                        'url': article.get('url', ''),
                        'description': article.get('description', '')
                    },
                    'content': preview['post']
                }

            if article.get('value_score') is not None:
                post_data['scoring'] = {
                    'score': article.get('value_score', 0),
                    'percentage': article.get('value_percentage', 0),
                    'priority': article.get('value_priority', 'UNKNOWN'),
                    'recommendation': article.get('value_recommendation', ''),
                    'reasons': article.get('value_reasons', [])
                }

            posts.append(post_data)

        return jsonify({'success': True, 'posts': posts})

    except Exception as e:
        logger.error(f"Error generating post: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/post', methods=['POST'])
def post_to_linkedin():
    """Post content to LinkedIn with optional image"""
    try:
        data = request.json or {}
        post_content = data.get('content', '')
        article_url = data.get('article_url', '') or None
        article_title = data.get('article_title', '')

        if not post_content:
            return jsonify({'error': 'Post content is required'}), 400

        if not agent:
            if not init_agent():
                return jsonify({'error': 'Failed to initialize agent.'}), 500

        # Fetch or generate image for the post (if enabled)
        image = None
        include_image = agent.config.get('post', {}).get('include_image', True)
        openai_key = agent.config.get('post_generation', {}).get('openai_api_key')
        if include_image:
            try:
                image = get_image_for_post(
                    article_url=article_url,
                    article_title=article_title,
                    post_content=post_content,
                    openai_api_key=openai_key
                )
            except Exception as e:
                logger.warning(f"Could not get image for post: {e}")

        success = agent.linkedin_poster.post_to_linkedin(
            post_content=post_content,
            article_url=article_url,
            image=image
        )

        if success:
            return jsonify({'success': True, 'message': 'Post successfully published to LinkedIn!'})
        else:
            return jsonify({'success': False, 'error': 'Failed to post to LinkedIn. Check your access token.'}), 500

    except Exception as e:
        logger.error(f"Error posting to LinkedIn: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get agent configuration status"""
    try:
        if not agent:
            if not init_agent():
                return jsonify({'initialized': False, 'error': 'Failed to initialize agent'}), 500

        has_openai = bool(agent.config.get('post_generation', {}).get('openai_api_key'))
        has_linkedin = bool(agent.config.get('linkedin', {}).get('access_token'))

        topics = agent.config.get('news', {}).get('topics', [])
        search_model = agent.config.get('news', {}).get('search_model', 'gpt-4o-mini')

        return jsonify({
            'initialized': True,
            'config': {
                'openai_configured': has_openai,
                'linkedin_configured': has_linkedin,
                'search_model': search_model,
                'topics': topics
            }
        })

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/regenerate', methods=['POST'])
def regenerate_post():
    """Regenerate a post for a specific article"""
    try:
        data = request.json or {}
        article = data.get('article', {})

        if not article.get('title'):
            return jsonify({'error': 'Article data is required'}), 400

        if not agent:
            if not init_agent():
                return jsonify({'error': 'Failed to initialize agent.'}), 500

        post_content = agent.post_generator.generate_post(article)

        return jsonify({
            'success': True,
            'content': post_content
        })

    except Exception as e:
        logger.error(f"Error regenerating post: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    init_agent()

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print("\n" + "=" * 60)
    print("AutoPost AI - LinkedIn Content Generator")
    print("Powered by OpenAI Web Search")
    print("=" * 60)
    print(f"Starting server on http://localhost:{port}")
    print("=" * 60 + "\n")

    app.run(debug=debug, host='0.0.0.0', port=port, threaded=True)
