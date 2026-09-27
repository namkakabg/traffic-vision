from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

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
