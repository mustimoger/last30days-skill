"""Opt-in twitterapi.io backend for the single X research source."""

from __future__ import annotations

import json
import time
from datetime import date, timedelta
from urllib.parse import urlsplit

from . import http, log, x_api, xquik


class Client:
    def __init__(self, config: dict):
        self.token = config.get("TWITTERAPI_IO_API_KEY") or ""
        self.base_url = (config.get("TWITTERAPI_IO_BASE_URL") or "https://api.twitterapi.io").rstrip("/")
        self.max_pages = int(config.get("LAST30DAYS_TWITTERAPI_MAX_PAGES") or 3)
        self.timeout = float(config.get("LAST30DAYS_TWITTERAPI_TIMEOUT_SECONDS") or 30)
        parsed = urlsplit(self.base_url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.path or parsed.query or parsed.fragment):
            raise ValueError("TWITTERAPI_IO_BASE_URL must be an HTTPS origin without credentials")
        if self.max_pages < 1 or self.timeout <= 0:
            raise ValueError("TwitterAPI page and timeout limits must be positive")

    def search(self, query, from_date, to_date, depth="default", *, deadline=None, cancel=None, count=None, scoring_query=None):
        count = count or x_api.DEPTH_CONFIG.get(depth, x_api.DEPTH_CONFIG["default"])
        # X's until: day is exclusive; the report's ending day is inclusive.
        end = (date.fromisoformat(to_date) + timedelta(days=1)).isoformat()
        start = date.fromisoformat(from_date).isoformat()
        params = {"query": f"({query}) since:{start} until:{end}", "queryType": "Top", "cursor": ""}
        items, seen_ids, cursors = [], set(), set()
        deadline = deadline if deadline is not None else time.monotonic() + x_api.DEADLINE_SECONDS
        if not self.token:
            return {"items": [], "error": "TwitterAPI auth failed: TWITTERAPI_IO_API_KEY not set"}
        for page in range(self.max_pages):
            if (cancel is not None and cancel.is_set()) or time.monotonic() >= deadline:
                return {"items": items, "error": "TwitterAPI research cancelled or timed out"}
            try:
                body = http.get(
                    f"{self.base_url}/twitter/tweet/advanced_search",
                    params=params, headers={"X-API-Key": self.token},
                    timeout=self.timeout, retries=1, max_429_retries=0,
                    deadline_monotonic=deadline, cancel=cancel,
                    usage_provider="twitterapi",
                )
            except http.HTTPError as exc:
                status = getattr(exc, "status_code", None)
                detail = f"TwitterAPI HTTP {status}" if status else "TwitterAPI request timed out or failed"
                if status in (401, 403):
                    detail = f"TwitterAPI auth failed (HTTP {status})"
                elif status == 402:
                    detail = "TwitterAPI key unpaid (HTTP 402)"
                log.source_log("TwitterAPI", detail, tty_only=False)
                return {"items": items, "error": detail}
            if not isinstance(body, dict) or not isinstance(body.get("tweets"), list):
                return {"items": items, "error": "TwitterAPI schema drift: missing tweets array"}
            if not isinstance(body.get("has_next_page"), bool):
                return {"items": items, "error": "TwitterAPI schema drift: invalid pagination flag"}
            tweets = body["tweets"]
            log.source_log("TwitterAPI", json.dumps({"event": "page", "returned_tweets": len(tweets), "page": page + 1}), tty_only=False)
            malformed = 0
            for tweet in tweets:
                if not isinstance(tweet, dict) or not tweet.get("id"):
                    malformed += 1
                    continue
                identifier = str(tweet["id"])
                if identifier in seen_ids:
                    continue
                author = tweet.get("author")
                if not isinstance(author, dict):
                    malformed += 1
                    continue
                handle = author.get("userName") or author.get("username")
                if not isinstance(handle, str) or not handle.strip():
                    malformed += 1
                    continue
                normalized = dict(tweet, author=dict(author, username=handle))
                item = xquik._parse_tweet(normalized, len(items), scoring_query or query, id_prefix="TIO")
                if item is None:
                    malformed += 1
                    continue
                # Preserve the source's complete text; the shared parser's
                # display excerpt is shorter than some research evidence.
                item["text"] = str(tweet.get("text") or "").strip()
                source_url = urlsplit(str(tweet.get("url") or ""))
                if source_url.scheme == "https" and source_url.hostname in {"x.com", "twitter.com", "www.twitter.com"}:
                    item["url"] = str(tweet["url"])
                seen_ids.add(identifier)
                items.append(item)
            if malformed:
                return {"items": items[:count], "error": f"TwitterAPI schema drift: {malformed} unparseable tweets"}
            if len(items) >= count or not body.get("has_next_page"):
                return {"items": items[:count]}
            cursor = body.get("next_cursor")
            if not isinstance(cursor, str) or not cursor or cursor in cursors:
                return {"items": items, "error": "TwitterAPI schema drift: missing or repeated cursor"}
            cursors.add(cursor)
            params["cursor"] = cursor
        return {"items": items[:count], "error": "TwitterAPI page limit reached; coverage is partial"}

    def handles(self, handles, topic, from_date, to_date, *, count, mentions=False, and_topic=False, deadline=None, cancel=None):
        items, errors, urls = [], [], set()
        for handle in handles:
            query = f"@{handle}" if mentions else f"from:{handle}"
            if and_topic:
                query += f" ({topic})"
            result = self.search(query, from_date, to_date, count=count, deadline=deadline, cancel=cancel, scoring_query=topic)
            if result.get("error"):
                errors.append(result["error"])
            for item in result["items"]:
                if mentions and x_api.is_own_post(item["url"], handle):
                    continue
                if item["url"] not in urls:
                    urls.add(item["url"])
                    item["id"] = f"TIOH{len(items) + 1}"
                    items.append(item)
            if any("auth failed" in error or "key unpaid" in error for error in errors):
                break
        return items, errors
