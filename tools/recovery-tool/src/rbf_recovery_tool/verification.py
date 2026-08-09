from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile


_ALLOWED_ROOTS = {"artifacts", "configuration", "system", "manifest.json"}
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_MAX_ARCHIVE_ENTRIES = 20_000
_MAX_UNCOMPRESSED_BYTES = 500 * 1024**3


@dataclass(frozen=True)
class VerificationResult:
    created_at: str
    version: str
    file_count: int
    total_uncompressed_bytes: int
    bundle_sha256: str
    release_artifact: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_sidecar(bundle: Path) -> str:
    checksum_path = Path(f"{bundle}.sha256")
    if not checksum_path.is_file() or checksum_path.stat().st_size > 4096:
        raise RuntimeError(f"Checksum sidecar is missing: {checksum_path.name}")
    lines = [
        line.strip()
        for line in checksum_path.read_text(encoding="ascii").splitlines()
        if line.strip()
    ]
    if len(lines) != 1:
        raise RuntimeError("A checksum sidecar must contain exactly one entry.")
    fields = lines[0].split()
    expected = fields[0].lower() if fields else ""
    if not _SHA256_RE.fullmatch(expected):
        raise RuntimeError("The checksum sidecar contains no valid SHA-256 digest.")
    if len(fields) > 1 and fields[-1].lstrip("*") != bundle.name:
        raise RuntimeError("The checksum sidecar names a different file.")
    actual = sha256_file(bundle)
    if expected != actual:
        raise RuntimeError("The recovery bundle checksum does not match.")
    return actual


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / relative


def _bundled_executable(*names: str) -> Path | None:
    for name in names:
        candidate = resource_path(f"bin/{name}")
        if candidate.is_file():
            return candidate
    return None


def locate_age() -> Path:
    bundled = _bundled_executable("age.exe", "age")
    executable = bundled or shutil.which("age.exe") or shutil.which("age")
    if executable:
        return Path(executable)
    raise RuntimeError("age is neither bundled nor available on PATH.")


def locate_age_keygen() -> Path:
    bundled = _bundled_executable("age-keygen.exe", "age-keygen")
    executable = bundled or shutil.which("age-keygen.exe") or shutil.which("age-keygen")
    if executable:
        return Path(executable)
    raise RuntimeError("age-keygen is neither bundled nor available on PATH.")


def generate_identity(target: Path) -> str:
    target = target.expanduser().resolve()
    if target.exists():
        raise RuntimeError("The selected identity file already exists; refusing to overwrite it.")
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    result = subprocess.run(
        [str(locate_age_keygen()), "-o", str(target)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
        creationflags=flags,
    )
    if result.returncode != 0 or not target.is_file():
        target.unlink(missing_ok=True)
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        suffix = f" ({detail[-1]})" if detail else ""
        raise RuntimeError(f"The age identity could not be created{suffix}.")
    public_key = ""
    for line in (result.stdout + "\n" + result.stderr).splitlines():
        if line.strip().lower().startswith("public key:"):
            public_key = line.split(":", 1)[1].strip()
    if not public_key:
        for line in target.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("# public key:"):
                public_key = line.split(":", 1)[1].strip()
                break
    if not public_key.startswith("age1"):
        target.unlink(missing_ok=True)
        raise RuntimeError("The public age recipient could not be determined.")
    if os.name != "nt":
        os.chmod(target, 0o600)
    return public_key


def decrypt_bundle(bundle: Path, identity: Path, output: Path) -> None:
    if not identity.is_file():
        raise RuntimeError("The private age identity was not found.")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    result = subprocess.run(
        [str(locate_age()), "-d", "-i", str(identity), "-o", str(output), str(bundle)],
        check=False,
        capture_output=True,
        text=True,
        timeout=3600,
        creationflags=flags,
    )
    if result.returncode != 0:
        detail = (result.stderr or "").strip().splitlines()
        suffix = f" ({detail[-1]})" if detail else ""
        raise RuntimeError(f"The recovery bundle could not be decrypted{suffix}.")


def _validated_members(handle: tarfile.TarFile) -> dict[str, tarfile.TarInfo]:
    members = handle.getmembers()
    if len(members) > _MAX_ARCHIVE_ENTRIES:
        raise RuntimeError("The recovery archive contains too many entries.")
    result: dict[str, tarfile.TarInfo] = {}
    total = 0
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or not path.parts or ".." in path.parts:
            raise RuntimeError(f"Unsafe path in recovery archive: {member.name}")
        if path.parts[0] not in _ALLOWED_ROOTS:
            raise RuntimeError(f"Unexpected recovery archive root: {member.name}")
        if not (member.isdir() or member.isfile()):
            raise RuntimeError(f"Links and special files are forbidden: {member.name}")
        normalized = path.as_posix()
        if normalized in result:
            raise RuntimeError(f"Duplicate archive path: {normalized}")
        result[normalized] = member
        if member.isfile():
            total += member.size
            if total > _MAX_UNCOMPRESSED_BYTES:
                raise RuntimeError("The recovery archive exceeds the safety size limit.")
    return result


def _manifest(handle: tarfile.TarFile, members: dict[str, tarfile.TarInfo]) -> dict[str, object]:
    member = members.get("manifest.json")
    if member is None or not member.isfile() or member.size > 10 * 1024**2:
        raise RuntimeError("manifest.json is missing or invalid.")
    source = handle.extractfile(member)
    if source is None:
        raise RuntimeError("manifest.json could not be read.")
    with source:
        payload = json.load(source)
    if not isinstance(payload, dict):
        raise RuntimeError("manifest.json is not an object.")
    if payload.get("schema_version") != 2 or payload.get("kind") != "rbf-disaster-recovery-bundle":
        raise RuntimeError("Unsupported recovery bundle schema.")
    return payload


def verify_plain_archive(archive: Path, bundle_sha256: str = "") -> VerificationResult:
    with tarfile.open(archive, mode="r:gz") as handle:
        members = _validated_members(handle)
        manifest = _manifest(handle, members)
        entries = manifest.get("files")
        if not isinstance(entries, list) or not entries:
            raise RuntimeError("The recovery manifest contains no file inventory.")
        expected: dict[str, dict[str, object]] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise RuntimeError("Invalid recovery manifest entry.")
            relative = str(entry.get("path") or "")
            path = PurePosixPath(relative)
            digest = str(entry.get("sha256") or "").lower()
            if path.is_absolute() or not path.parts or ".." in path.parts:
                raise RuntimeError(f"Unsafe manifest path: {relative}")
            if not _SHA256_RE.fullmatch(digest) or relative in expected:
                raise RuntimeError(f"Invalid or duplicate manifest path: {relative}")
            expected[relative] = entry
        actual_files = {
            name for name, member in members.items() if member.isfile() and name != "manifest.json"
        }
        if actual_files != set(expected):
            raise RuntimeError("Archive and manifest inventories do not match.")
        total = 0
        for relative, entry in expected.items():
            member = members[relative]
            if member.size != int(entry.get("size_bytes", -1)):
                raise RuntimeError(f"File size mismatch: {relative}")
            source = handle.extractfile(member)
            if source is None:
                raise RuntimeError(f"Archive file could not be read: {relative}")
            digest = hashlib.sha256()
            size = 0
            with source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    size += len(block)
                    digest.update(block)
            if size != member.size or digest.hexdigest() != entry["sha256"]:
                raise RuntimeError(f"File verification failed: {relative}")
            total += size
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, dict):
            raise RuntimeError("The artifact map is missing.")
        for key in ("postgres", "files", "release"):
            relative = str(artifacts.get(key) or "")
            if relative not in actual_files:
                raise RuntimeError(f"Recovery artifact is missing: {key}")
        config_prefix = str(artifacts.get("configuration") or "").rstrip("/") + "/"
        if not any(name.startswith(config_prefix) for name in actual_files):
            raise RuntimeError("Recovery configuration is missing.")
        application = manifest.get("application")
        application = application if isinstance(application, dict) else {}
        return VerificationResult(
            created_at=str(manifest.get("created_at") or ""),
            version=str(application.get("version") or ""),
            file_count=len(expected),
            total_uncompressed_bytes=total,
            bundle_sha256=bundle_sha256,
            release_artifact=PurePosixPath(str(artifacts["release"])).name,
        )


def verify_encrypted_bundle(bundle: Path, identity: Path) -> VerificationResult:
    bundle = bundle.expanduser().resolve()
    identity = identity.expanduser().resolve()
    if not bundle.is_file():
        raise RuntimeError("The selected recovery bundle was not found.")
    bundle_sha256 = verify_sidecar(bundle)
    with tempfile.TemporaryDirectory(prefix="rbf-recovery-") as temporary:
        archive = Path(temporary) / "recovery.tar.gz"
        decrypt_bundle(bundle, identity, archive)
        return verify_plain_archive(archive, bundle_sha256)

