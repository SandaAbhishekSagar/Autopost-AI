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
                        "content": "You are a technical AI/ML expert creating highly engaging LinkedIn posts focused on major tech giants (OpenAI, NVIDIA, Google, Microsoft, Meta, Apple, Amazon, Anthropic, etc.). Write posts that sound like a real person sharing insights, not ChatGPT or corporate marketing. Use authentic, conversational language with personal touches ('I learned...', 'I think...', 'I'd build...'). CRITICAL: Write substantial, detailed posts (minimum 400 characters excluding hashtags). Expand on each section with context, analysis, and insight. Do NOT write short, generic posts. ALWAYS include relevant experience with similar projects when applicable - reference specific projects, technologies, or work experiences from the user's profile that relate to the news. ALWAYS emphasize the specific company (OpenAI, NVIDIA, Google, Microsoft, Meta, etc.) and their products/models (GPT-4, ChatGPT, Sora, H100, A100, Gemini, Claude, Llama, Copilot, etc.). Include specific technologies, frameworks, models, architectures, companies, and technical details. Keep technical concepts simple enough for non-experts while maintaining depth. Focus on value and teaching, not bragging. Use maximum 3-5 emojis total. Focus on breaking news and major announcements from these tech giants."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500  # Increased to allow for longer, more detailed posts
            )
            
            post_content = response.choices[0].message.content.strip()
            
            # Check if post is too short (excluding hashtags)
            post_without_hashtags = post_content
            min_length = 400
            if len(post_without_hashtags) < min_length:
                logger.warning(f"Generated post is too short ({len(post_without_hashtags)} chars). Minimum recommended: {min_length} chars. Consider regenerating.")
            
            # Add hashtags if enabled (limit to 3-5, place at bottom)
            if self.include_hashtags and self.hashtags:
                # Limit to 3-5 hashtags maximum
                limited_hashtags = self.hashtags[:5] if len(self.hashtags) > 5 else self.hashtags
                hashtag_string = " ".join(limited_hashtags)
                # Ensure hashtags are at the bottom, not in the middle
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
        
        # Add project experience (if available) - CRITICAL for connecting to similar work
        if self.profile.get('projects'):
            projects = self.profile['projects']
            if isinstance(projects, list):
                project_list = []
                for project in projects:
                    if isinstance(project, dict):
                        proj_str = project.get('name', '')
                        if project.get('technologies'):
                            techs = ", ".join(project['technologies']) if isinstance(project['technologies'], list) else project['technologies']
                            proj_str += f" (Technologies: {techs})"
                        if project.get('description'):
                            proj_str += f" - {project['description']}"
                        project_list.append(proj_str)
                    else:
                        project_list.append(str(project))
                if project_list:
                    context_parts.append(f"Relevant Projects & Work Experience: {'; '.join(project_list)}")
            else:
                context_parts.append(f"Relevant Projects & Work Experience: {projects}")
        
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
        
        prompt = f"""Create a highly engaging, storytelling-style LinkedIn post about this AI/ML news article from major tech giants (OpenAI, NVIDIA, Google, Microsoft, Meta, Apple, Amazon, Anthropic, etc.) that showcases deep technical expertise. 

**CRITICAL: Follow this exact structure with white space between sections:**

1. **STRONG OPENING HOOK (First 1-2 lines - LinkedIn cuts after 2 lines!)**:
   - Must be curiosity-driven and attention-grabbing
   - NOT generic like "Good morning LinkedIn" or "Check out this news"
   - Examples of good hooks:
     * "This could change how startups use AI."
     * "Everyone is talking about this AI release, but here's what matters."
     * "Most people missed this detail in today's AI news."
     * "I just learned something that changes how I think about [topic]."
   - Use 1-2 strategic emojis maximum in the hook

2. **WHAT HAPPENED (3-5 lines - EXPAND ON THE NEWS)**:
   - Provide a detailed summary of the news, not just one line
   - Include key details, context, and specifics from the article
   - Explain what actually happened, who was involved, what the situation is
   - Keep it simple enough for non-experts but provide enough detail to be informative
   - DO NOT just copy the headline - expand on it with context
   - Add white space after this section

3. **WHY IT MATTERS (4-6 lines - DEEP ANALYSIS REQUIRED)**:
   - Explain the impact, use-case, or future implications in detail
   - Add your own thinking and analysis, not just restate the news
   - Discuss technical implications, industry impact, or broader significance
   - Connect it to trends, challenges, or opportunities in AI/ML
   - Make it useful, insightful, or thought-provoking
   - Provide specific examples or scenarios where this matters
   - Add white space after this section

4. **HOW I WOULD USE IT / WHAT I LEARNED / SIMILAR PROJECT EXPERIENCE (3-5 lines - PERSONAL CONNECTION)**:
   - Use personal language: "I learned...", "I think...", "I'd build...", "I would use this to..."
   - **CRITICAL: Include your experience with similar projects if applicable**
   - Reference specific projects you've worked on that relate to this news (e.g., "When I worked on [similar project], I encountered...", "This reminds me of a project where I...", "Having built [similar thing], I can see how this would...")
   - Share detailed, relevant insights from your experience
   - Connect the news to your actual work experience naturally and specifically
   - Explain how this relates to your skills, projects, or expertise areas
   - Sound like a real person, not ChatGPT or corporate speak
   - Avoid over-polished corporate tone
   - DO NOT use generic phrases like "I'd use this to explore new possibilities" - be specific
   - Add white space after this section

5. **ENGAGING QUESTION / CTA (1 line)**:
   - End with a compelling question that invites discussion
   - Make it thought-provoking and discussion-worthy

The post MUST:

**FORMAT & STYLE:**
1. **Strategic Emojis**: Use 3-5 relevant emojis MAXIMUM throughout the entire post (🤖 🚀 💡 🔥 ⚡ 🎯 🧠 💻). NO emoji overload. Space them naturally - one in the hook, one or two in the middle, one at the end if needed.
2. **Personal Voice**: Write like a real person, not ChatGPT or corporate marketing. Use conversational, authentic language.
3. **Value Over Flex**: Focus on teaching and explaining clearly. Avoid bragging or showing off. Make it useful for others.
4. **Simple Language**: Keep technical concepts simple enough for non-experts to understand, while maintaining depth for technical readers.

**TECHNICAL CONTENT (Maintain Depth):**
5. **Technical Depth**: Include specific technical details, architectures, models, frameworks, and methodologies
6. **Company & Technology References (CRITICAL)**: ALWAYS emphasize the specific tech giant mentioned (OpenAI, NVIDIA, Google, Microsoft, Meta, Apple, Amazon, Anthropic, etc.) and their specific products:
   - OpenAI: GPT-4, GPT-4 Turbo, ChatGPT, Sora, DALL-E, Whisper, API updates
   - NVIDIA: H100, A100, GH200, Blackwell, RTX GPUs, CUDA, AI chips, data center GPUs
   - Google: Gemini, Gemini Pro, DeepMind, AlphaGo, AlphaFold, PaLM, BERT, TensorFlow
   - Microsoft: Copilot, Azure AI, GPT-4 integration, Bing Chat, Microsoft 365 AI
   - Meta: Llama 2, Llama 3, OPT, AI research, PyTorch
   - Apple: CoreML, Neural Engine, Siri improvements, on-device AI
   - Amazon: Bedrock, Alexa AI, SageMaker, AWS AI services
   - Anthropic: Claude, Claude 3, Constitutional AI
   - Other: Tesla Dojo, X.AI Grok, etc.
7. **Hardware Focus**: If NVIDIA or hardware-related, emphasize GPU performance, chip architecture, compute capabilities, training infrastructure
8. **Technical Analysis**: Provide technical insights about:
   - Model architectures (transformer variants, attention mechanisms, MoE, etc.)
   - Training methodologies (RLHF, fine-tuning approaches, data pipelines)
   - Performance metrics (benchmarks, efficiency, latency, throughput)
   - Implementation details (scaling, optimization, deployment strategies)
   - Technical trade-offs and comparisons
**PERSONAL TOUCH (CRITICAL):**
- ALWAYS use first-person language: "I learned...", "I think...", "I'd build...", "I would use this to...", "This reminds me of when I..."
- **INCLUDE SIMILAR PROJECT EXPERIENCE**: If the news relates to projects you've worked on, mention them naturally:
  * "When I worked on [similar project/tool/technology], I encountered..."
  * "This reminds me of a project where I used [related technology]..."
  * "Having built [similar thing] using [technologies from profile], I can see how this would..."
  * "In my experience with [relevant skill/project], this would be useful for..."
- Reference your actual skills, projects, and experience from your profile when relevant
- Sound like a real human sharing insights, not an AI or corporate account
- Avoid phrases like "This is interesting" or "This matters" - be specific and personal
- Share your genuine thoughts and how you'd actually use this technology based on your experience

**STRUCTURE (MUST FOLLOW EXACTLY - MINIMUM LENGTHS ENFORCED):**
- Strong opening hook (1-2 lines) - curiosity-driven, attention-grabbing
- What happened (3-5 lines) - detailed summary with context, NOT just one line
- Why it matters (4-6 lines) - deep analysis with your thinking, NOT generic statements
- How I would use it / What I learned (3-5 lines) - specific personal connection, NOT generic phrases
- Engaging question (1-2 lines) - thought-provoking question that invites discussion
- Use white space between sections for readability
- **TOTAL POST LENGTH: Aim for 400-800 characters minimum (excluding hashtags) - make it substantial!**

**TONE:**
- Engaging, conversational, authentic human voice
- Professional yet approachable and exciting
- Technically accurate but accessible to non-experts
- Make readers feel like they're learning something fascinating
- Avoid corporate marketing speak or over-polished language
- Sound like you're talking to a colleague, not giving a presentation

**LENGTH REQUIREMENTS**: 
- Minimum: 400 characters (excluding hashtags) - make it substantial and detailed
- Maximum: {self.max_length} characters
- Each section must be fully developed, not just one or two sentences
- Avoid short, generic posts - expand on each point with detail and insight

Your Profile Information (use this to reference similar projects and experience):
{profile_context}

**IMPORTANT**: When writing the "HOW I WOULD USE IT / WHAT I LEARNED" section, actively look for connections between the article and your profile (skills, projects, expertise areas). If there's a relevant project or experience, mention it naturally. For example:
- If the article is about LLMs and you have NLP/LLM experience, mention a relevant project
- If it's about computer vision and you have CV skills, reference your experience
- If it's about a specific framework (PyTorch, TensorFlow) you've used, connect it to your work
- If it's about a tech giant's product you've worked with, mention your experience

Article Information:
Title: {title}
Description: {description}
Source: {source}
URL: {url}

CRITICAL INSTRUCTIONS:
- **FOLLOW THE EXACT STRUCTURE ABOVE** - What/Why/How/Question format with white space
- **MINIMUM LENGTH ENFORCED**: Post must be at least 400 characters (excluding hashtags). Each section must be fully developed.
- **EXPAND ON EVERY SECTION**: Do NOT write one-line summaries. Provide detail, context, and insight in each section.
- **STRONG OPENING HOOK** - First 1-2 lines must be curiosity-driven (see examples above)
- **NO MARKDOWN FORMATTING**: Use plain text only - do NOT use **bold**, __italic__, or any markdown syntax. LinkedIn doesn't support markdown.
- **EMOJI LIMIT**: Maximum 3-5 emojis total, spaced naturally. NO emoji overload.
- **PERSONAL VOICE**: Use "I learned...", "I think...", "I'd build..." - sound like a real person, not ChatGPT
- **INCLUDE SIMILAR PROJECT EXPERIENCE**: If applicable, reference your experience with similar projects, tools, or technologies from your profile. Connect the news to your actual work naturally and specifically.
- **AVOID GENERIC PHRASES**: Do NOT use generic statements like "I'd use this to explore new possibilities" or "This relates to my experience with Python". Be SPECIFIC about how it connects to your work, projects, or expertise.
- **DEEP ANALYSIS REQUIRED**: The "WHY IT MATTERS" section must provide substantial analysis, not just restate the news. Discuss implications, trends, challenges, or opportunities.
- **VALUE OVER FLEX**: Focus on teaching and explaining, not bragging
- **SIMPLE STRUCTURE**: Use white space between sections. No walls of text.
- Extract EVERY technical detail from the article (model names, companies, frameworks, metrics, architectures)
- Use exact technical terminology (e.g., "GPT-4 Turbo", "Claude 3 Opus", "Llama 3 70B", "NVIDIA H100", "Google Gemini Pro")
- ALWAYS identify and emphasize which tech giant is involved (OpenAI, NVIDIA, Google, Microsoft, Meta, etc.)
- Reference real AI companies and technologies with specific product names
- If NVIDIA-related, emphasize GPU specs, performance metrics, chip architecture, training capabilities
- Include specific technical metrics if mentioned
- Make it ENGAGING, SHAREABLE, and COMPELLING while maintaining technical depth
- **END WITH A QUESTION** - Must invite discussion (1-2 lines, not just one short question)
- **AVOID**: "Good morning LinkedIn", generic greetings, corporate speak, emoji overload, bragging, short generic posts, one-line sections

Write the LinkedIn post now. Do not include the URL in the post text (it will be added separately). Make it highly engaging, storytelling-style, with eye-catching heading and strategic emojis, while showcasing deep technical expertise."""

        return prompt

    def _generate_fallback_post(self, article: Dict) -> str:
        """Generate a simple fallback post if AI generation fails - follows checklist structure"""
        title = article.get('title', 'Interesting AI/ML Development')
        description = article.get('description', '')
        url = article.get('url', '')
        
        # Follow the checklist structure: Hook/What/Why/How/Question
        post = f"""This could change how we think about AI 🤖

{title}

{description[:250] if description else 'Interesting development in AI/ML that caught my attention.'}

I think this matters because it relates to my experience with {', '.join(self.profile.get('skills', ['AI/ML'])[:2])}. I'd use this to explore new possibilities in the field.

What are your thoughts on this? Let's discuss! 💡"""
        
        # Add hashtags at bottom (limit to 3-5)
        if self.include_hashtags and self.hashtags:
            limited_hashtags = self.hashtags[:5] if len(self.hashtags) > 5 else self.hashtags
            post += f"\n\n{' '.join(limited_hashtags)}"
        
        return post[:self.max_length]

