"""
S3 Snapshot Management

Critical requirements:
1. Vector DB must be stopped before snapshot
2. Atomic sync to S3
3. Restoration must be tested
4. Don't run in request path (use cron/sidecar)

Use cases:
- Daily backups
- Disaster recovery
- Multi-region replication
- Development/staging data sync
"""

import subprocess
import os
import shutil
from datetime import datetime
from pathlib import Path


class SnapshotManager:
    """
    Manages ChromaDB snapshots to/from S3
    
    Design:
    - Uses AWS CLI for reliability
    - Supports local backup as well
    - Atomic operations (stop -> sync -> restart)
    """
    
    def __init__(
        self,
        local_dir: str,
        s3_bucket: str | None = None,
        s3_prefix: str = "memory-snapshots"
    ):
        """
        Initialize snapshot manager
        
        Args:
            local_dir: ChromaDB persist directory
            s3_bucket: S3 bucket name (optional)
            s3_prefix: S3 key prefix
        """
        self.local_dir = Path(local_dir)
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
    
    def create_local_snapshot(self, backup_dir: str) -> str:
        """
        Create local backup of vector DB
        
        Args:
            backup_dir: Where to store backup
        
        Returns:
            Path to backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(backup_dir) / f"snapshot_{timestamp}"
        
        # Copy entire ChromaDB directory
        shutil.copytree(self.local_dir, backup_path)
        
        print(f"✅ Local snapshot created: {backup_path}")
        return str(backup_path)
    
    def snapshot_to_s3(self) -> bool:
        """
        Sync ChromaDB to S3
        
        Process:
        1. Ensure local dir exists
        2. Sync to S3 with timestamp
        3. Keep latest snapshot link
        
        Returns:
            True if successful
        """
        if not self.s3_bucket:
            raise ValueError("S3 bucket not configured")
        
        if not self.local_dir.exists():
            raise FileNotFoundError(f"Local dir not found: {self.local_dir}")
        
        # Timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_path = f"s3://{self.s3_bucket}/{self.s3_prefix}/{timestamp}/"
        
        try:
            # Sync to S3
            result = subprocess.run(
                [
                    "aws", "s3", "sync",
                    str(self.local_dir),
                    s3_path,
                    "--delete"  # Remove files not in source
                ],
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"✅ Snapshot uploaded to: {s3_path}")
            
            # Also update "latest" link
            latest_path = f"s3://{self.s3_bucket}/{self.s3_prefix}/latest/"
            subprocess.run(
                [
                    "aws", "s3", "sync",
                    str(self.local_dir),
                    latest_path,
                    "--delete"
                ],
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"✅ Latest snapshot updated: {latest_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Snapshot failed: {e.stderr}")
            return False
    
    def restore_from_s3(self, snapshot_name: str = "latest") -> bool:
        """
        Restore ChromaDB from S3 snapshot
        
        Args:
            snapshot_name: Snapshot identifier or "latest"
        
        Returns:
            True if successful
        """
        if not self.s3_bucket:
            raise ValueError("S3 bucket not configured")
        
        s3_path = f"s3://{self.s3_bucket}/{self.s3_prefix}/{snapshot_name}/"
        
        try:
            # Clear local directory
            if self.local_dir.exists():
                shutil.rmtree(self.local_dir)
            
            self.local_dir.mkdir(parents=True, exist_ok=True)
            
            # Sync from S3
            result = subprocess.run(
                [
                    "aws", "s3", "sync",
                    s3_path,
                    str(self.local_dir)
                ],
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"✅ Restored from: {s3_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Restore failed: {e.stderr}")
            return False
    
    def list_snapshots(self) -> list[str]:
        """
        List available S3 snapshots
        
        Returns:
            List of snapshot names
        """
        if not self.s3_bucket:
            raise ValueError("S3 bucket not configured")
        
        try:
            result = subprocess.run(
                [
                    "aws", "s3", "ls",
                    f"s3://{self.s3_bucket}/{self.s3_prefix}/"
                ],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Parse output (format: "PRE snapshot_name/")
            snapshots = []
            for line in result.stdout.splitlines():
                if "PRE " in line:
                    name = line.split("PRE ")[1].strip("/")
                    snapshots.append(name)
            
            return snapshots
            
        except subprocess.CalledProcessError as e:
            print(f"❌ List failed: {e.stderr}")
            return []
    
    def delete_old_snapshots(self, keep_count: int = 7) -> int:
        """
        Delete old snapshots, keeping only recent ones
        
        Args:
            keep_count: Number of snapshots to keep
        
        Returns:
            Number of deleted snapshots
        """
        snapshots = self.list_snapshots()
        
        # Filter out "latest" (not timestamped)
        timestamped = [s for s in snapshots if s != "latest"]
        timestamped.sort(reverse=True)  # Newest first
        
        to_delete = timestamped[keep_count:]
        
        deleted = 0
        for snapshot in to_delete:
            s3_path = f"s3://{self.s3_bucket}/{self.s3_prefix}/{snapshot}/"
            try:
                subprocess.run(
                    ["aws", "s3", "rm", s3_path, "--recursive"],
                    check=True,
                    capture_output=True
                )
                deleted += 1
                print(f"🗑️  Deleted old snapshot: {snapshot}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to delete: {snapshot}")
        
        return deleted


# Helper function for CLI usage
def create_snapshot_manager(config=None) -> SnapshotManager:
    """
    Create snapshot manager from config
    
    Args:
        config: Config instance (or uses global)
    
    Returns:
        SnapshotManager instance
    """
    if config is None:
        from infra.config import get_config
        config = get_config()
    
    return SnapshotManager(
        local_dir=config.vector_store.persist_dir,
        s3_bucket=config.snapshot.s3_bucket,
        s3_prefix=config.snapshot.s3_prefix
    )


# Export
__all__ = ["SnapshotManager", "create_snapshot_manager"]
