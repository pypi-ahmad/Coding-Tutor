"""Bounded Firecrawl MCP search used only as question-generation context."""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from typing import Any

FIRECRAWL_MCP_URL = "https://mcp.firecrawl.dev/v2/mcp"
MAX_RESULTS = 5
MAX_SCRAPES = 3
MAX_SOURCE_CHARS = 6_000


class WebResearchError(RuntimeError):
    pass


@dataclass(frozen=True)
class WebSource:
    title: str
    url: str
    excerpt: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def firecrawl_access_mode() -> str:
    return "authenticated" if os.environ.get("FIRECRAWL_API_KEY", "").strip() else "keyless"


def _json_content(result: Any) -> Any:
    texts = [getattr(block, "text", "") for block in getattr(result, "content", [])]
    raw = "\n".join(text for text in texts if text).strip()
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"data": [{"title": "Web result", "url": "", "description": raw}]}


def _rows(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "results", "web"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, dict):
            nested = _rows(value)
            if nested:
                return nested
    return []


async def _research(query: str) -> list[WebSource]:
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
    except ImportError as exc:
        raise WebResearchError("The MCP client dependency is unavailable.") from exc

    headers = {}
    key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"

    try:
        async with create_mcp_http_client(headers=headers) as http_client:
            async with streamable_http_client(FIRECRAWL_MCP_URL, http_client=http_client) as streams:
                read, write = streams
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    search = await session.call_tool(
                        "firecrawl_search", {"query": query, "limit": MAX_RESULTS}
                    )
                    candidates = _rows(_json_content(search))[:MAX_RESULTS]
                    sources: list[WebSource] = []
                    for row in candidates:
                        url = str(row.get("url") or "").strip()
                        if not url.startswith(("https://", "http://")):
                            continue
                        title = str(row.get("title") or url).strip()[:300]
                        excerpt = str(
                            row.get("description") or row.get("markdown") or row.get("content") or ""
                        ).strip()
                        if len(sources) < MAX_SCRAPES and len(excerpt) < 500:
                            try:
                                scraped = await session.call_tool(
                                    "firecrawl_scrape",
                                    {"url": url, "formats": ["markdown"], "onlyMainContent": True},
                                )
                                scrape_payload = _json_content(scraped)
                                if isinstance(scrape_payload, dict):
                                    data = scrape_payload.get("data", scrape_payload)
                                    if isinstance(data, dict):
                                        excerpt = str(data.get("markdown") or data.get("content") or excerpt)
                            except Exception:
                                pass
                        sources.append(WebSource(title, url, excerpt[:MAX_SOURCE_CHARS]))
                    return sources
    except WebResearchError:
        raise
    except Exception as exc:
        raise WebResearchError("Firecrawl web research is temporarily unavailable.") from exc


def research_web(query: str) -> list[WebSource]:
    query = query.strip()
    if not query:
        return []
    return asyncio.run(_research(query))
