import json

import pytest

from app.observability import configure_structured_logging, redact_log_fields


def test_log_processor_redacts_sensitive_keys_and_credential_patterns() -> None:
    event = redact_log_fields(
        None,
        "info",
        {
            "event": "test_event",
            "authorization": "Bearer header-secret-value",
            "api_key": "sk-proj-ABCDEFGHIJKLMNOP",
            "details": (
                "Authorization: Bearer body-secret-value "
                "OPENAI_API_KEY=sk-proj-QRSTUVWXYZABCDEF"
            ),
            "nested": {
                "password": "sensitive-password",
                "safe_count": 4,
                "request_body": "raw prompt text",
            },
        },
    )
    rendered = json.dumps(event)
    assert event["authorization"] == "[REDACTED]"
    assert event["api_key"] == "[REDACTED]"
    assert event["nested"] == {
        "password": "[REDACTED]",
        "safe_count": 4,
        "request_body": "[REDACTED]",
    }
    assert "header-secret-value" not in rendered
    assert "ABCDEFGHIJKLMNOP" not in rendered
    assert "body-secret-value" not in rendered
    assert "QRSTUVWXYZABCDEF" not in rendered
    assert "sensitive-password" not in rendered
    assert "raw prompt text" not in rendered


def test_log_processor_bounds_depth_strings_and_collections() -> None:
    value = {
        "deep": {
            "deeper": {
                "deepest": {
                    "beyond": {"still_beyond": "not emitted"}
                }
            }
        }
    }
    value["items"] = list(range(40))
    value["long"] = "x" * 600
    processed = redact_log_fields(None, "info", value)
    assert (
        processed["deep"]["deeper"]["deepest"]["beyond"]["still_beyond"]
        == "[TRUNCATED]"
    )
    assert len(processed["items"]) == 33
    assert processed["items"][-1] == "[TRUNCATED]"
    assert len(processed["long"]) == 513


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValueError, match="SHADOWLENS_LOG_LEVEL"):
        configure_structured_logging("TRACE")
