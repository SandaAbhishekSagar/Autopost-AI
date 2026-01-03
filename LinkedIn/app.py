"""
Flask Web Application for LinkedIn AI/ML Auto-Poster
Provides a web UI for generating, reviewing, and posting LinkedIn content
"""

from flask import Flask, render_template, request, jsonify
import yaml
import logging
import os
from agent import LinkedInAIAgent
import sys
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global agent instance
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
    """Generate a post preview"""
    try:
        data = request.json
        num_posts = data.get('num_posts', 1)
        
        if not agent:
            if not init_agent():
                return jsonify({'error': 'Failed to initialize agent. Check your config.yaml'}), 500
        
        # Generate preview posts
        previews = agent.preview_posts(num_posts=num_posts)
        
        # Format response
        posts = []
        for preview in previews:
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
            
            # Add value scoring if available
            if article.get('value_score') is not None:
                post_data['scoring'] = {
                    'score': article.get('value_score', 0),
                    'percentage': article.get('value_percentage', 0),
                    'priority': article.get('value_priority', 'UNKNOWN'),
                    'recommendation': article.get('value_recommendation', ''),
                    'reasons': article.get('value_reasons', [])
                }
            
            posts.append(post_data)
        
        return jsonify({
            'success': True,
            'posts': posts
        })
    
    except Exception as e:
        logger.error(f"Error generating post: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/post', methods=['POST'])
def post_to_linkedin():
    """Post content to LinkedIn"""
    try:
        data = request.json
        post_content = data.get('content', '')
        article_url = data.get('article_url', '')
        
        if not post_content:
            return jsonify({'error': 'Post content is required'}), 400
        
        if not agent:
            if not init_agent():
                return jsonify({'error': 'Failed to initialize agent. Check your config.yaml'}), 500
        
        # Post to LinkedIn
        success = agent.linkedin_poster.post_to_linkedin(
            post_content=post_content,
            article_url=article_url if article_url else None
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Post successfully published to LinkedIn!'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to post to LinkedIn. Check the logs for details.'
            }), 500
    
    except Exception as e:
        logger.error(f"Error posting to LinkedIn: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get agent status"""
    try:
        if not agent:
            if not init_agent():
                return jsonify({
                    'initialized': False,
                    'error': 'Failed to initialize agent'
                }), 500
        
        # Check config
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            has_openai = bool(config.get('post_generation', {}).get('openai_api_key'))
            has_linkedin = bool(config.get('linkedin', {}).get('access_token'))
            
            return jsonify({
                'initialized': True,
                'config': {
                    'openai_configured': has_openai,
                    'linkedin_configured': has_linkedin
                }
            })
        except Exception as e:
            return jsonify({
                'initialized': False,
                'error': f'Error reading config: {str(e)}'
            }), 500
    
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize agent on startup
    init_agent()
    
    # Get port from environment variable (Railway provides this)
    port = int(os.environ.get('PORT', 5000))
    # Disable debug in production
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Run the app
    print("\n" + "="*60)
    print("LinkedIn AI/ML Auto-Poster - Web UI")
    print("="*60)
    print(f"Starting server on port {port}...")
    if not debug:
        print("Production mode")
    print("="*60 + "\n")
    
    # Use 0.0.0.0 to bind to all interfaces (required for Railway)
    app.run(debug=debug, host='0.0.0.0', port=port, threaded=True)

