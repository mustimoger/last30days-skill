"""twitterapi.io routing and paid-request boundary regressions."""

import threading
import unittest
from unittest.mock import patch

from lib import backends, env, http, pipeline
from lib.twitterapi import Client

CONFIG = {"TWITTERAPI_IO_API_KEY": "dummy-key", "LAST30DAYS_X_BACKEND": "twitterapi"}


def tweet(identifier="1", handle="vendor"):
    return {"id": identifier, "author": {"userName": handle}, "text": "AI agent workflow " * 40,
            "createdAt": "2026-10-14T12:00:00Z", "likeCount": 0,
            "url": f"https://x.com/{handle}/status/{identifier}"}


class TwitterAPITests(unittest.TestCase):
    @patch("lib.twitterapi.http.get")
    def test_paging_dedup_and_last_day_inclusion(self, get):
        get.side_effect = [
            {"tweets": [tweet()], "has_next_page": True, "next_cursor": "page2"},
            {"tweets": [tweet(), tweet("2")], "has_next_page": False},
        ]
        result = Client(CONFIG).search("AI agents", "2026-10-01", "2026-10-14")
        self.assertNotIn("error", result)
        self.assertEqual(len(result["items"]), 2)
        self.assertIn("until:2026-10-15", get.call_args_list[0].kwargs["params"]["query"])
        self.assertEqual(get.call_args_list[1].kwargs["params"]["cursor"], "page2")
        self.assertGreater(len(result["items"][0]["text"]), 500)
        self.assertEqual(result["items"][0]["engagement"]["likes"], 0)

    @patch("lib.twitterapi.http.get")
    def test_clean_empty_is_not_error(self, get):
        get.return_value = {"tweets": [], "has_next_page": False}
        self.assertEqual(Client(CONFIG).search("AI", "2026-10-01", "2026-10-14"), {"items": []})

    @patch("lib.twitterapi.http.get")
    def test_error_after_first_page_retains_partial_evidence(self, get):
        get.side_effect = [
            {"tweets": [tweet()], "has_next_page": True, "next_cursor": "p2"},
            http.HTTPError("rate limited", status_code=429),
        ]
        result = Client(CONFIG).search("AI", "2026-10-01", "2026-10-14")
        self.assertEqual(len(result["items"]), 1)
        self.assertIn("429", result["error"])

    @patch("lib.twitterapi.http.get")
    def test_auth_and_payment_failures_are_explicit(self, get):
        for status, marker in [(401, "auth failed"), (403, "auth failed"), (402, "key unpaid")]:
            get.side_effect = http.HTTPError("provider rejected key", status_code=status)
            result = Client(CONFIG).search("AI", "2026-10-01", "2026-10-14")
            self.assertIn(marker, result["error"])
            self.assertNotIn("dummy-key", result["error"])

    @patch("lib.twitterapi.http.get")
    def test_schema_drift_is_not_clean_empty(self, get):
        for body in [{}, {"tweets": "invalid"}, {"tweets": [{"id": "1", "author": {}}]}]:
            get.return_value = body
            self.assertIn("schema drift", Client(CONFIG).search("AI", "2026-10-01", "2026-10-14")["error"])

    @patch("lib.twitterapi.http.get")
    def test_repeated_cursor_is_bounded(self, get):
        get.return_value = {"tweets": [tweet()], "has_next_page": True, "next_cursor": "same"}
        result = Client(CONFIG).search("AI", "2026-10-01", "2026-10-14")
        self.assertEqual(get.call_count, 2)
        self.assertIn("repeated cursor", result["error"])

    @patch("lib.twitterapi.http.get")
    def test_cancel_and_missing_key_make_no_request(self, get):
        cancel = threading.Event()
        cancel.set()
        self.assertIn("cancelled", Client(CONFIG).search("AI", "2026-10-01", "2026-10-14", cancel=cancel)["error"])
        self.assertIn("auth failed", Client({}).search("AI", "2026-10-01", "2026-10-14")["error"])
        get.assert_not_called()

    def test_http_origin_cannot_receive_key(self):
        for url in ["http://api.twitterapi.io", "https://user:pass@api.twitterapi.io", "https://api.twitterapi.io/path"]:
            with self.assertRaises(ValueError):
                Client(dict(CONFIG, TWITTERAPI_IO_BASE_URL=url))

    def test_pin_never_falls_back_or_auto_selects(self):
        config = dict(CONFIG, XAI_API_KEY="dummy-xai", X_BEARER_TOKEN="dummy-bearer")
        self.assertEqual(env.x_backend_chain(config), ["twitterapi"])
        self.assertEqual(env.x_backend_chain(dict(config, TWITTERAPI_IO_API_KEY="")), [])
        self.assertNotIn("twitterapi", env.x_auto_chain(CONFIG))
        self.assertEqual(env.get_x_source_status(CONFIG, probe=False)["source"], "twitterapi")
        self.assertTrue(backends._X_PROBES["twitterapi"](CONFIG).usable)

    @patch("lib.twitterapi.http.get")
    def test_real_pipeline_dispatch_uses_adapter(self, get):
        get.return_value = {"tweets": [tweet()], "has_next_page": False}
        items, error = pipeline._fetch_x_backend("twitterapi", "AI agents", "2026-10-01", "2026-10-14", "quick", CONFIG)
        self.assertFalse(error)
        self.assertEqual(items[0]["author_handle"], "vendor")

    @patch("lib.twitterapi.http.get")
    def test_handle_mentions_exclude_subjects_own_posts(self, get):
        get.return_value = {"tweets": [tweet(), tweet("2", "other")], "has_next_page": False}
        items, errors = Client(CONFIG).handles(["vendor"], "AI agents", "2026-10-01", "2026-10-14", count=20, mentions=True)
        self.assertFalse(errors)
        self.assertEqual([item["author_handle"] for item in items], ["other"])
