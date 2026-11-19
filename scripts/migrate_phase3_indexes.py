"""
Database Migration: Phase 3 Indexes
Created: 2026-05-21
Purpose: Add composite indexes for performance optimization

This migration adds 4 new indexes to improve query performance:
1. idx_visit_service_name - For service name filtering
2. idx_visit_payment_status - For payment status queries
3. idx_herbal_tx_visit_group - For visit-based herbal queries
4. idx_herbal_tx_date_type - For transaction reports
"""

import sqlite3
import os
from datetime import datetime

def run_migration(db_path="data.db"):
    """Run Phase 3 index migration."""
    print(f"[{datetime.now()}] Starting Phase 3 index migration...")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if indexes already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        existing_indexes = {row[0] for row in cursor.fetchall()}
        
        indexes_to_create = [
            ("idx_visit_service_name", "CREATE INDEX IF NOT EXISTS idx_visit_service_name ON visits(service_name)"),
            ("idx_visit_payment_status", "CREATE INDEX IF NOT EXISTS idx_visit_payment_status ON visits(payment_status, date)"),
            ("idx_herbal_tx_visit_group", "CREATE INDEX IF NOT EXISTS idx_herbal_tx_visit_group ON herbal_transactions(visit_id, sale_group_id)"),
            ("idx_herbal_tx_date_type", "CREATE INDEX IF NOT EXISTS idx_herbal_tx_date_type ON herbal_transactions(date, transaction_type)"),
        ]
        
        created_count = 0
        skipped_count = 0
        
        for index_name, sql in indexes_to_create:
            if index_name in existing_indexes:
                print(f"  ⏭️  SKIP: {index_name} (already exists)")
                skipped_count += 1
            else:
                print(f"  ⚙️  Creating index: {index_name}...")
                cursor.execute(sql)
                print(f"  ✅ Created: {index_name}")
                created_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n[{datetime.now()}] Migration completed successfully!")
        print(f"  Created: {created_count} indexes")
        print(f"  Skipped: {skipped_count} indexes (already exist)")
        print(f"  Total: {len(indexes_to_create)} indexes")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Migration failed: {e}")
        return False

def verify_indexes(db_path="data.db"):
    """Verify that all indexes were created successfully."""
    print(f"\n[{datetime.now()}] Verifying indexes...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        expected_indexes = [
            "idx_visit_service_name",
            "idx_visit_payment_status",
            "idx_herbal_tx_visit_group",
            "idx_herbal_tx_date_type",
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        existing_indexes = {row[0] for row in cursor.fetchall()}
        
        all_present = True
        for index_name in expected_indexes:
            if index_name in existing_indexes:
                print(f"  ✅ {index_name}")
            else:
                print(f"  ❌ {index_name} (MISSING)")
                all_present = False
        
        conn.close()
        
        if all_present:
            print(f"\n✅ All indexes verified successfully!")
        else:
            print(f"\n⚠️  Some indexes are missing!")
        
        return all_present
        
    except Exception as e:
        print(f"\nERROR: Verification failed: {e}")
        return False

def rollback_migration(db_path="data.db"):
    """Rollback Phase 3 indexes (drop them)."""
    print(f"[{datetime.now()}] Rolling back Phase 3 indexes...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        indexes_to_drop = [
            "idx_visit_service_name",
            "idx_visit_payment_status",
            "idx_herbal_tx_visit_group",
            "idx_herbal_tx_date_type",
        ]
        
        dropped_count = 0
        
        for index_name in indexes_to_drop:
            try:
                cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                print(f"  ✅ Dropped: {index_name}")
                dropped_count += 1
            except Exception as e:
                print(f"  ⚠️  Failed to drop {index_name}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n[{datetime.now()}] Rollback completed!")
        print(f"  Dropped: {dropped_count} indexes")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        db_path = sys.argv[2] if len(sys.argv) > 2 else "data.db"
        
        if command == "migrate":
            success = run_migration(db_path)
            sys.exit(0 if success else 1)
        elif command == "verify":
            success = verify_indexes(db_path)
            sys.exit(0 if success else 1)
        elif command == "rollback":
            success = rollback_migration(db_path)
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown command: {command}")
            print("Usage: python migrate_phase3_indexes.py [migrate|verify|rollback] [db_path]")
            sys.exit(1)
    else:
        # Default: run migration
        print("=" * 60)
        print("Phase 3 Index Migration")
        print("=" * 60)
        success = run_migration()
        if success:
            verify_indexes()
        sys.exit(0 if success else 1)
