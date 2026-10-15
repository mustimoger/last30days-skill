"""OpenAI request compatibility and migration limits."""

from unittest.mock import patch

import pytest

from lib import env, providers


@pytest.mark.parametrize("effort", [None, "none", "low"])
def test_request_uses_compatible_reasoning_and_sampling(effort):
    client = providers.OpenAIClient("dummy-key", reasoning_effort=effort, max_output_tokens=128)
    with patch.object(providers.http, "post", return_value={"output_text": "ok"}) as post:
        assert client.generate_text("gpt-6-luna", "Return ok") == "ok"
    payload = post.call_args.args[1]
    assert payload["max_output_tokens"] == 128
    assert payload["store"] is False
    if effort is None:
        assert "reasoning" not in payload
    else:
        assert payload["reasoning"] == {"effort": effort}
    if effort in (None, "none"):
        assert payload["temperature"] == 0
    else:
        assert "temperature" not in payload


def test_existing_client_keeps_legacy_payload():
    client = providers.OpenAIClient("dummy-key")
    with patch.object(providers.http, "post", return_value={"output_text": "ok"}) as post:
        client.generate_text("gpt-4.1-mini", "Return ok")
    assert post.call_args.args[1] == {
        "model": "gpt-4.1-mini", "store": False, "input": "Return ok", "temperature": 0,
    }


@pytest.mark.parametrize("value", [0, -1, "0", "1.5", "invalid", True, 1.5])
def test_invalid_output_limit_fails_before_transport(value):
    with patch.object(providers.http, "post") as post:
        with pytest.raises(ValueError, match="positive integer"):
            providers.OpenAIClient("dummy-key", max_output_tokens=value)
        post.assert_not_called()


def test_invalid_effort_fails_before_transport():
    with patch.object(providers.http, "post") as post:
        with pytest.raises(ValueError, match="supported effort"):
            providers.OpenAIClient("dummy-key", reasoning_effort="typo")
        post.assert_not_called()


def test_private_config_reaches_runtime_client(tmp_path, monkeypatch):
    config_file = tmp_path / ".env"
    config_file.write_text(
        "OPENAI_API_KEY=dummy-key\nLAST30DAYS_REASONING_PROVIDER=openai\n"
        "LAST30DAYS_PLANNER_MODEL=gpt-6-luna\nLAST30DAYS_RERANK_MODEL=gpt-6-luna\n"
        "LAST30DAYS_OPENAI_REASONING_EFFORT=none\n"
        "LAST30DAYS_OPENAI_MAX_OUTPUT_TOKENS=32768\n"
    )
    monkeypatch.setattr(env, "CONFIG_FILE", config_file)
    config = env.get_config()
    runtime, client = providers.resolve_runtime(config, "default")
    assert runtime.planner_model == runtime.rerank_model == "gpt-6-luna"
    assert client.reasoning_effort == "none"
    assert client.max_output_tokens == 32768
    monkeypatch.setenv("LAST30DAYS_OPENAI_REASONING_EFFORT", "low")
    _, client = providers.resolve_runtime(env.get_config(), "default")
    assert client.reasoning_effort == "low"
