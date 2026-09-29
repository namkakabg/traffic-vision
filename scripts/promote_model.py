#!/usr/bin/env python3
"""CLI operator script to promote candidate models, rollback, or list backups."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to sys.path so script can run from any working directory
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from trafficvision.config import AppPaths  # noqa: E402
from trafficvision.registry import (  # noqa: E402
    ModelIntegrityError,
    ModelNotFoundError,
    ModelPromotionError,
    ModelRegistry,
    ModelSecurityError,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote candidate model to production or rollback to a previous backup."
    )
    parser.add_argument(
        "--candidate-dir",
        type=Path,
        default=None,
        help="Path to candidate directory containing model.onnx and manifest.json to promote.",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback production model to backup (most recent or specified by --backup-id).",
    )
    parser.add_argument(
        "--backup-id",
        type=str,
        default=None,
        help="Specific backup ID folder name to rollback to (optional).",
    )
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="List all existing automated model backups.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=repo_root,
        help="Root directory of the project (default: repo root).",
    )

    args = parser.parse_args()
    project_root = args.project_root.resolve()
    paths = AppPaths.from_root(project_root)
    paths.ensure_directories()
    registry = ModelRegistry(paths)

    # 1. Handle --list-backups
    if args.list_backups:
        backups = registry.list_backups()
        print(f"[*] Found {len(backups)} backup(s) in {paths.backups}:")
        if not backups:
            print("    (no backups found)")
            return 0

        for b in backups:
            print(
                f"    - ID: {b.backup_id} | Model: {b.model_id} | Timestamp: {b.timestamp} | Classes: {len(b.manifest.class_names)}"
            )
        return 0

    # 2. Handle --rollback
    if args.rollback:
        target_info = f"backup '{args.backup_id}'" if args.backup_id else "most recent backup"
        print(f"[*] Rolling back production model to {target_info}...")
        try:
            restored = registry.rollback_to_backup(args.backup_id)
        except (ModelNotFoundError, ModelSecurityError, ModelIntegrityError) as exc:
            print(f"[!] Rollback failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"[!] Unexpected error during rollback: {exc}", file=sys.stderr)
            return 1

        print("[+] Rollback successful:")
        print(f"    Model ID:    {restored.manifest.model_id}")
        print(f"    Stage:       {restored.manifest.stage}")
        print(f"    Classes:     {len(restored.manifest.class_names)} classes")
        print(f"    Model Path:  {restored.model_path}")
        print(f"    Manifest:    {restored.manifest_path}")
        return 0

    # 3. Handle --candidate-dir
    if args.candidate_dir is not None:
        candidate_path = args.candidate_dir.resolve()
        if not candidate_path.is_dir():
            print(
                f"[!] Error: Candidate directory does not exist: {candidate_path}", file=sys.stderr
            )
            return 1

        print(f"[*] Promoting candidate model from: {candidate_path}")
        try:
            promoted = registry.promote_candidate(candidate_path)
        except (
            ModelPromotionError,
            ModelIntegrityError,
            ModelSecurityError,
            FileNotFoundError,
        ) as exc:
            print(f"[!] Promotion failed: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"[!] Unexpected error during promotion: {exc}", file=sys.stderr)
            return 1

        print("[+] Candidate model successfully promoted to production:")
        print(f"    Model ID:    {promoted.manifest.model_id}")
        print(f"    Stage:       {promoted.manifest.stage}")
        print(f"    Classes:     {len(promoted.manifest.class_names)} classes")
        print(f"    Backend:     {promoted.manifest.backend}")
        print(f"    SHA-256:     {promoted.manifest.sha256}")
        print(f"    Model Path:  {promoted.model_path}")
        print(f"    Manifest:    {promoted.manifest_path}")
        return 0

    print(
        "[!] Error: Must specify one of --candidate-dir <path>, --rollback, or --list-backups.",
        file=sys.stderr,
    )
    parser.print_help(file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
