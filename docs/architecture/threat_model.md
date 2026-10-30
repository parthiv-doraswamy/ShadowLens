# ShadowLens Threat Model

**Status:** STRIDE-lite baseline derived from the master specification; not a completed security audit.  
**Source:** Master Specification sections 0, 1, 9, 10 and 22.

## 1. Assets and trust boundaries

**Assets:** local bearer token, SQLite database, install salt, HMAC vault, redacted findings/evidence, policy, uploaded files, optional gateway configuration and optional triage credentials.

**Trust boundaries:** untrusted PCAP/HAR/JSONL uploads; local processes and OS telemetry; agent-supplied traces; browser dashboard/API; optional gateway client/upstream; optional remote LLM provider; community detection/provider rules.

## 2. Threats and required mitigations

| Threat | Impact | Required mitigation | Validation |
|---|---|---|---|
| Local malware reads dashboard/API | Exposes local audit data | Loopback bind, bearer token, restrictive token/database permissions | Auth and file-permission tests |
| Malicious PCAP/HAR crashes parser | Denial of service or code-path abuse | Type/size limits, bounded resources, fuzzing, parse in subprocess with timeout where specified | Malformed corpus, fuzz/property tests |
| Regex ReDoS | CPU exhaustion | Safe-regex linting, per-rule 10 ms budget, optional RE2 | Rule lint and timeout tests |
| Prompt injection in inspected content targets triage | LLM follows attacker text | Treat snippet as quoted untrusted data, redact, length-cap, no tools, schema validate, deterministic override | Adversarial triage tests |
| Encoding layers evade detection | Hidden secret/PII | Bounded multi-layer decoding depth ≤3 and size ≤5 MB | Decode-boundary tests |
| Gateway becomes exfiltration point | Data leakage / SSRF | Explicit opt-in, loopback-only, configured upstream allowlist, reject arbitrary URLs, audit-only, no body persistence | Gateway SSRF and non-persistence tests |
| Community rules poison detection | False positives/negatives | Signed/checksummed rules and mandatory positive/negative tests | Rule integrity and CI tests |
| Permissions are overclaimed | False security assurance | Explicit coverage and UNAVAILABLE states; no automatic elevation | Permission-denial integration tests |
| Secret leaks through logs/exports | Credential disclosure | Redaction at boundaries, HMAC vault, masked evidence, identifier hashing | No-raw-persist and export tests |
| Collector failure stops entire service | Blind spot | Isolated adapters, supervisor restart with backoff and health visibility | Fault-injection tests |
| Policy simulation mutates live state | Unintended enforcement/config change | Candidate policy replay in isolated read-only path | State immutability tests |

## 3. STRIDE-lite coverage

- **Spoofing:** provider identity remains provisional until corroborated; local bearer token protects API.
- **Tampering:** versioned/checksummed detection rules; validated policy and structured uploads.
- **Repudiation:** event provenance, timestamps, source and linked evidence retained in safe metadata.
- **Information disclosure:** local-only defaults, transient raw payloads, redacted API/export, hashed identifiers.
- **Denial of service:** upload limits, bounded queues, parser timeouts, regex budgets, collector isolation.
- **Elevation of privilege:** no automatic privilege escalation; gateway restricted to loopback and allowlisted upstreams.

## 4. Security assumptions and limitations

- psutil may not observe other users' processes/sockets without permissions.
- Encrypted HTTPS body is not inspected.
- Process attribution can be incomplete due to PID reuse, short-lived connections, VPNs, proxies or shared stacks.
- File-read and shell-command evidence requires structured agent traces, supported OS audit adapters or explicit instrumentation; psutil alone is insufficient.
- Compliance mapping is informational, not certification.
- This document is a design threat model, not evidence that mitigations have been implemented or independently tested.

## 5. Required security test families

Upload parser fuzzing; malformed/truncated PCAP/HAR tests; size-limit tests; regex timeouts; prompt-injection triage tests; no-raw-persist tests; gateway SSRF/upstream tests; auth tests; permission-denial tests; rule integrity tests; policy replay immutability tests; export redaction tests.
