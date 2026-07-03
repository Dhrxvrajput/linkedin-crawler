# LinkedIn Opportunity Agent

An AI-powered agent that scans your LinkedIn feed, detects professional opportunities, scores their relevance to your profile, and delivers actionable daily digests.

## Architecture

```
LinkedIn Feed → Crawler → LangGraph Pipeline → SQLite DB → Streamlit Dashboard
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
               Summarize  Classify  Detect
                          Domain   Opportunities
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
              Analyze    Score      Save
           Relationships Relevance   to DB
                              │
                              ▼
                        Generate Digest
```

## Pipeline Nodes

1. **fetch_posts** — Scrapes LinkedIn feed using Playwright
2. **summarize** — Summarizes each post with Groq (Llama)
3. **classify_domain** — Classifies post domain/industry
4. **detect_opportunities** — Identifies jobs, collaborations, partnerships, etc.
5. **analyze_relationships** — Analyzes your relationship with post authors
6. **score_relevance** — Scores opportunity relevance to your profile
7. **save_to_db** — Persists results to SQLite
8. **generate_digest** — Creates an actionable daily digest

## Setup

### 1. Install dependencies

```bash
cd linkedin-opportunity-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

Edit `.env` with your credentials:

```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
USER_NAME=Your Name
USER_TITLE=Your Job Title
USER_COMPANY=Your Company
USER_INTERESTS=AI,startups,product
USER_SKILLS=Python,leadership,strategy
```

### 3. Initialize database

```bash
python -c "from database.db import setup_database; setup_database()"
```

## Usage

### Run the agent (CLI)

```bash
python app.py
python app.py --max-posts 20
```

### Launch dashboard

```bash
python app.py --dashboard
# or
streamlit run dashboard/streamlit_app.py
```

### Dashboard pages

- **Home** — Overview, metrics, run agent
- **Opportunities** — Browse and manage detected opportunities
- **People Radar** — Track relevant people from your feed
- **Research** — Browse posts, view digests, export
- **Settings** — View configuration

## Project Structure

```
linkedin-opportunity-agent/
├── app.py                  # CLI entry point
├── config/                 # Settings and constants
├── graph/                  # LangGraph workflow
├── nodes/                  # Pipeline node implementations
├── linkedin/               # LinkedIn crawler and auth
├── llm/                    # Groq integration and prompts
├── database/               # SQLAlchemy models and CRUD
├── services/               # Business logic layer
├── dashboard/              # Streamlit UI
├── schemas/                # Pydantic data models
├── utils/                  # Helpers and utilities
├── storage/                # Sessions, exports, database
└── tests/                  # Unit tests
```

## Notes

- LinkedIn may trigger security challenges on first login. Run `python app.py --login` once (opens a browser) to sign in. After that, crawls run headless in the background.
- Session cookies are saved to `storage/sessions/linkedin.json` for reuse.
- Digests are exported to `storage/exports/`.
- LinkedIn DOM selectors may need updating as LinkedIn changes its UI.

## License

MIT
