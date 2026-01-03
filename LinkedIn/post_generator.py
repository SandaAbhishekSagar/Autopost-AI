"""
Post Generator Module
Uses AI to generate personalized LinkedIn posts from news articles
"""

from openai import OpenAI
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.profile = config.get('profile', {})
        self.post_config = config.get('post_generation', {})
        
        # Initialize OpenAI
        api_key = self.post_config.get('openai_api_key')
        if not api_key:
            raise ValueError("OpenAI API key is required in config.yaml")
        
        self.client = OpenAI(api_key=api_key)
        self.model = self.post_config.get('ai_model', 'gpt-4')
        self.tone = self.post_config.get('tone', 'professional')
        self.max_length = self.post_config.get('max_post_length', 3000)
        self.include_hashtags = self.post_config.get('include_hashtags', True)
        self.hashtags = self.post_config.get('hashtags', [])

    def generate_post(self, article: Dict) -> str:
        """Generate a LinkedIn post from a news article"""
        
        # Build context about the user
        profile_context = self._build_profile_context()
        
        # Build the prompt
        prompt = self._build_prompt(article, profile_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional tech content creator and AI/ML expert with deep industry knowledge. You create long-form, highly valuable LinkedIn posts (800-2000 characters) that professionals actually want to read and share. Your posts are authoritative, insightful, and provide real value - not generic summaries. You write like a thought leader who breaks down complex tech news in an accessible yet deep way. You focus on major tech giants (OpenAI, NVIDIA, Google, Microsoft, Meta, Apple, Amazon, Anthropic, etc.) and their products. Your writing style is professional, engaging, and educational - you teach while you inform. You use strategic emojis sparingly (3-5 total) and structure posts for maximum readability with clear sections and white space."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.75,
                max_tokens=2500  # Significantly increased for long-form professional content
            )
            
            post_content = response.choices[0].message.content.strip()
            
            # Check minimum length and warn if too short
            min_length = 800
            post_without_hashtags = post_content
            if self.include_hashtags and self.hashtags:
                # Remove hashtags for length check
                for tag in self.hashtags:
                    post_without_hashtags = post_without_hashtags.replace(tag, '')
            
            if len(post_without_hashtags.strip()) < min_length:
                logger.warning(f"Generated post is shorter than recommended minimum ({len(post_without_hashtags)} chars). Minimum recommended: {min_length} chars for professional content.")
            
            # Add hashtags if enabled (limit to 5-7 most relevant)
            if self.include_hashtags and self.hashtags:
                # Limit hashtags to avoid clutter
                limited_hashtags = self.hashtags[:7] if len(self.hashtags) > 7 else self.hashtags
                hashtag_string = " ".join(limited_hashtags)
                post_content = f"{post_content}\n\n{hashtag_string}"
            
            # Ensure length is within limits
            if len(post_content) > self.max_length:
                post_content = post_content[:self.max_length-3] + "..."
            
            return post_content
            
        except Exception as e:
            logger.error(f"Error generating post: {e}")
            # Fallback to a simple template
            return self._generate_fallback_post(article)

    def _build_profile_context(self) -> str:
        """Build a context string about the user's profile"""
        context_parts = []
        
        if self.profile.get('name'):
            context_parts.append(f"Name: {self.profile['name']}")
        
        if self.profile.get('title'):
            context_parts.append(f"Title: {self.profile['title']}")
        
        if self.profile.get('current_role'):
            context_parts.append(f"Current Role: {self.profile['current_role']}")
        
        if self.profile.get('skills'):
            skills = ", ".join(self.profile['skills'])
            context_parts.append(f"Technical Skills: {skills}")
        
        if self.profile.get('experience_years'):
            context_parts.append(f"Experience: {self.profile['experience_years']} years")
        
        if self.profile.get('expertise_areas'):
            expertise = ", ".join(self.profile['expertise_areas'])
            context_parts.append(f"Expertise Areas: {expertise}")
        
        # Add education information
        if self.profile.get('education'):
            edu = self.profile['education']
            edu_str = f"Education: {edu.get('degree', '')} from {edu.get('university', '')}"
            if edu.get('gpa'):
                edu_str += f" (GPA: {edu['gpa']})"
            context_parts.append(edu_str)
            
            if edu.get('achievements'):
                achievements = ", ".join(edu['achievements'])
                context_parts.append(f"Notable Achievements: {achievements}")
        
        return "\n".join(context_parts)

    def _build_prompt(self, article: Dict, profile_context: str) -> str:
        """Build the prompt for OpenAI"""
        title = article.get('title', 'No title')
        description = article.get('description', 'No description')
        url = article.get('url', '')
        source = article.get('source', 'Unknown')
        
        prompt = f"""Create a professional, long-form LinkedIn post (800-2000 characters, excluding hashtags) about this AI/ML news from major tech giants. Write like a professional tech content creator - authoritative, insightful, and valuable.

**CRITICAL: FIRST 2 LINES ARE EVERYTHING**
LinkedIn only shows the first 2 lines in the feed. If those don't grab attention, people will scroll past. Make them count!

**MANDATORY STRUCTURE (Follow this exact format with white space between sections):**

1. **COMPELLING HEADLINE (EXACTLY 2 LINES - MOST CRITICAL!)**
   - Line 1: Curiosity-driven, attention-grabbing hook that makes people stop scrolling
   - Line 2: Continue the hook or add context that builds intrigue
   - Use 1-2 strategic emojis maximum (one in first line recommended)
   - NO markdown formatting (no **bold**, __italic__)
   - Must be curiosity-driven, not generic
   - Examples of GOOD hooks:
     * "This NVIDIA announcement changes everything for AI training. Here's why it matters..."
     * "OpenAI just dropped something that will reshape how we build AI apps. Most people missed this detail..."
     * "Everyone's talking about this AI release, but here's what actually matters for developers..."
   - Examples of BAD hooks (avoid these):
     * "Good morning LinkedIn!"
     * "Check out this news about AI"
     * "Interesting development in AI/ML"
   - Add blank line after

2. **THE NEWS - DETAILED BREAKDOWN (4-6 lines, 2-4 lines per paragraph)**
   - What actually happened? Provide comprehensive context
   - Who is involved? (Company, product, team)
   - What are the key details? (Specs, metrics, features, numbers)
   - When did this happen? (Timeline, release date)
   - Why is this significant? (Context and background)
   - Extract ALL technical details from the article
   - Use specific product names: GPT-4 Turbo, NVIDIA H100, Google Gemini Pro, etc.
   - Keep paragraphs short (2-4 lines max) for readability
   - Add blank line after

3. **WHY THIS MATTERS - DEEP ANALYSIS (5-8 lines, 2-4 lines per paragraph)**
   - Industry implications: How does this affect the AI/ML landscape?
   - Technical significance: What's the technical breakthrough or innovation?
   - Market impact: Who benefits? What problems does this solve?
   - Competitive landscape: How does this compare to competitors?
   - Real-world applications: Where and how will this be used?
   - Future implications: What does this enable next?
   - Provide YOUR professional analysis, not just restating the news
   - Keep paragraphs short (2-4 lines max) - no walls of text
   - Add blank line after

4. **TECHNICAL DEEP DIVE (4-6 lines, 2-4 lines per paragraph)**
   - Architecture details: How does it work technically?
   - Performance metrics: Benchmarks, speed, efficiency, scale
   - Technical innovations: What's new or different?
   - Implementation considerations: What does it take to use this?
   - Trade-offs: What are the limitations or considerations?
   - Reference frameworks, models, hardware specifics
   - Keep paragraphs short (2-4 lines max) for easy scanning
   - Add blank line after

5. **PERSONAL INSIGHT / EXPERIENCE (3-5 lines)**
   - Connect to your experience: "In my work with {', '.join(self.profile.get('skills', ['AI/ML'])[:3])}..."
   - Share relevant insights from your expertise
   - How would you use this? What would you build?
   - What challenges have you faced that this addresses?
   - Sound authentic and personal, NOT like ChatGPT or corporate marketing
   - Use first-person language naturally: "I think...", "I've found...", "In my experience..."
   - Avoid generic phrases - be specific about your experience
   - Add blank line after

6. **CALL TO ACTION (1-2 lines)**
   - Thought-provoking question that invites discussion
   - Make it specific and engaging
   - Examples: "What use cases are you most excited about?" or "How do you think this will change your workflow?"

**TECH GIANTS & PRODUCTS TO EMPHASIZE:**
- OpenAI: GPT-4, GPT-4 Turbo, ChatGPT, Sora, DALL-E, Whisper, API updates, pricing
- NVIDIA: H100, A100, GH200, Blackwell, RTX GPUs, CUDA, AI chips, data center infrastructure
- Google: Gemini, Gemini Pro/Ultra, DeepMind, AlphaGo, AlphaFold, PaLM, BERT, TensorFlow
- Microsoft: Copilot, Azure AI, GPT-4 integration, Bing Chat, Microsoft 365 AI, Azure OpenAI
- Meta: Llama 2, Llama 3, OPT, AI research, PyTorch, open-source models
- Apple: CoreML, Neural Engine, Siri, on-device AI, MLX framework
- Amazon: Bedrock, Alexa AI, SageMaker, AWS AI services, Titan models
- Anthropic: Claude, Claude 3 (Opus/Sonnet/Haiku), Constitutional AI, safety research
- Others: Tesla Dojo, X.AI Grok, Mistral AI, Cohere, etc.

**WRITING REQUIREMENTS (ALIGNED WITH LINKEDIN BEST PRACTICES):**
- MINIMUM LENGTH: 800 characters (excluding hashtags) - make it substantial!
- TARGET LENGTH: 1200-1800 characters for optimal engagement
- MAXIMUM LENGTH: {self.max_length} characters
- FIRST 2 LINES: Must be curiosity-driven and attention-grabbing (LinkedIn only shows these in feed!)
- Use strategic emojis: 3-5 total MAXIMUM, spaced naturally (🤖 🚀 💡 🔥 ⚡ 🎯 🧠 💻)
- Paragraph length: 2-4 lines maximum per paragraph (no walls of text)
- White space: Blank line between each major section for readability
- Professional tone: Authoritative but accessible, educational but engaging
- Authentic voice: Sound like a real person, NOT ChatGPT or corporate marketing
- NO markdown formatting anywhere (LinkedIn doesn't support it - will show as literal text)
- Write in first person when sharing personal insights
- Be specific: Use exact product names, metrics, and technical terms
- Provide value: Teach, explain, analyze - don't just summarize or restate the news
- Easy to scan: Break up text, use short paragraphs, make it readable

**TONE & STYLE:**
- Professional tech content creator voice (authoritative but approachable)
- Educational and valuable (teach, don't just inform)
- Engaging but not overly casual (maintain professionalism)
- Technical depth without being inaccessible (explain complex concepts simply)
- Thought leadership quality (provide unique insights, not generic summaries)
- Authentic human voice (sound like you're talking to a colleague, not giving a presentation)
- Value-first approach (every sentence should add value, not just fill space)

Your Profile Information:
{profile_context}

Article Information:
Title: {title}
Description: {description}
Source: {source}
URL: {url}

**CRITICAL CHECKLIST (MUST FOLLOW ALL):**
- ✅ FIRST 2 LINES: Curiosity-driven hook that stops scrolling (LinkedIn only shows these!)
- ✅ Follow the EXACT 6-section structure above
- ✅ Each section must be FULLY DEVELOPED (not 1-2 sentences)
- ✅ MINIMUM 800 characters (excluding hashtags)
- ✅ Paragraphs: 2-4 lines maximum (no walls of text)
- ✅ White space: Blank line between each section
- ✅ Extract and include ALL technical details from the article
- ✅ Emphasize the specific tech giant and their products
- ✅ Provide deep analysis, not surface-level summary
- ✅ Authentic voice: Sound like a real person, not ChatGPT
- ✅ Value-first: Every section should teach or provide insight
- ✅ Strategic emojis: 3-5 total maximum, spaced naturally
- ✅ NO markdown formatting anywhere (LinkedIn doesn't support it)
- ✅ Engaging question: End with thought-provoking CTA
- ✅ Easy to scan: Short paragraphs, clear sections, readable format

**AVOID:**
- ❌ Generic hooks like "Good morning LinkedIn" or "Check out this news"
- ❌ Long paragraphs (more than 4 lines)
- ❌ Walls of text without breaks
- ❌ Corporate marketing speak
- ❌ Just summarizing the news without adding value
- ❌ Too many emojis (more than 5)
- ❌ Markdown formatting (will show as literal text)

Write the complete LinkedIn post now following the structure above. Do not include the URL in the post text."""

        return prompt

    def _generate_fallback_post(self, article: Dict) -> str:
        """Generate a professional fallback post if AI generation fails"""
        title = article.get('title', 'Interesting AI/ML Development')
        description = article.get('description', '')
        url = article.get('url', '')
        
        # Create a more substantial fallback post
        post = f"""🚀 Breaking: {title}

Here's what you need to know about this latest development in AI/ML:

{description[:400] if len(description) > 400 else description}

This is particularly relevant for those working with {', '.join(self.profile.get('skills', ['AI/ML'])[:3])}. The implications could be significant for how we approach AI development and deployment.

Key takeaways:
• This represents a notable shift in the AI landscape
• The technical details suggest important improvements in performance and capabilities
• Industry applications could be wide-ranging

From my experience in {', '.join(self.profile.get('expertise_areas', ['AI/ML'])[:2])}, I see this addressing several challenges we've been facing in the field.

What are your thoughts on this development? How do you see this impacting your work?

{url if url else ''}"""
        
        if self.include_hashtags and self.hashtags:
            limited_hashtags = self.hashtags[:7] if len(self.hashtags) > 7 else self.hashtags
            post += f"\n\n{' '.join(limited_hashtags)}"
        
        return post[:self.max_length]

