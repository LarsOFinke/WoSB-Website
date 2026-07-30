from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


BackupOperation = Literal["discover", "configure", "test", "backup", "delete_configuration"]
_HOST_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_REMOTE_DIRECTORY_PATTERN = re.compile(r"^/[A-Za-z0-9._/-]+$")
_HOST_KEY_PATTERN = re.compile(
    r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+$"
)


class BackupDiscoveryRequest(BaseModel):
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(default=22, ge=1, le=65535)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        normalized = value.strip().rstrip(".")
        if not _HOST_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid DNS name or IP address without a URL scheme.")
        return normalized


class BackupConfigurationRequest(BackupDiscoveryRequest):
    username: str = Field(min_length=1, max_length=64)
    remote_directory: str = Field(min_length=1, max_length=512)
    private_key: str | None = Field(default=None, max_length=32768)
    host_key: str = Field(min_length=32, max_length=8192)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip()
        if not _USERNAME_PATTERN.fullmatch(normalized):
            raise ValueError("The SSH username contains unsupported characters.")
        return normalized

    @field_validator("remote_directory")
    @classmethod
    def validate_remote_directory(cls, value: str) -> str:
        normalized = value.strip().rstrip("/") or "/"
        if not _REMOTE_DIRECTORY_PATTERN.fullmatch(normalized):
            raise ValueError("Use an absolute remote path without spaces or shell characters.")
        if any(part in {"", ".", ".."} for part in normalized.split("/")[1:]):
            raise ValueError("The remote directory must not contain dot path segments.")
        return normalized

    @field_validator("private_key")
    @classmethod
    def validate_private_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip() + "\n"
        header = normalized.splitlines()[0]
        if not normalized.startswith("-----BEGIN ") or "PRIVATE KEY-----" not in header:
            raise ValueError("Paste a PEM/OpenSSH private key.")
        if "-----END " not in normalized:
            raise ValueError("The private key footer is missing.")
        return normalized

    @field_validator("host_key")
    @classmethod
    def validate_host_key(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not _HOST_KEY_PATTERN.fullmatch(normalized):
            raise ValueError("Use the discovered SSH public host key.")
        return normalized


class BackupConnectionSummary(BaseModel):
    configured: bool = False
    host: str | None = None
    port: int | None = None
    username: str | None = None
    remote_directory: str | None = None
    host_key_fingerprint: str | None = None
    private_key_configured: bool = False


class BackupArtifact(BaseModel):
    artifact_type: Literal["postgresql", "files"]
    filename: str
    size_bytes: int = Field(ge=0)
    sha256: str = Field(min_length=64, max_length=64)
    remote_path: str


class BackupControlStatus(BaseModel):
    state: str = "idle"
    operation: str = "idle"
    message: str = "No backup operation has been requested yet."
    requested_by: str | None = None
    requested_at: str | None = None
    started_at: str | None = None
    heartbeat_at: str | None = None
    finished_at: str | None = None
    connection: BackupConnectionSummary = Field(default_factory=BackupConnectionSummary)
    discovered_host: str | None = None
    discovered_port: int | None = None
    discovered_host_key: str | None = None
    discovered_fingerprint: str | None = None
    artifacts: list[BackupArtifact] = Field(default_factory=list)
    log_tail: list[str] = Field(default_factory=list)
    request_available: bool = False


class BackupControlRequestResult(BaseModel):
    accepted: bool
    status: BackupControlStatus
