#!/bin/bash

# Database backup script for Procurement Copilot
# This script creates nightly backups of the PostgreSQL database

set -e

# Configuration
BACKUP_DIR="/backups"
DB_NAME="${POSTGRES_DB:-procurement_copilot}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
BACKUP_FILE="$BACKUP_DIR/procurement_copilot_$(date +%Y%m%d_%H%M%S).sql"

# Create backup
echo "Starting database backup..."
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose \
    --no-password \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_FILE"

# Compress the backup
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "Backup completed: $BACKUP_FILE"

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup size: $BACKUP_SIZE"

# Clean up old backups (keep only last 30 days)
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "procurement_copilot_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# List remaining backups
echo "Remaining backups:"
ls -lh "$BACKUP_DIR"/procurement_copilot_*.sql.gz 2>/dev/null || echo "No backups found"

# Optional: Upload to S3 (uncomment and configure if needed)
# if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
#     echo "Uploading backup to S3..."
#     aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/backups/$(basename "$BACKUP_FILE")"
#     echo "Backup uploaded to S3"
# fi

echo "Backup process completed successfully"
