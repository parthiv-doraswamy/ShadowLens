"""Positive and negative provider classification tests [REQ-DISC-001]."""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.providers.registry import ProviderRegistry, Signal, default_registry

REGISTRY = default_registry()


@pytest.mark.parametrize(
    ("host", "path", "provider"),
    [
        ("api.openai.com", "/v1/chat/completions", "openai"),
        ("api.anthropic.com", "/v1/messages", "anthropic"),
        ("generativelanguage.googleapis.com", "/v1beta/models", "google_gemini"),
        ("team.openai.azure.com", "/openai/deployments/gpt/chat/completions", "azure_openai"),
        ("bedrock-runtime.us-east-1.amazonaws.com", "/model/example/invoke", "aws_bedrock"),
        ("api.cohere.com", "/v2/chat", "cohere"),
        ("api.mistral.ai", "/v1/chat/completions", "mistral"),
        ("api.perplexity.ai", "/chat/completions", "perplexity"),
        ("api.groq.com", "/openai/v1/chat/completions", "groq"),
        ("api.together.xyz", "/v1/chat/completions", "together"),
        ("api.fireworks.ai", "/inference/v1/chat/completions", "fireworks"),
        ("api.featherless.ai", "/v1/chat/completions", "featherless"),
        ("openrouter.ai", "/api/v1/chat/completions", "openrouter"),
        ("api-inference.huggingface.co", "/models/example", "huggingface_inference"),
        ("api.replicate.com", "/v1/predictions", "replicate"),
        ("api.deepseek.com", "/v1/chat/completions", "deepseek"),
        ("api.x.ai", "/v1/chat/completions", "xai"),
        ("127.0.0.1", "/api/chat", "ollama"),
        ("127.0.0.1", "/v1/models", "lm_studio"),
        ("127.0.0.1", "/completion", "llama_cpp"),
        ("127.0.0.1", "/v1/chat/completions", "vllm"),
        ("api2.cursor.sh", "/aiserver.v1/Service/Stream", "cursor"),
        ("api.githubcopilot.com", "/inference/chat", "github_copilot"),
        ("server.codeium.com", "/exa.language_server_pb.LanguageServerService", "codeium_windsurf"),
        ("api.tabnine.com", "/v1/completions", "tabnine"),
    ],
)
def test_each_required_provider_has_positive_example(host: str, path: str, provider: str) -> None:
    signal = Signal(host=host, path=path, port=443 if host != "127.0.0.1" else {
        "ollama": 11434, "lm_studio": 1234, "llama_cpp": 8080, "vllm": 8000
    }[provider])
    result = REGISTRY.classify(signal)
    assert result.provider == provider
    assert result.matched is True
    assert result.provisional is False
    assert result.confidence >= 0.85


@pytest.mark.parametrize(
    ("host", "path"),
    [
        ("example.com", "/"),
        ("notopenai.com", "/v1/chat/completions"),
        ("fake-anthropic.example", "/v1/messages"),
        ("api.openai.com.attacker.example", "/v1/chat/completions"),
        ("googleapis.com.attacker.example", "/v1beta/models"),
        ("localhost", "/health"),
        ("random.example", "/v1/embeddings"),
    ],
)
def test_non_provider_or_lookalike_hosts_are_not_confirmed(host: str, path: str) -> None:
    result = REGISTRY.classify(Signal(host=host, path=path))
    assert result.matched is False
    if path == "/v1/chat/completions" or path == "/v1/messages":
        assert result.provider == "unknown_llm_api"
        assert result.confidence == 0.7
        assert result.provisional is True
    else:
        assert result.provider == "unknown"


def test_header_signature_classifies_only_with_independent_corroboration() -> None:
    result = REGISTRY.classify(Signal(
        host="api.example.test",
        path="/messages",
        headers={"anthropic-version": "2023-06-01"},
    ))
    assert result.provider in {"unknown", "unknown_llm_api"}
    assert result.provisional is True


def test_authorized_header_fingerprint_can_corroborate_provider() -> None:
    result = REGISTRY.classify(Signal(
        host="gateway.internal",
        path="/v1/messages",
        headers={"anthropic-version": "2023-06-01", "x-api-key": "sk-ant-placeholder"},
        user_agent="anthropic-sdk/1.0",
    ))
    assert result.provider == "anthropic"
    assert result.confidence >= 0.7
    assert "sk-ant-placeholder" not in str(result)


def test_url_signal_parser_is_metadata_only() -> None:
    signal = Signal.from_url(
        "https://api.openai.com/v1/chat/completions?token=must-not-be-read",
        headers={"Authorization": "Bearer secret"},
    )
    assert signal.host == "api.openai.com"
    assert signal.path == "/v1/chat/completions"
    assert signal.headers["authorization"] == "Bearer secret"  # in-memory input only
    result = REGISTRY.classify(signal)
    assert result.provider == "openai"
    assert "secret" not in str(result)


def test_rejects_invalid_url_and_registry_schema() -> None:
    with pytest.raises(ValueError):
        Signal.from_url("file:///etc/passwd")
    with pytest.raises(ValidationError):
        Signal(host="bad host")
    with pytest.raises(ValueError, match="provider YAML"):
        ProviderRegistry.from_yaml(Path(__file__).parent / "invalid-providers.yaml")


def test_registry_reload_is_atomic_on_invalid_yaml(tmp_path: Path) -> None:
    registry = default_registry()
    original_ids = [provider.id for provider in registry.providers]
    invalid = tmp_path / "bad.yaml"
    invalid.write_text("version: 1\nproviders: [not-a-provider]", encoding="utf-8")
    with pytest.raises(ValidationError):
        registry.reload(invalid)
    assert [provider.id for provider in registry.providers] == original_ids


def test_path_or_body_shape_alone_never_confirms_provider() -> None:
    result = REGISTRY.classify(Signal(
        host="unrecognized.example",
        path="/v1/chat/completions",
    ))
    assert result.provider == "unknown_llm_api"
    assert result.confidence == 0.7
    assert result.provisional is True


def test_provider_yaml_covers_all_minimum_named_providers() -> None:
    expected = {
        "openai", "anthropic", "google_gemini", "azure_openai", "aws_bedrock",
        "cohere", "mistral", "perplexity", "groq", "together", "fireworks",
        "featherless", "openrouter", "huggingface_inference", "replicate",
        "deepseek", "xai", "ollama", "lm_studio", "llama_cpp", "vllm",
        "cursor", "github_copilot", "codeium_windsurf", "tabnine",
    }
    assert {provider.id for provider in REGISTRY.providers} == expected


@pytest.mark.parametrize("provider", REGISTRY.providers, ids=lambda item: item.id)
def test_every_provider_has_a_negative_example(provider: object) -> None:
    """Provider path/port hints must not match when the destination host is unrelated."""
    paths = provider.paths
    ports = provider.ports
    signal = Signal(
        host="unrelated-attacker.invalid",
        path=paths[0] if paths else "/",
        port=ports[0] if ports else None,
    )
    result = REGISTRY.classify(signal)
    assert result.provider != provider.id


def test_unknown_json_llm_shape_remains_provisional() -> None:
    result = REGISTRY.classify(Signal(
        host="unrecognized.example",
        path="/custom/inference",
        json_keys=["model", "messages"],
    ))
    assert result.provider == "unknown_llm_api"
    assert result.confidence == 0.7
    assert result.provisional is True
    assert result.matched is False


def test_wildcard_host_patterns_support_region_labels_and_boundaries() -> None:
    result = REGISTRY.classify(Signal(
        host="bedrock-runtime.us-east-1.amazonaws.com",
        path="/model/example/invoke",
        port=443,
    ))
    assert result.provider == "aws_bedrock"
    spoofed = REGISTRY.classify(Signal(
        host="bedrock-runtime.us-east-1.amazonaws.com.attacker.invalid",
        path="/model/example/invoke",
        port=443,
    ))
    assert spoofed.provider == "unknown"


def test_unknown_llm_api_kind_conforms_to_domain_contract() -> None:
    from app.models.contracts import AIContext

    result = REGISTRY.classify(Signal(
        host="unknown.example",
        path="/v1/chat/completions",
    ))
    context = AIContext.model_validate(result.to_ai_context())
    assert context.provider == "unknown_llm_api"
    assert context.kind.value == "unknown_llm_api"


def test_signal_repr_and_serialization_do_not_expose_header_values() -> None:
    signal = Signal(
        host="gateway.internal",
        headers={"Authorization": "Bearer do-not-print-this"},
    )
    assert "do-not-print-this" not in repr(signal)
    assert "do-not-print-this" not in str(signal.model_dump())
    assert signal.headers["authorization"] == "Bearer do-not-print-this"


def test_invalid_header_regex_is_rejected_before_registry_activation(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid-regex.yaml"
    invalid.write_text(
        "version: 1\nproviders:\n"
        "  - id: invalid_provider\n"
        "    display_name: Invalid\n"
        "    kind: cloud\n"
        "    headers: {x-test: '['}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="invalid header fingerprint pattern"):
        ProviderRegistry.from_yaml(invalid)
