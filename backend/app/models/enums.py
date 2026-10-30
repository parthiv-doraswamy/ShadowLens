"""Versioned vocabulary shared by ShadowLens domain contracts."""

from enum import StrEnum


class EventSource(StrEnum):
    SOCKET = "socket"
    PCAP = "pcap"
    LOG = "log"
    GATEWAY = "gateway"
    CONFIG = "config"
    AGENT_HOOK = "agent_hook"


class VisibilityTier(StrEnum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


class RawVisibility(StrEnum):
    METADATA = "metadata"
    SHAPE = "shape"
    CONTENT = "content"


class AIKind(StrEnum):
    CLOUD = "cloud"
    LOCAL = "local"
    GATEWAY = "gateway"
    UNKNOWN = "unknown"
    UNKNOWN_LLM_API = "unknown_llm_api"


class FindingCategory(StrEnum):
    SECRET = "secret"
    PII = "pii"
    AGENT_BEHAVIOR = "agent_behavior"
    SHADOW_AI = "shadow_ai"
    SHAPE_ANOMALY = "shape_anomaly"
    CHAIN = "chain"
    CANARY = "canary"
    POLICY = "policy"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(StrEnum):
    OPEN = "open"
    TRIAGED = "triaged"
    ACCEPTED_RISK = "accepted_risk"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"


class FieldState(StrEnum):
    OBSERVED = "observed"
    DERIVED = "derived"
    UNAVAILABLE = "unavailable"


class CollectionState(StrEnum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"


class ToolKind(StrEnum):
    EXTENSION = "extension"
    DESKTOP = "desktop"
    CLI = "cli"
    AGENT = "agent"
    LOCAL_LLM = "local_llm"
    MCP_SERVER = "mcp_server"
    WEB_APP = "web_app"
    UNKNOWN = "unknown"
