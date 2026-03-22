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
        """Generate a LinkedIn post from a news article or blog post"""
        # Route blog posts to the dedicated blog post generator
        if article.get('content_type') == 'blog':
            return self.generate_blog_post(article)

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

    def generate_multi_article_post(self, articles: List[Dict]) -> str:
        """
        Generate a storytelling LinkedIn post from multiple articles
        
        Args:
            articles: List of article dictionaries (minimum 3 recommended)
        
        Returns:
            Generated post content
        """
        if len(articles) < 2:
            logger.warning("Multi-article post requires at least 2 articles. Using single article mode.")
            return self.generate_post(articles[0])
        
        # Build context about the user
        profile_context = self._build_profile_context()
        
        # Build the storytelling prompt
        prompt = self._build_storytelling_prompt(articles, profile_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional tech content creator and AI/ML expert with deep industry knowledge. You create compelling storytelling LinkedIn posts that weave multiple news articles into cohesive narratives. Your posts are authoritative, insightful, and provide real value. You write like a thought leader who connects the dots between different developments in AI/ML. You focus on major tech giants (OpenAI, NVIDIA, Google, Microsoft, Meta, Apple, Amazon, Anthropic, etc.) and their products. Your writing style is professional, engaging, and educational - you tell stories that teach while they inform. You use strategic emojis (6-10 total) and structure posts for maximum readability with clear sections and white space."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.75,
                max_tokens=3000  # Increased for multi-article storytelling
            )
            
            post_content = response.choices[0].message.content.strip()
            
            # Check minimum length
            min_length = 1000  # Multi-article posts should be longer
            post_without_hashtags = post_content
            if self.include_hashtags and self.hashtags:
                for tag in self.hashtags:
                    post_without_hashtags = post_without_hashtags.replace(tag, '')
            
            if len(post_without_hashtags.strip()) < min_length:
                logger.warning(f"Generated multi-article post is shorter than recommended minimum ({len(post_without_hashtags)} chars). Minimum recommended: {min_length} chars.")
            
            # Add hashtags if enabled
            if self.include_hashtags and self.hashtags:
                limited_hashtags = self.hashtags[:7] if len(self.hashtags) > 7 else self.hashtags
                hashtag_string = " ".join(limited_hashtags)
                post_content = f"{post_content}\n\n{hashtag_string}"
            
            # Ensure length is within limits
            if len(post_content) > self.max_length:
                post_content = post_content[:self.max_length-3] + "..."
            
            return post_content
            
        except Exception as e:
            logger.error(f"Error generating multi-article post: {e}")
            # Fallback to single article mode
            return self.generate_post(articles[0])

    def generate_blog_post(self, blog_post: Dict) -> str:
        """
        Generate an engaging LinkedIn post promoting a personal blog article.
        Highlights the author's profile, shares key insights, and invites the
        audience to read, connect, follow the blog, and engage.
        """
        profile_context = self._build_profile_context()
        prompt = self._build_blog_prompt(blog_post, profile_context)

        blog_config = self.config.get('blog', {})
        author_name = blog_config.get('author_name', self.profile.get('name', 'the author'))
        linkedin_url = blog_config.get('linkedin_url', '')
        blog_site_url = blog_config.get('url', 'https://www.abhisheksagarsanda.com/blog')

        role_line = self.profile.get('title') or self.profile.get('current_role') or 'AI Engineer and educator'
        system_prompt = (
            f"You are a personal brand content strategist and LinkedIn ghostwriter for {author_name}, "
            f"whose professional positioning is: {role_line}. Your goal is to write authentic, knowledgeable LinkedIn posts "
            "that showcase the author's deep expertise, provide genuine value to the reader, and organically "
            "invite the audience to connect, follow the blog, and engage. "
            "Your writing feels like a brilliant colleague sharing hard-won knowledge — not marketing copy. "
            "You create curiosity, demonstrate credibility, and leave the reader wanting more. "
            "You use a warm, confident, and intellectually stimulating tone. "
            "Posts are long-form (900-2000 characters), structured for easy reading with short paragraphs "
            "and strategic white space, use 3-6 emojis sparingly, and end with a thought-provoking question."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.78,
                max_tokens=2800,
            )
            post_content = response.choices[0].message.content.strip()

            if len(post_content) < 700:
                logger.warning(f"Blog post too short ({len(post_content)} chars), consider re-generating.")

            # Append blog-specific hashtags if configured, otherwise use defaults
            if self.include_hashtags:
                blog_hashtags = blog_config.get('hashtags', self.hashtags)
                limited = blog_hashtags[:7] if len(blog_hashtags) > 7 else blog_hashtags
                post_content = f"{post_content}\n\n{' '.join(limited)}"

            if len(post_content) > self.max_length:
                post_content = post_content[:self.max_length - 3] + "..."

            return post_content

        except Exception as e:
            logger.error(f"Error generating blog post: {e}")
            return self._generate_fallback_blog_post(blog_post)

    def generate_multi_blog_post(self, blog_posts: List[Dict]) -> str:
        """
        Generate a storytelling LinkedIn post weaving together multiple personal blog posts.
        Useful for weekly roundups or thematic series.
        """
        if len(blog_posts) < 2:
            return self.generate_blog_post(blog_posts[0])

        profile_context = self._build_profile_context()
        prompt = self._build_blog_storytelling_prompt(blog_posts, profile_context)

        blog_config = self.config.get('blog', {})
        author_name = blog_config.get('author_name', self.profile.get('name', 'the author'))

        system_prompt = (
            f"You are a personal brand content strategist for {author_name}, an AI Engineer. "
            "Write a compelling LinkedIn post that weaves together multiple blog articles into a cohesive "
            "narrative. The post should feel like an author sharing a journey of discovery — not a listicle. "
            "Demonstrate deep expertise, spark curiosity, and warmly invite readers to connect and explore "
            "the full articles. Use authentic first-person voice, 5-8 emojis strategically, and end with "
            "an engaging question that sparks discussion."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.78,
                max_tokens=3200,
            )
            post_content = response.choices[0].message.content.strip()

            if self.include_hashtags:
                blog_hashtags = blog_config.get('hashtags', self.hashtags)
                limited = blog_hashtags[:7] if len(blog_hashtags) > 7 else blog_hashtags
                post_content = f"{post_content}\n\n{' '.join(limited)}"

            if len(post_content) > self.max_length:
                post_content = post_content[:self.max_length - 3] + "..."

            return post_content

        except Exception as e:
            logger.error(f"Error generating multi-blog post: {e}")
            return self.generate_blog_post(blog_posts[0])

    def _build_blog_prompt(self, blog_post: Dict, profile_context: str) -> str:
        """Build the prompt for a single blog post promotion."""
        title = blog_post.get('title', 'My Latest Blog Post')
        description = blog_post.get('description', '')
        url = blog_post.get('url', '')
        tags = blog_post.get('tags', [])
        tags_str = ", ".join(tags) if tags else "AI, Machine Learning, LLM"
        published_at = blog_post.get('published_at', '')

        blog_config = self.config.get('blog', {})
        author_name = blog_config.get('author_name', self.profile.get('name', 'I'))
        blog_site_url = blog_config.get('url', 'https://www.abhisheksagarsanda.com/blog')
        linkedin_url = blog_config.get('linkedin_url', '')

        connect_line = ""
        if linkedin_url:
            connect_line = f"\n- Invite readers to connect with {author_name} on LinkedIn: {linkedin_url}"

        prompt = f"""Write an engaging, knowledgeable LinkedIn post that promotes this personal blog article written by {author_name}.

**YOUR CORE MISSION:**
Make this post so insightful and valuable that readers immediately want to:
1. Read the full blog article (link included)
2. Follow {author_name}'s blog for more expertise
3. Connect with {author_name} on LinkedIn
4. Comment with their thoughts or questions
5. Share this post with their network

**CRITICAL: FIRST 2 LINES ARE EVERYTHING**
LinkedIn only shows the first 2 lines before "...see more". These lines MUST create irresistible curiosity about the blog topic.

---

**MANDATORY POST STRUCTURE (output ONLY smooth prose — NO section headers, NO numbers):**

**1. POWERFUL HOOK (EXACTLY 2 LINES — NO markdown, NO bold)**
- Open with a provocative statement, surprising insight, or bold claim from the blog
- Second line deepens the intrigue or adds a surprising twist
- Use 1-2 emojis strategically (never in both lines)
- Make the reader FEEL they will miss something if they scroll past
- Example hooks:
  * "Most engineers are building RAG systems wrong. And I wrote a 15-minute deep-dive to prove it."
  * "I spent 3 months benchmarking every major LLM evaluation framework. The results shocked me. 🧠"
  * "The transformer architecture has a dirty secret that most tutorials skip over."
- Add blank line after

**2. WHAT THIS ARTICLE IS ABOUT (3-4 lines)**
- Give a crisp, compelling overview of the blog post's core idea
- Mention the specific problem it solves or question it answers
- Use the blog's topic/tags naturally: {tags_str}
- Keep it conversational — like you're telling a smart colleague what you wrote
- Add blank line after

**3. 3-4 KEY INSIGHTS (each as a short punchy paragraph, 2-3 lines each)**
- Extract the most valuable, non-obvious insights from the blog's title and description
- Each insight should feel like a mini-revelation — something the reader didn't know or hadn't thought about
- Ground each insight in real-world AI/ML practice or genuine technical depth
- Reference specific concepts, techniques, or frameworks relevant to: {tags_str}
- Keep paragraphs to 2-3 lines max for easy scanning
- Add blank line between each insight

**4. AUTHOR SPOTLIGHT (2-3 lines)**
- Introduce {author_name} naturally and credibly (not as a sales pitch)
- Reference their profile: {profile_context}
- Mention the blog ({blog_site_url}) as a resource for engineers who want to stay ahead in AI
- Sound proud but humble — like a friend vouching for someone brilliant
- Add blank line after

**5. CALL-TO-ACTION (3-4 lines)**
- Invite readers to: read the full article at {url}
- Invite them to follow the blog for weekly deep-dives on AI/LLMs/ML engineering
- Warmly invite connections: "If you're building with AI or want to exchange ideas, let's connect"{connect_line}
- Make the CTA feel natural and generous — not pushy or salesy
- Add blank line after

**6. ENGAGING QUESTION (1-2 lines)**
- End with a thought-provoking question that directly relates to the blog topic
- Make it specific enough that experts will have opinions: NOT "What do you think?" but something like "Are you using sparse attention in production yet, or still on full attention?"
- This is the spark for comments and discussion

---

**WRITING REQUIREMENTS:**
- MINIMUM LENGTH: 900 characters (excluding hashtags) — make it substantial and worth reading
- TARGET LENGTH: 1200-1800 characters
- MAXIMUM LENGTH: {self.max_length} characters
- Emojis: 3-6 total, placed naturally — never clustered together
- Paragraph length: 2-4 lines max — no walls of text
- White space: blank line between each section for readability
- NO markdown formatting (LinkedIn shows it as raw text)
- First person voice throughout ("I wrote", "In my research", "I discovered")
- Authoritative yet approachable — like a knowledgeable friend, not a corporation
- Technically substantive — reference real AI/ML concepts, not just buzzwords
- Authentic: avoid phrases like "game-changer", "delve into", "it's important to note"

**BLOG POST INFORMATION:**
Title: {title}
Description: {description}
URL: {url}
Topics/Tags: {tags_str}
Published: {published_at}

**AUTHOR PROFILE:**
{profile_context}

Write the complete LinkedIn post now. Output ONLY the post content — clean prose, no headers, no section labels, no bullet points. The blog URL should be mentioned naturally in the CTA section."""

        return prompt

    def _build_blog_storytelling_prompt(self, blog_posts: List[Dict], profile_context: str) -> str:
        """Build a storytelling prompt for multiple blog posts (e.g. weekly roundup)."""
        blog_config = self.config.get('blog', {})
        author_name = blog_config.get('author_name', self.profile.get('name', 'I'))
        blog_site_url = blog_config.get('url', 'https://www.abhisheksagarsanda.com/blog')
        linkedin_url = blog_config.get('linkedin_url', '')

        posts_info = []
        for i, post in enumerate(blog_posts, 1):
            tags = ", ".join(post.get('tags', []))
            posts_info.append(
                f"Article {i}:\n"
                f"- Title: {post.get('title', '')}\n"
                f"- Description: {post.get('description', '')}\n"
                f"- URL: {post.get('url', '')}\n"
                f"- Topics: {tags or 'AI/ML'}"
            )
        posts_text = "\n\n".join(posts_info)

        connect_line = f"\n- Invite connections on LinkedIn: {linkedin_url}" if linkedin_url else ""

        prompt = f"""Write an engaging LinkedIn post from {author_name} that weaves together {len(blog_posts)} recent blog articles into a compelling narrative — like an author sharing the thread connecting their latest work.

**YOUR GOAL:**
Make readers feel the intellectual excitement of following {author_name}'s blog journey. Create FOMO — they should feel they're missing out on critical AI knowledge by not following. Invite genuine engagement.

**CRITICAL: FIRST 2 LINES — Make them unforgettable**
Hook the reader with the unifying theme connecting all these articles.

---

**STRUCTURE (output ONLY smooth prose, NO headers, NO bullets, NO section labels):**

1. HOOK (2 lines): Bold opening that captures the connecting theme across these articles. 1-2 emojis.
(blank line)

2. THE THREAD (3-4 lines): What pattern or journey connects these pieces? Why are they writing about this now? Create narrative momentum.
(blank line)

3. ARTICLE HIGHLIGHTS (weave naturally, 2-3 lines per article):
For each article: share the most surprising or valuable insight, reference its URL naturally as "read more here: [url]" or "full breakdown at [url]"
(blank line between each)

4. THE BIGGER PICTURE (3-4 lines): What does the totality of this work reveal about the direction of AI/ML? Show the thought leadership.
(blank line)

5. AUTHOR & BLOG SPOTLIGHT (2-3 lines):
- About {author_name}: {profile_context}
- The blog ({blog_site_url}) publishes deep-dives for engineers who want to build better AI systems
(blank line)

6. CTA (3-4 lines):
- Follow the blog for weekly expert content
- Connect with {author_name} to exchange ideas{connect_line}
- Invite readers to share which topic resonates most
(blank line)

7. ENGAGING QUESTION (1-2 lines): Spark debate or reflection about the themes covered.

---

**REQUIREMENTS:**
- MINIMUM LENGTH: 1100 characters (excluding hashtags)
- TARGET LENGTH: 1500-2200 characters
- Emojis: 5-8 total, spaced naturally
- NO markdown formatting
- Authentic first-person voice
- Technically substantive — real insights, not vague buzzwords
- Short paragraphs (2-4 lines max), blank line between sections

**BLOG ARTICLES:**
{posts_text}

**AUTHOR PROFILE:**
{profile_context}

Write the complete LinkedIn post now. Output ONLY the post content — no headers, no section labels."""

        return prompt

    def _generate_fallback_blog_post(self, blog_post: Dict) -> str:
        """Simple fallback post when AI generation fails."""
        title = blog_post.get('title', 'My Latest Blog Post')
        description = blog_post.get('description', '')
        url = blog_post.get('url', '')
        tags = blog_post.get('tags', [])
        tags_str = " ".join(f"#{t.replace(' ', '')}" for t in tags[:5]) if tags else "#AI #MachineLearning"
        author_name = self.config.get('blog', {}).get('author_name', self.profile.get('name', ''))
        blog_url = self.config.get('blog', {}).get('url', 'https://www.abhisheksagarsanda.com/blog')

        post = f"""🧠 Just published a new deep-dive: {title}

{description[:350] if description else ''}

If you're working with AI systems, this one's worth 15 minutes of your time.

👉 Read the full article: {url}

I write practical, in-depth content on AI engineering, LLMs, and production ML systems at {blog_url} — designed for engineers who want to build smarter, not just faster.

Follow along if this is the kind of content you want more of. And if you're building in the AI space, I'd love to connect and exchange ideas.

What's your current biggest challenge with {tags[0] if tags else 'AI systems'}?

{tags_str}"""

        if self.include_hashtags and self.hashtags:
            post += f"\n{' '.join(self.hashtags[:5])}"

        return post[:self.max_length]

    def _build_profile_context(self) -> str:
        """Build a context string about the user's profile (resume-aware)."""
        context_parts = []

        if self.profile.get('name'):
            context_parts.append(f"Name: {self.profile['name']}")

        if self.profile.get('location'):
            context_parts.append(f"Location: {self.profile['location']}")

        if self.profile.get('title'):
            context_parts.append(f"Professional title / headline: {self.profile['title']}")

        if self.profile.get('current_role'):
            context_parts.append(f"Current role(s): {self.profile['current_role']}")

        if self.profile.get('professional_summary'):
            summary = str(self.profile['professional_summary']).strip()
            if len(summary) > 1400:
                summary = summary[:1397] + "..."
            context_parts.append(f"Professional summary: {summary}")

        if self.profile.get('portfolio_url'):
            context_parts.append(f"Portfolio / website: {self.profile['portfolio_url']}")

        if self.profile.get('skills'):
            skills = ", ".join(self.profile['skills'])
            context_parts.append(f"Technical skills: {skills}")

        if self.profile.get('experience_years') is not None:
            context_parts.append(f"Years of relevant experience: {self.profile['experience_years']}")

        if self.profile.get('expertise_areas'):
            expertise = ", ".join(self.profile['expertise_areas'])
            context_parts.append(f"Expertise areas: {expertise}")

        if self.profile.get('notable_metrics'):
            metrics = self.profile['notable_metrics']
            if isinstance(metrics, list):
                for m in metrics:
                    context_parts.append(f"Impact / proof point: {m}")

        if self.profile.get('credentials'):
            creds = self.profile['credentials']
            if isinstance(creds, list):
                context_parts.append("Credentials & leadership: " + "; ".join(creds))

        if self.profile.get('publications'):
            pubs = self.profile['publications']
            if isinstance(pubs, list):
                context_parts.append("Publications & talks: " + "; ".join(pubs))

        # Add education information
        if self.profile.get('education'):
            edu = self.profile['education']
            edu_str = f"Education: {edu.get('degree', '')} from {edu.get('university', '')}"
            if edu.get('gpa'):
                edu_str += f" (GPA: {edu['gpa']})"
            context_parts.append(edu_str)

            if edu.get('achievements'):
                achievements = ", ".join(edu['achievements'])
                context_parts.append(f"Academic highlights: {achievements}")

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

**MANDATORY STRUCTURE (Follow this flow in your writing - but output ONLY smooth prose, NO section headers or numbers):**

**CRITICAL OUTPUT RULE**: Write ONLY the post content as flowing prose. Do NOT include section numbers (1., 2., 3.), section labels (COMPELLING HEADLINE, THE NEWS, etc.), or bullet-point dashes in your output. The reader should see a clean LinkedIn post, not an outline.

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

Write the complete LinkedIn post now. Output ONLY the post content as clean prose - no section numbers, no headers like "COMPELLING HEADLINE" or "THE NEWS", no bullet formatting. Do not include the URL in the post text."""

        return prompt

    def _build_storytelling_prompt(self, articles: List[Dict], profile_context: str) -> str:
        """Build the storytelling prompt for multi-article posts"""
        
        # Format articles information
        articles_info = []
        for i, article in enumerate(articles, 1):
            articles_info.append(f"""
Article {i}:
- Title: {article.get('title', 'No title')}
- Source: {article.get('source', 'Unknown')}
- Description: {article.get('description', 'No description')}
- URL: {article.get('url', '')}
""")
        
        articles_text = "\n".join(articles_info)
        
        prompt = f"""Create a compelling storytelling LinkedIn post (1000-2500 characters, excluding hashtags) that weaves together {len(articles)} news articles into a cohesive narrative. This is NOT just summarizing articles - you're creating a story that connects them.

**CRITICAL: FIRST 2 LINES ARE EVERYTHING**
LinkedIn only shows the first 2 lines in the feed. Make them count with a curiosity-driven hook that introduces the connecting theme!

**MANDATORY STORYTELLING STRUCTURE (Follow this flow - output ONLY smooth prose, NO section headers or numbers):**

**CRITICAL OUTPUT RULE**: Write ONLY the post content as flowing prose. Do NOT include section numbers (1., 2., 3.), section labels (EYE-CATCHING HEADING, OPENING, etc.), or bullet-point dashes. Output a clean LinkedIn post, not an outline.

1. **EYE-CATCHING HEADING (EXACTLY 2 LINES - NO MARKDOWN!)**
   - Line 1: Curiosity-driven hook that introduces the overarching theme connecting all articles
   - Line 2: Continue the hook or add context that builds intrigue
   - Use 2-3 strategic emojis (one in first line recommended)
   - NO markdown formatting (no **bold**, __italic__)
   - Must introduce the connecting theme/narrative
   - Examples:
     * "Three major AI developments just dropped this week. Here's the pattern most people are missing..."
     * "OpenAI, NVIDIA, and Google all made announcements. But the real story is what connects them..."
   - Add blank line after

2. **OPENING - INTRODUCE THE CONNECTING THEME (3-5 lines)**
   - What's the overarching theme or pattern connecting these articles?
   - Why are these developments happening together?
   - Set up the narrative arc
   - Reference sources naturally: "According to TechCrunch...", "Reuters reports...", "The Verge notes...", "Hacker News discussion highlights..."
   - Add blank line after

3. **DEVELOPMENT - WEAVE ARTICLES TOGETHER (8-12 lines, 2-4 lines per paragraph)**
   - Weave together insights from each article
   - Show how articles complement each other
   - Highlight interesting connections, contrasts, or patterns
   - Reference each source naturally as you discuss their article
   - Use specific product names: GPT-4 Turbo, NVIDIA H100, Google Gemini Pro, Claude 3 Opus, Llama 3 70B
   - Include technical details: model architectures, training methodologies, performance metrics
   - Keep paragraphs short (2-4 lines max) for readability
   - Add blank line after

4. **CONNECTION POINTS - SHOW THE BIGGER PICTURE (5-8 lines, 2-4 lines per paragraph)**
   - What patterns emerge when you look at all articles together?
   - How do these developments relate to each other?
   - What's the bigger picture or trend?
   - Industry implications: How does this affect the AI/ML landscape?
   - Competitive dynamics: How do these relate to each other?
   - Keep paragraphs short (2-4 lines max)
   - Add blank line after

5. **TECHNICAL DEEP DIVE (6-10 lines, 2-4 lines per paragraph)**
   - Architecture details: How do these technologies work?
   - Performance metrics: Benchmarks, speed, efficiency, scale
   - Technical innovations: What's new or different?
   - Framework references: PyTorch, TensorFlow, JAX, HuggingFace
   - Training methodologies: RLHF, fine-tuning approaches, MoE architectures
   - Implementation considerations: What does it take to use these?
   - Keep paragraphs short (2-4 lines max)
   - Add blank line after

6. **PERSONAL INSIGHT / EXPERIENCE (4-6 lines)**
   - Weave in your experience naturally: "In my work with {', '.join(self.profile.get('skills', ['AI/ML'])[:3])}..."
   - "Having fine-tuned models like GPT-4 and LLaMA..."
   - "When I deployed {self.profile.get('expertise_areas', ['AI systems'])[0]}..."
   - Share relevant insights from your expertise
   - Connect to your expertise areas
   - Use storytelling phrases: "This reminded me of...", "In my experience...", "Having worked with..."
   - Sound authentic and personal, NOT like ChatGPT
   - Add blank line after

7. **CONCLUSION - FORWARD-LOOKING THOUGHTS (3-5 lines)**
   - What does this mean for the future?
   - What are the implications?
   - What should we watch for next?
   - Add blank line after

8. **ENGAGING QUESTION/CTA (1-2 lines)**
   - Thought-provoking question that invites discussion
   - Make it specific and engaging
   - Examples: "What patterns are you seeing in AI development?" or "How do you think these developments will converge?"

**TECH GIANTS & PRODUCTS TO EMPHASIZE:**
- OpenAI: GPT-4, GPT-4 Turbo, ChatGPT, Sora, DALL-E, Whisper, API updates
- NVIDIA: H100, A100, GH200, Blackwell, RTX GPUs, CUDA, AI chips
- Google: Gemini, Gemini Pro/Ultra, DeepMind, AlphaGo, AlphaFold, PaLM, BERT, TensorFlow
- Microsoft: Copilot, Azure AI, GPT-4 integration, Bing Chat, Azure OpenAI
- Meta: Llama 2, Llama 3, OPT, AI research, PyTorch
- Apple: CoreML, Neural Engine, Siri, MLX framework
- Amazon: Bedrock, Alexa AI, SageMaker, AWS AI services
- Anthropic: Claude, Claude 3 (Opus/Sonnet/Haiku), Constitutional AI
- Others: Tesla Dojo, X.AI Grok, Mistral AI, Cohere

**STORYTELLING REQUIREMENTS:**
- Create a NARRATIVE ARC: opening → development → connections → personal insight → conclusion
- Weave articles together naturally - don't just list them
- Reference sources naturally as you discuss their content
- Show connections and patterns between articles
- Maintain technical depth while being engaging
- Use 6-10 strategic emojis total, spaced naturally (🤖 🚀 💡 🔥 ⚡ 🎯 🧠 💻 🎨 🔬)
- NO markdown formatting anywhere (LinkedIn doesn't support it)
- Paragraph length: 2-4 lines maximum (no walls of text)
- White space: Blank line between each major section
- MINIMUM LENGTH: 1000 characters (excluding hashtags)
- TARGET LENGTH: 1500-2200 characters for optimal engagement
- MAXIMUM LENGTH: {self.max_length} characters

**TONE & STYLE:**
- Professional tech content creator voice
- Storytelling approach - create a narrative, not just summaries
- Educational and valuable (teach, don't just inform)
- Engaging but professional
- Technical depth without being inaccessible
- Authentic human voice (sound like you're talking to a colleague)
- Value-first approach (every section should add value)

Your Profile Information:
{profile_context}

Articles to Synthesize:
{articles_text}

**CRITICAL CHECKLIST:**
- ✅ FIRST 2 LINES: Curiosity-driven hook introducing connecting theme (NO MARKDOWN!)
- ✅ Create a cohesive NARRATIVE, not just article summaries
- ✅ Reference sources naturally ("According to TechCrunch...", "Reuters reports...")
- ✅ Show connections and patterns between articles
- ✅ Weave in personal experience authentically
- ✅ Include technical depth (specific models, frameworks, metrics)
- ✅ MINIMUM 1000 characters (excluding hashtags)
- ✅ Paragraphs: 2-4 lines maximum
- ✅ White space: Blank line between sections
- ✅ Strategic emojis: 6-10 total, spaced naturally
- ✅ NO markdown formatting anywhere
- ✅ Engaging question: End with thought-provoking CTA

Write the complete storytelling LinkedIn post now. Output ONLY the post content as clean prose - no section numbers, no headers like "OPENING" or "DEVELOPMENT", no bullet formatting. Do not include URLs in the post text."""

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

