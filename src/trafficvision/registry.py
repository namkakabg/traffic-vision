from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import onnx

from trafficvision.config import AppPaths
from trafficvision.domain import ModelManifest, RegisteredModel


class ModelRegistryError(Exception):
    """Base exception for model registry errors."""


class ModelNotFoundError(ModelRegistryError):
    """Raised when a requested model is not found."""


class ModelIntegrityError(ModelRegistryError):
    """Raised when a model checksum does not match manifest."""


class ModelSecurityError(ModelRegistryError):
    """Raised when an artifact filename breaches path boundary."""


class ModelPromotionError(ModelRegistryError):
    """Raised when candidate model fails promotion criteria."""


@dataclass(frozen=True)
class BackupInfo:
    backup_id: str
    timestamp: str
    model_id: str
    backup_dir: Path
    manifest: ModelManifest


def sha256_file(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file in streaming chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def _atomic_write_bytes(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as tf:
        tf.write(data)
        temp_name = tf.name
    os.replace(temp_name, target)


def _atomic_copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as tf:
        temp_name = tf.name
    shutil.copy2(src, temp_name)
    os.replace(temp_name, dest)


class ModelRegistry:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def install_baseline(self, model_file: Path, manifest: ModelManifest) -> RegisteredModel:
        """Atomically install baseline model and set it as production."""
        self.paths.ensure_directories()

        # 1. Install into baseline directory: artifacts/baseline/<model_id>/
        baseline_dir = self.paths.baseline / manifest.model_id
        baseline_dir.mkdir(parents=True, exist_ok=True)
        baseline_model_path = baseline_dir / manifest.artifact_filename
        baseline_manifest_path = baseline_dir / "manifest.json"

        _atomic_copy_file(model_file, baseline_model_path)
        _atomic_write_bytes(
            baseline_manifest_path,
            manifest.model_dump_json(indent=2).encode("utf-8"),
        )

        # 2. Install into production directory: artifacts/production/
        prod_manifest = manifest.model_copy(
            update={
                "stage": "production",
                "source_model_id": manifest.model_id,
            }
        )
        prod_dir = self.paths.production
        prod_dir.mkdir(parents=True, exist_ok=True)
        prod_model_path = prod_dir / manifest.artifact_filename
        prod_manifest_path = prod_dir / "manifest.json"

        _atomic_copy_file(model_file, prod_model_path)
        _atomic_write_bytes(
            prod_manifest_path,
            prod_manifest.model_dump_json(indent=2).encode("utf-8"),
        )

        prod_model = RegisteredModel(
            manifest=prod_manifest,
            model_path=prod_model_path,
            manifest_path=prod_manifest_path,
        )
        self.verify(prod_model)
        return prod_model

    def get_production(self) -> RegisteredModel:
        """Load and verify current production model."""
        manifest_path = self.paths.production / "manifest.json"
        if not manifest_path.is_file():
            raise ModelNotFoundError(
                f"Production manifest does not exist at {manifest_path}. Please run bootstrap first."
            )

        try:
            content = manifest_path.read_text(encoding="utf-8")
            data = json.loads(content)
            manifest = ModelManifest.model_validate(data)
        except Exception as e:
            raise ModelNotFoundError(f"Failed to read production manifest: {e}") from e

        # Security check: ensure model_path does not escape production directory
        artifact_filename = manifest.artifact_filename
        prod_resolved = self.paths.production.resolve()
        target_path = (self.paths.production / artifact_filename).resolve()

        try:
            target_path.relative_to(prod_resolved)
        except ValueError as err:
            raise ModelSecurityError(
                f"Artifact filename '{artifact_filename}' escapes production directory"
            ) from err

        if not target_path.is_file():
            raise ModelNotFoundError(f"Production model file not found at {target_path}")

        prod_model = RegisteredModel(
            manifest=manifest,
            model_path=target_path,
            manifest_path=manifest_path,
        )
        self.verify(prod_model)
        return prod_model

    def verify(self, model: RegisteredModel) -> None:
        """Verify model file exists and matches its manifest SHA-256."""
        if not model.model_path.is_file():
            raise ModelIntegrityError(f"Model file {model.model_path} does not exist")

        actual_sha = sha256_file(model.model_path)
        if actual_sha != model.manifest.sha256.lower():
            raise ModelIntegrityError(
                f"Model checksum mismatch for {model.manifest.model_id}: "
                f"expected {model.manifest.sha256}, got {actual_sha}"
            )

    def promote_candidate(self, candidate_dir: Path) -> RegisteredModel:
        """Validate candidate model, backup current production, promote candidate, and verify."""
        self.paths.ensure_directories()

        if not candidate_dir.exists() or not candidate_dir.is_dir():
            raise ModelNotFoundError(f"Candidate directory does not exist: {candidate_dir}")

        cand_manifest_path = candidate_dir / "manifest.json"
        if not cand_manifest_path.is_file():
            raise ModelNotFoundError(f"Candidate manifest not found at {cand_manifest_path}")

        try:
            cand_manifest = ModelManifest.model_validate_json(
                cand_manifest_path.read_text(encoding="utf-8")
            )
        except Exception as e:
            raise ModelNotFoundError(f"Invalid candidate manifest: {e}") from e

        # Security check: ensure artifact_filename does not escape candidate directory
        artifact_filename = cand_manifest.artifact_filename
        cand_resolved = candidate_dir.resolve()
        cand_model_path = (candidate_dir / artifact_filename).resolve()

        try:
            cand_model_path.relative_to(cand_resolved)
        except ValueError as err:
            raise ModelSecurityError(
                f"Artifact filename '{artifact_filename}' escapes candidate directory"
            ) from err

        if not cand_model_path.is_file():
            raise ModelNotFoundError(f"Candidate model file not found at {cand_model_path}")

        # Check integrity: sha256
        actual_sha = sha256_file(cand_model_path)
        if actual_sha != cand_manifest.sha256.lower():
            raise ModelIntegrityError(
                f"Candidate model checksum mismatch: expected {cand_manifest.sha256}, got {actual_sha}"
            )

        # Class count verification: exactly 82 classes
        if len(cand_manifest.class_names) != 82:
            raise ModelPromotionError(
                f"Candidate model must have exactly 82 classes, got {len(cand_manifest.class_names)}"
            )

        # Smoke test ONNX model
        try:
            onnx.checker.check_model(str(cand_model_path))
        except Exception as e:
            raise ModelIntegrityError(f"Candidate ONNX smoke test failed: {e}") from e

        # Backup current production model if it exists
        curr_prod_manifest_path = self.paths.production / "manifest.json"
        backup_dir: Path | None = None
        if curr_prod_manifest_path.is_file():
            try:
                curr_manifest = ModelManifest.model_validate_json(
                    curr_prod_manifest_path.read_text(encoding="utf-8")
                )
                curr_model_id = curr_manifest.model_id
            except Exception:
                curr_model_id = "unknown"

            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            base_backup_name = f"{ts}_{curr_model_id}"
            backup_dir = self.paths.backups / base_backup_name
            counter = 1
            while backup_dir.exists():
                backup_dir = self.paths.backups / f"{base_backup_name}_{counter}"
                counter += 1

            backup_dir.mkdir(parents=True, exist_ok=True)
            for item in self.paths.production.iterdir():
                if item.is_file():
                    shutil.copy2(item, backup_dir / item.name)
                elif item.is_dir():
                    shutil.copytree(item, backup_dir / item.name, dirs_exist_ok=True)

        # Promote candidate to production
        prod_manifest = cand_manifest.model_copy(
            update={
                "stage": "production",
                "source_model_id": cand_manifest.model_id,
            }
        )
        self.paths.production.mkdir(parents=True, exist_ok=True)
        prod_model_path = self.paths.production / cand_manifest.artifact_filename
        prod_manifest_path = self.paths.production / "manifest.json"

        try:
            _atomic_copy_file(cand_model_path, prod_model_path)
            _atomic_write_bytes(
                prod_manifest_path,
                prod_manifest.model_dump_json(indent=2).encode("utf-8"),
            )

            # Remove extraneous files from production dir
            for item in self.paths.production.iterdir():
                if item.name not in (cand_manifest.artifact_filename, "manifest.json"):
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)

            prod_model = RegisteredModel(
                manifest=prod_manifest,
                model_path=prod_model_path,
                manifest_path=prod_manifest_path,
            )
            self.verify(prod_model)
        except Exception:
            # Critical: Automatic rollback if post-promotion verification or installation fails
            if backup_dir is not None and backup_dir.is_dir():
                try:
                    self._restore_from_backup_dir(backup_dir)
                except Exception:
                    pass
            else:
                if self.paths.production.is_dir():
                    for item in self.paths.production.iterdir():
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
            raise

        return prod_model

    def list_backups(self) -> list[BackupInfo]:
        """List all valid backups sorted by timestamp descending."""
        if not self.paths.backups.is_dir():
            return []

        backups: list[BackupInfo] = []
        for entry in self.paths.backups.iterdir():
            if entry.is_dir():
                manifest_file = entry / "manifest.json"
                if manifest_file.is_file():
                    try:
                        manifest = ModelManifest.model_validate_json(
                            manifest_file.read_text(encoding="utf-8")
                        )
                    except Exception:
                        continue

                    ts_match = re.match(r"^(\d{8}_\d{6})", entry.name)
                    timestamp = ts_match.group(1) if ts_match else manifest.created_at
                    backups.append(
                        BackupInfo(
                            backup_id=entry.name,
                            timestamp=timestamp,
                            model_id=manifest.model_id,
                            backup_dir=entry,
                            manifest=manifest,
                        )
                    )

        def _sort_key(b: BackupInfo) -> tuple[str, int]:
            try:
                mtime = b.backup_dir.stat().st_mtime_ns
            except Exception:
                mtime = 0
            return (b.timestamp, mtime)

        backups.sort(key=_sort_key, reverse=True)
        return backups

    def rollback_to_backup(self, backup_id: str | None = None) -> RegisteredModel:
        """Rollback production to a specified backup or the most recent backup."""
        self.paths.ensure_directories()

        if backup_id is None:
            backups = self.list_backups()
            if not backups:
                raise ModelNotFoundError("No backups available to rollback")
            return self._restore_from_backup_dir(backups[0].backup_dir)

        # Security check: prevent path traversal via backup_id
        target_dir = (self.paths.backups / backup_id).resolve()
        try:
            target_dir.relative_to(self.paths.backups.resolve())
        except ValueError as err:
            raise ModelSecurityError(f"Backup ID '{backup_id}' escapes backups directory") from err

        if target_dir.is_dir() and (target_dir / "manifest.json").is_file():
            return self._restore_from_backup_dir(target_dir)

        # Search by backup_id matching in list_backups()
        matched = [b for b in self.list_backups() if b.backup_id == backup_id]
        if not matched:
            raise ModelNotFoundError(f"Backup '{backup_id}' not found")

        return self._restore_from_backup_dir(matched[0].backup_dir)

    def _restore_from_backup_dir(self, backup_dir: Path) -> RegisteredModel:
        """Restore production model from a backup directory."""
        manifest_file = backup_dir / "manifest.json"
        if not manifest_file.is_file():
            raise ModelNotFoundError(f"Backup manifest not found in {backup_dir}")

        try:
            backup_manifest = ModelManifest.model_validate_json(
                manifest_file.read_text(encoding="utf-8")
            )
        except Exception as e:
            raise ModelIntegrityError(f"Corrupt backup manifest: {e}") from e

        artifact_filename = backup_manifest.artifact_filename
        backup_resolved = backup_dir.resolve()
        model_file = (backup_dir / artifact_filename).resolve()

        try:
            model_file.relative_to(backup_resolved)
        except ValueError as err:
            raise ModelSecurityError(f"Backup artifact '{artifact_filename}' escapes directory") from err

        if not model_file.is_file():
            raise ModelIntegrityError(f"Backup model file not found at {model_file}")

        actual_sha = sha256_file(model_file)
        if actual_sha != backup_manifest.sha256.lower():
            raise ModelIntegrityError(
                f"Backup checksum mismatch for {backup_manifest.model_id}: "
                f"expected {backup_manifest.sha256}, got {actual_sha}"
            )

        # Restore to production directory atomically
        self.paths.production.mkdir(parents=True, exist_ok=True)
        prod_manifest = backup_manifest.model_copy(update={"stage": "production"})

        prod_model_path = self.paths.production / artifact_filename
        prod_manifest_path = self.paths.production / "manifest.json"

        _atomic_copy_file(model_file, prod_model_path)
        _atomic_write_bytes(
            prod_manifest_path,
            prod_manifest.model_dump_json(indent=2).encode("utf-8"),
        )

        # Remove extraneous files from production
        for item in self.paths.production.iterdir():
            if item.name not in (artifact_filename, "manifest.json"):
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

        prod_model = RegisteredModel(
            manifest=prod_manifest,
            model_path=prod_model_path,
            manifest_path=prod_manifest_path,
        )
        self.verify(prod_model)
        return prod_model

