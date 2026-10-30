# Chunk 3.1 — Provider Registry and Classifier

**Requirement:** REQ-DISC-001 (P0)  
**Status:** Implemented on `feat/provider-registry-req-disc-001`; pull-request CI pending.  
**Scope:** Provider identity classification from observable metadata only.

## Delivered

- Added a versioned YAML registry with the 25 provider/tool families required by the master specification: OpenAI, Anthropic, Google Gemini/Vertex, Azure OpenAI, AWS Bedrock, Cohere, Mistral, Perplexity, Groq, Together, Fireworks, Featherless, OpenRouter, Hugging Face, Replicate, DeepSeek, xAI, Ollama, LM Studio, llama.cpp, vLLM, Cursor, GitHub Copilot, Codeium/Windsurf and Tabnine.
- Added deterministic classification for exact and wildcard DNS host patterns, URL paths, destination ports, TLS SNI, bounded HTTP header fingerprints and User-Agent signals.
- Added strict Pydantic schema validation and atomic YAML reload. An invalid replacement leaves the active registry untouched.
- Added unknown API-like request handling. Known LLM request paths and keys-only JSON shape hints (`messages` or `prompt`) return `provider=unknown_llm_api`, `kind=unknown_llm_api`, confidence `0.7` and `provisional=true`. Those clues never establish a named provider on their own.
- Added domain enum support so the unknown-API classification is valid in the existing `AIContext` contract.
- Kept headers transient to classification: header values are omitted from `Signal` representations/serialization and never copied into match evidence. The classifier does not accept or inspect request-body values.
- Declared PyYAML as a runtime dependency and included `providers.yaml` as installed package data.
- Updated README, backlog, acceptance notes and requirement traceability.

## Files changed

- `backend/app/providers/__init__.py`
- `backend/app/providers/registry.py`
- `backend/app/providers/providers.yaml`
- `backend/app/models/enums.py`
- `backend/pyproject.toml`
- `backend/tests/test_provider_registry.py`
- `docs/requirements/traceability_matrix.md`
- `docs/requirements/acceptance_criteria.md`
- `docs/requirements/implementation_backlog.md`
- `README.md`

## Tests added

- Positive classification cases for all 25 registry entries.
- Per-provider negative case using an unrelated destination host with the provider's path/port hints.
- Lookalike-domain and suffix-spoof rejection.
- Unknown API path and keys-only JSON-shape provisional classification.
- Header fingerprint corroboration and header-value non-disclosure.
- URL parsing without network access or query-string retention.
- Invalid URL, YAML schema, regex, and failed-reload behavior.
- Compatibility with the shared `AIContext` Pydantic contract.

## Verification status

- **Local test execution:** Not run in this environment; repository source was inspected and changed through the GitHub connector.
- **GitHub Actions:** Pending PR-triggered CI and Security workflows. Do not treat this chunk as CI-verified until both workflows complete successfully.
- **No test pass is claimed in this report.**

## Boundaries and remaining work

- The registry classifies supplied metadata; it does not itself collect sockets, PCAP, HAR, HTTP logs, SNI, or process data.
- JSON shape classification expects a future bounded parser to pass key names only; this chunk does not parse or retain request bodies.
- Registry signatures are initial deterministic fingerprints and need maintenance as providers change.
- `REQ-DISC-002` sanctioned/shadow policy and 24-hour deduplication are not included.
- `REQ-DISC-003` opt-in config discovery and `REQ-DISC-004` browser-extension discovery are separate future chunks.
- No TLS decryption, MITM, external network calls, or secret/prompt persistence was added.

## Traceability

`REQ-DISC-001` maps to `backend/app/providers` and `backend/tests/test_provider_registry.py`. This requirement is implemented on the feature branch; final verification status depends on PR CI.
