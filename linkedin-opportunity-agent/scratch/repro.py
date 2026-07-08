
import asyncio
from typing import Optional
from pydantic import BaseModel

class PostAuthor(BaseModel):
    name: str

class PostSchema(BaseModel):
    author: PostAuthor
    summary: Optional[str] = None

posts = [
    PostSchema(author=PostAuthor(name="Alice"), summary="Hello world"),
    PostSchema(author=PostAuthor(name="Bob"), summary=None),
]

result = {"posts": posts}

sample = [
    {
        "author": p.author.name if hasattr(p, "author") else p.get("author_name", "Unknown"),
        "summary": ((p.summary if hasattr(p, "summary") else p.get("summary", "")) or "")[:80],
    }
    for p in result.get("posts", [])[:3]
]
print(sample)
