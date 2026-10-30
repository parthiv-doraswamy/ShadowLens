# ShadowLens Requirement Traceability Matrix

**Status:** Complete planning map for all IDs extracted in Chunk 0.2. Test paths below are planned test ownership, not claims that test files exist or pass.  
**Source:** Master Specification sections 6, 12, 14, 15–17 and 20–22.

## 1. Traceability rules

- Every REQ ID maps to at least one implementation chunk, planned test and observable API/UI/CLI outcome.
- Tests must be written before implementation and derived from acceptance criteria.
- The source section 16 matrix is an excerpt; this matrix extends it as a planning artifact.
- NOV features without a dedicated REQ are mapped to their closest functional requirement and milestone; their standalone acceptance must be added before implementation.
- NFRs are tracked separately below.
- Priority conflicts remain as documented in requirements_catalog.md.

## 2. Functional requirement matrix

| Requirement | Primary module | Chunk / milestone | Planned test ownership | Observable outcome |
|---|---|---|---|---|
| REQ-COL-001 | collectors/socket | 2.3 / M2 | tests/integration/test_socket.py | Inventory + health partial-visibility badge |
| REQ-COL-002 | collectors/pcap | 2.4 / M2 | tests/integration/test_pcap.py | Ingest page, T1/T3 event evidence |
| REQ-COL-003 | collectors/logs | 2.3 / M2 | tests/integration/test_log_ingest.py | Imported event/finding list |
| REQ-COL-004 | collectors/loopback | 9.3 / M6 | tests/integration/test_loopback.py | Ingest coverage and permission status |
| REQ-COL-005 | collectors/gateway | 9.4 / M6 | tests/integration/test_gateway.py | Gateway setup/status panel |
| REQ-COL-006 | collectors/agent_hooks | 3.1 / M3 | tests/integration/test_agent_adapters.py | Agent activity inventory |
| REQ-COL-007 | sim/scenarios | 8.1 / M6 | tests/integration/test_simulator.py | Scenario launcher and populated demo |
| REQ-DISC-001 | backend/app/providers | 3.1 / M2 | backend/tests/test_provider_registry.py | Provider identity/confidence, evidence, provisional unknown state |
| REQ-DISC-002 | core/providers + policy | 3.1 / M2 | tests/unit/test_sanctioned_shadow.py | Shadow AI finding / sanction status |
| REQ-DISC-003 | collectors/config_scanner | 3.2 / M3 | tests/security/test_config_scanner_boundary.py | Config discovery results + opt-in state |
| REQ-DISC-004 | collectors/browser_extension | 3.2 / M3 | tests/unit/test_extension_discovery.py | Extension risk finding |
| REQ-DET-001 | core/normalize | 4.1 / M1 | tests/unit/test_normalization.py | Normalized inspection candidate |
| REQ-DET-002 | core/detect/secrets | 4.2 / M1 | tests/unit/test_rules_secrets.py | Secret finding with masked evidence |
| REQ-DET-003 | core/detect/entropy | 4.3 / M1 | tests/unit/test_entropy.py | Entropy candidate confidence |
| REQ-DET-004 | core/detect/pii | 4.4 / M1 | tests/unit/test_pii_validators.py | Validated PII finding |
| REQ-DET-005 | core/detect/proprietary | 4.5 / M1 | tests/unit/test_proprietary_data.py | Proprietary-data finding without code persistence |
| REQ-DET-006 | core/detect/canary | 4.7 / M1 | tests/security/test_canary.py | Critical canary finding |
| REQ-DET-007 | core/detect/dedup | 4.8 / M1 | tests/unit/test_finding_dedup.py | Occurrence count / suppression |
| REQ-DET-008 | core/detect/streaming | 4.8 / M1 | tests/unit/test_chunk_boundary.py | Cross-chunk secret detection |
| REQ-AGT-001 | core/agent/toolcalls | 5.2 / M3 | tests/unit/test_toolcall_normalization.py | Normalized agent event |
| REQ-AGT-002 | core/agent/shell_rules | 5.3 / M3 | tests/unit/test_shell_rules.py | Shell behavior finding |
| REQ-AGT-003 | core/agent/fs_rules | 5.4 / M3 | tests/unit/test_fs_rules.py | Sensitive file-read finding |
| REQ-AGT-004 | core/agent/net_rules | 5.5 / M3 | tests/unit/test_agent_network_rules.py | New-host / exfil destination finding |
| REQ-AGT-005 | core/agent/autonomy | 5.6 / M3 | tests/unit/test_autonomy.py | A0–A4 autonomy level |
| REQ-AGT-006 | core/agent/mcp_risk | 5.7 / M3 | tests/unit/test_mcp_risk.py | MCP capability risk |
| REQ-AGT-007 | core/agent/chain | 5.9 / M3 | tests/integration/test_chain.py | Critical ordered chain timeline |
| REQ-SHP-001 | core/shape | 6.2 / M4 | tests/unit/test_shape.py | T2 shape finding ≤0.7 confidence |
| REQ-RSK-001 | core/risk | 6.1 / M4 | tests/unit/test_risk.py | Deterministic bounded score |
| REQ-RSK-002 | core/risk + api | 6.1 / M4 | tests/api/test_risk_explain.py | Contribution table/top drivers/quick wins |
| REQ-CMP-001 | core/compliance | 6.3 / M4 | tests/unit/test_compliance.py | Versioned informational posture |
| REQ-CMP-002 | export/bom | 6.4 / M4 | tests/unit/test_ai_bom.py | CycloneDX 1.6 JSON |
| REQ-TRI-001 | core/triage | 7.4 / M7 | tests/integration/test_triage_fallback.py | Rule-based fallback / optional advisory |
| REQ-TRI-002 | core/triage | 7.5 / M7 | tests/security/test_triage_guardrails.py | Invalid output rejected; deterministic finding retained |
| REQ-POL-001 | config/policy | 7.1 / M7 | tests/unit/test_policy_validation.py | Validated hot-reloaded policy |
| REQ-POL-002 | core/policy_simulator | 7.2 / M7 | tests/integration/test_policy_simulation.py | Read-only candidate-policy diff |
| REQ-UI-001 | frontend/overview | 1.3, 7.1 / M5 | tests/e2e/test_overview.py | API-backed KPI/trend dashboard |
| REQ-UI-002 | frontend/inventory | 1.4, 7.1 / M5 | tests/e2e/test_inventory.py | Tool table and timeline |
| REQ-UI-003 | frontend/alerts | 1.4, 7.1 / M5 | tests/e2e/test_alerts.py | Filters and working status actions |
| REQ-UI-004 | frontend/graph | 1.4, 7.1 / M5 | tests/e2e/test_permission_graph.py | Evidence-backed React Flow graph |
| REQ-UI-005 | frontend/compliance | 1.4, 7.1 / M5 | tests/e2e/test_compliance.py | Control posture and export |
| REQ-UI-006 | frontend/ingest | 1.4, 7.1 / M5 | tests/e2e/test_ingest.py | Upload, simulator and safe controls |
| REQ-UI-007 | frontend/policy_studio | 1.4, 7.1 / M5 | tests/e2e/test_policy_studio.py | Policy validation/simulation diff |
| REQ-UI-008 | frontend/privacy_badge | 1.3, 7.1 / M5 | tests/e2e/test_privacy_badge.py | Accurate runtime privacy mode |
| REQ-UI-009 | frontend/design_system | 1.1, 1.3 / M5 | tests/e2e/test_accessibility.py | Keyboard, contrast, themes, empty states |
| REQ-PRIV-001 | core/privacy + repositories | 4.6 / M1; all phases | tests/security/test_no_raw_persist.py | Raw test secret absent from retained stores |
| REQ-PRIV-002 | core/privacy/vault | 4.6 / M1 | tests/security/test_hmac_vault.py | HMAC + masked preview only |
| REQ-PRIV-003 | core/privacy/redaction | 4.6 / M1 | tests/unit/test_redaction.py | Typed placeholders in context |
| REQ-PRIV-004 | api/export/triage | 4.6 / M1; 7.3 / M7 | tests/security/test_default_redaction.py | Redacted API/export; no unapproved egress |
| REQ-PRIV-005 | cli/forget | 4.6 / M1 | tests/security/test_forget.py | DB/vault/salt wipe verified |
| REQ-PRIV-006 | export/identifiers | 4.6 / M1 | tests/security/test_identifier_export.py | Hashed identifiers by default |

## 3. Novelty feature traceability

| NOV | Feature | REQ / implementation owner | Milestone |
|---|---|---|---|
| NOV-1 | Visibility tiers and evidence chain | Cross-cutting canonical contracts; all collectors/findings | M0–M5 |
| NOV-2 | Config-based discovery | REQ-DISC-003 | M3 |
| NOV-3 | Agent permission graph | REQ-UI-004 + REQ-AGT-003/004/006 | M3/M5 |
| NOV-4 | Canary tokens | REQ-DET-006 | M1 |
| NOV-5 | Encrypted-flow shape analysis | REQ-SHP-001 | M4 |
| NOV-6 | Injection-to-exfil chain | REQ-AGT-007 | M3 |
| NOV-7 | AI-BOM | REQ-CMP-002 | M4 |
| NOV-8 | Compliance control mapping | REQ-CMP-001 | M4 |
| NOV-9 | Explainable risk score | REQ-RSK-001/002 | M4 |
| NOV-10 | Policy simulator | REQ-POL-002 | M7 |
| NOV-11 | Privacy-first vault | REQ-PRIV-001–006 | M1 and continuous |
| NOV-12 | Detection benchmark harness | Section 12; REQ-DET-001–004 support | M1 |
| NOV-13 | Scenario simulator | REQ-COL-007 | M6 |
| NOV-14 | LLM triage guardrails | REQ-TRI-001/002 | M7 |
| NOV-15 | SIEM/ticket export | Section 3 stretch; export interfaces | M8 stretch |

## 4. NFR traceability

| NFR | Owning module | Planned verification |
|---|---|---|
| NFR-PERF-1 | bus/core pipeline | Sustained 2,000 events/s benchmark on documented 4-core machine |
| NFR-PERF-2 | PCAP parser | ≥50 MB/s benchmark; 200 MB upload cap |
| NFR-PERF-3 | collectors/runtime | Idle RAM <150 MB and CPU <3% measurement |
| NFR-PERF-4 | frontend | Local first-paint <1.5 s measurement |
| NFR-REL-1 | collector supervisor | Fault injection, independent restart/backoff |
| NFR-REL-2 | repositories | WAL, ≥500-row batches, retention purge tests |
| NFR-SEC-1 | API auth | Bearer auth on all routes except /api/health |
| NFR-PORT-1 | collectors/platform | Linux/macOS/Windows capability matrix and permission tests |
| NFR-TEST-1 | test suite | ≥90% core/detect and ≥80% overall coverage |
| NFR-DOC-1 | README/packaging | Clean-checkout quick start in fewer than five commands |

## 5. Source section 16 test-path carryover

The source's named tests are retained: test_socket.py, test_pcap.py, test_gateway.py, test_rules_secrets.py, test_pii_validators.py, test_fs_rules.py, test_chain.py, test_shape.py, test_risk.py, test_triage_fallback.py, test_no_raw_persist.py and test_compliance.py. This matrix expands them with planned test ownership for the remaining IDs. The exact final test path can be refined during implementation without dropping requirement coverage.

## 6. Validation checklist

- [x] Every extracted REQ ID appears exactly once as a primary row.
- [x] Every REQ ID has a planned module, chunk/milestone, test and outcome.
- [x] All NOV IDs are mapped.
- [x] All NFR IDs are mapped to verification.
- [ ] Tests implemented and passing — future implementation gate.
