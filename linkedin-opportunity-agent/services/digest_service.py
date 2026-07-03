from datetime import datetime
from pathlib import Path

from config.settings import get_settings
from database.crud import get_latest_digest, get_opportunities
from database.db import get_db
from services.opportunity_service import OpportunityService
from utils.helpers import ensure_dir


class DigestService:
    def __init__(self):
        self.settings = get_settings()
        self.opp_service = OpportunityService()

    def get_latest(self) -> str | None:
        with get_db() as db:
            digest = get_latest_digest(db)
            return digest.content if digest else None

    def generate_summary(self, top_n: int | None = None) -> str:
        top_n = top_n or self.settings.digest_top_n
        opps = self.opp_service.get_top(n=top_n)

        if not opps:
            return "No opportunities found yet. Run the agent to scan your LinkedIn feed."

        lines = [
            f"# LinkedIn Opportunity Digest",
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"Top {len(opps)} opportunities:\n",
        ]

        for i, opp in enumerate(opps, 1):
            lines.append(f"## {i}. {opp.title}")
            lines.append(f"**Score:** {opp.relevance_score:.2f} | **Type:** {opp.opportunity_type}")
            lines.append(f"**Author:** {opp.author_name}")
            lines.append(f"{opp.description}")
            if opp.action_items:
                lines.append("**Actions:**")
                for action in opp.action_items:
                    lines.append(f"- {action}")
            lines.append("")

        return "\n".join(lines)

    def export_digest(self, content: str | None = None) -> Path:
        content = content or self.generate_summary()
        export_dir = ensure_dir(self.settings.export_dir)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = Path(export_dir) / f"digest_{timestamp}.md"
        path.write_text(content)
        return path
