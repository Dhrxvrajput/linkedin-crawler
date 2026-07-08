SUMMARIZE_PROMPT = """Summarize the following LinkedIn post concisely in 3-4 sentences.

Post by {author_name} ({author_title}):
---
{content}
---

Respond in JSON format:
{{
    "summary": "3-4 sentence summary",
    "key_topics": ["topic1", "topic2"],
    "sentiment": "positive|neutral|negative"
}}"""

CLASSIFY_DOMAIN_PROMPT = """Classify the domain/industry of this LinkedIn post.

Summary: {summary}
Content: {content}

Choose from: technology, finance, healthcare, education, marketing, sales, product, design, operations, legal, other

Respond in JSON:
{{
    "domain": "category",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

DETECT_OPPORTUNITY_PROMPT = """Analyze this LinkedIn post for professional opportunities.

Post by {author_name}:
Summary: {summary}
Domain: {domain}
Content: {content}

Look for: job openings, hiring posts, collaboration requests, investment opportunities,
partnerships, speaking engagements, networking opportunities, project leads.

Respond in JSON:
{{
    "is_opportunity": true/false,
    "opportunity_type": "job|collaboration|investment|partnership|speaking|hiring|networking|other",
    "title": "short opportunity title",
    "description": "what the opportunity is",
    "confidence_score": 0.0-1.0,
    "action_items": ["suggested action 1", "suggested action 2"],
    "tags": ["tag1", "tag2"]
}}"""

ANALYZE_RELATIONSHIP_PROMPT = """Analyze the relationship between the user and this LinkedIn post author.

User profile:
- Name: {user_name}
- Title: {user_title}
- Company: {user_company}
- Interests: {user_interests}
- Skills: {user_skills}

Post author:
- Name: {author_name}
- Title: {author_title}
- Company: {author_company}

Post summary: {summary}

Respond in JSON:
{{
    "relationship_type": "direct_connection|second_degree|mutual_interest|industry_peer|unknown",
    "relevance_score": 0.0-1.0,
    "mutual_connections": 0,
    "shared_interests": ["interest1"],
    "reasoning": "brief explanation"
}}"""

SCORE_RELEVANCE_PROMPT = """Score how relevant this opportunity is for the user.

User profile:
- Name: {user_name}
- Title: {user_title}
- Company: {user_company}
- Interests: {user_interests}
- Skills: {user_skills}

Opportunity:
- Title: {title}
- Type: {opportunity_type}
- Description: {description}
- Domain: {domain}
- Author: {author_name}
- Relationship: {relationship_type}

Respond in JSON:
{{
    "relevance_score": 0.0-1.0,
    "reasoning": "why this is or isn't relevant",
    "recommended_actions": ["action1", "action2"]
}}"""

GENERATE_DIGEST_PROMPT = """Create a professional daily digest of LinkedIn opportunities.

User: {user_name} ({user_title} at {user_company})

Top opportunities:
{opportunities_text}

Write a concise, actionable digest (3-5 paragraphs) highlighting:
1. Top opportunities ranked by relevance
2. Key people to connect with
3. Recommended actions for today

Use a professional but friendly tone."""

GENERATE_CONGRATS_COMMENT_PROMPT = """Write one short LinkedIn congratulatory comment.

Post by {author_name} ({author_title}):
Summary: {summary}
Content: {content}

Rules:
- 1 sentence only
- max {max_chars} characters
- natural, human tone
- no hashtags
- no emojis
- no generic AI wording

Respond in JSON:
{{
    "comment": "comment based on the post "
}}"""
