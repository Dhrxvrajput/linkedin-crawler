from enum import Enum


class OpportunityType(str, Enum):
    JOB = "job"
    COLLABORATION = "collaboration"
    INVESTMENT = "investment"
    PARTNERSHIP = "partnership"
    SPEAKING = "speaking"
    HIRING = "hiring"
    NETWORKING = "networking"
    OTHER = "other"


class DomainCategory(str, Enum):
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    MARKETING = "marketing"
    SALES = "sales"
    PRODUCT = "product"
    DESIGN = "design"
    OPERATIONS = "operations"
    LEGAL = "legal"
    OTHER = "other"


class RelationshipType(str, Enum):
    DIRECT_CONNECTION = "direct_connection"
    SECOND_DEGREE = "second_degree"
    MUTUAL_INTEREST = "mutual_interest"
    INDUSTRY_PEER = "industry_peer"
    UNKNOWN = "unknown"


class PostStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"


class OpportunityStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    ACTIONED = "actioned"
    DISMISSED = "dismissed"


# LinkedIn selectors (may need updating as LinkedIn changes its DOM)
LINKEDIN_SELECTORS = {
    "feed_container": "div.scaffold-finite-scroll__content",
    "post_card": "div.feed-shared-update-v2",
    "post_author": "span.update-components-actor__name",
    "post_text": "div.feed-shared-update-v2__description",
    "post_time": "span.update-components-actor__sub-description",
    "post_reactions": "span.social-details-social-counts__reactions-count",
    "post_comments": "button.social-details-social-counts__comments",
    "login_email": "#username",
    "login_password": "#password",
    "login_submit": "button[type='submit']",
}

# Graph node names
NODE_FETCH_POSTS = "fetch_posts"
NODE_CHECK_CACHE = "check_cache"
NODE_FILTER_RELEVANCE = "filter_relevance"
NODE_SUMMARIZE = "summarize"
NODE_CLASSIFY_DOMAIN = "classify_domain"
NODE_DETECT_OPPORTUNITIES = "detect_opportunities"
NODE_ANALYZE_RELATIONSHIPS = "analyze_relationships"
NODE_SCORE_RELEVANCE = "score_relevance"
NODE_SKIP_POST = "skip_post"
NODE_SAVE_TO_DB = "save_to_db"
NODE_GENERATE_DIGEST = "generate_digest"
