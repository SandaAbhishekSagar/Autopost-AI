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
                        "content": "You are a technical AI/ML expert creating highly engaging LinkedIn posts. Write posts in a storytelling format that are both technically deep AND highly engaging. Use eye-catching headings, strategic emojis, and narrative flow. Include specific technologies, frameworks, models, architectures, companies, and technical details. Reference specific AI companies (OpenAI, Anthropic, Google, Meta, Microsoft, etc.), models (GPT-4, Claude, Gemini, Llama, etc.), frameworks (PyTorch, TensorFlow, JAX, etc.), and technical concepts. Be specific about architectures, performance metrics, implementation details, and technical trade-offs. Write for a technical audience but make it captivating and shareable."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1200  # Increased for more technical detail
            )
            
            post_content = response.choices[0].message.content.strip()
            
            # Add hashtags if enabled
            if self.include_hashtags and self.hashtags:
                hashtag_string = " ".join(self.hashtags)
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
        
        prompt = f"""Create a highly engaging, storytelling-style LinkedIn post about this AI/ML news article that showcases deep technical expertise. The post MUST:

**FORMAT & STYLE:**
1. **Eye-Catching Heading**: Start with a compelling, attention-grabbing headline with strategic emojis (1-2 lines max, use 2-3 relevant emojis). IMPORTANT: Use plain text only - NO markdown formatting (no **bold**, no __italic__, no #hashtags in heading). Just use emojis and plain text for emphasis.
2. **Storytelling Format**: Write in a narrative, engaging style - tell a story with a beginning, middle, and end. Use phrases like "Let me share what caught my attention...", "Here's what's fascinating...", "This reminded me of when I..."
3. **Strategic Emojis**: Use 5-8 relevant emojis throughout (🤖 🚀 💡 🔥 ⚡ 🎯 🧠 💻 🔬 📊 🎨 but don't overuse - space them naturally)
4. **Engaging Hook**: First paragraph after heading should immediately capture attention with a personal connection or intriguing question

**TECHNICAL CONTENT (Maintain Depth):**
5. **Technical Depth**: Include specific technical details, architectures, models, frameworks, and methodologies
6. **Company & Technology References**: Name specific AI companies (OpenAI, Anthropic, Google DeepMind, Meta AI, Microsoft, NVIDIA, etc.), models (GPT-4, Claude, Gemini, Llama, Mistral, etc.), and frameworks (PyTorch, TensorFlow, JAX, HuggingFace, etc.)
7. **Technical Analysis**: Provide technical insights about:
   - Model architectures (transformer variants, attention mechanisms, MoE, etc.)
   - Training methodologies (RLHF, fine-tuning approaches, data pipelines)
   - Performance metrics (benchmarks, efficiency, latency, throughput)
   - Implementation details (scaling, optimization, deployment strategies)
   - Technical trade-offs and comparisons
8. **Personal Story Integration**: Weave in your experience naturally in storytelling format:
   - "In my work with {', '.join(self.profile.get('skills', [])[:3])}..."
   - "Having fine-tuned models like GPT-4 and LLaMA..."
   - "When I deployed YOLOv8 for object detection..."
   - Share a brief, relevant technical challenge or insight from your experience as a story
9. **Technical Perspective**: Share your professional technical opinion on implications
10. **Strong Call-to-Action**: End with an engaging question that invites discussion

**STRUCTURE:**
- Eye-catching heading with emoji (1-2 lines)
- Engaging opening paragraph (hook with personal connection)
- Technical deep-dive with storytelling elements (narrative flow)
- Personal connection/experience (weaved into the story)
- Technical implications and insights
- Engaging question/CTA

**TONE:**
- Engaging, conversational, storytelling style
- Professional yet approachable and exciting
- Technically accurate but shareable
- Make readers feel like they're learning something fascinating

**LENGTH**: Maximum {self.max_length} characters

Your Profile Information:
{profile_context}

Article Information:
Title: {title}
Description: {description}
Source: {source}
URL: {url}

CRITICAL INSTRUCTIONS:
- Start with an EYE-CATCHING HEADING (use 2-3 relevant emojis, make it compelling and attention-grabbing)
- **NO MARKDOWN FORMATTING IN HEADING**: Use plain text only - do NOT use **bold**, __italic__, or any markdown syntax in the heading. LinkedIn doesn't support markdown, so it will show as literal text. Use emojis and plain text for emphasis only.
- Write in STORYTELLING FORMAT - make it a narrative with flow, not a bullet list or dry technical report
- Use STRATEGIC EMOJIS (5-8 total, relevant to content, spaced naturally throughout)
- Create an ENGAGING HOOK in the first paragraph that draws readers in
- Extract EVERY technical detail from the article (model names, companies, frameworks, metrics, architectures)
- Use exact technical terminology (e.g., "GPT-4 Turbo", "Claude 3 Opus", "Llama 3 70B")
- Reference real AI companies and technologies
- Include specific technical metrics if mentioned
- Weave in your personal experience naturally as part of the story
- Make it ENGAGING, SHAREABLE, and COMPELLING while maintaining technical depth
- End with a compelling question that invites discussion
- Use storytelling phrases: "Here's what caught my attention...", "This reminded me of...", "Let me share..."

Write the LinkedIn post now. Do not include the URL in the post text (it will be added separately). Make it highly engaging, storytelling-style, with eye-catching heading and strategic emojis, while showcasing deep technical expertise."""

        return prompt

    def _generate_fallback_post(self, article: Dict) -> str:
        """Generate a simple fallback post if AI generation fails"""
        title = article.get('title', 'Interesting AI/ML Development')
        description = article.get('description', '')
        url = article.get('url', '')
        
        post = f"""🤖 Exciting development in AI/ML: {title}

{description[:200]}...

As someone working in AI/ML, I find this particularly interesting because it relates to my experience with {', '.join(self.profile.get('skills', ['AI/ML'])[:2])}.

What are your thoughts on this? Let's discuss in the comments!

{url if url else ''}"""
        
        if self.include_hashtags and self.hashtags:
            post += f"\n\n{' '.join(self.hashtags)}"
        
        return post[:self.max_length]

