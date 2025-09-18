#!/bin/bash

# TenderPulse Database Backup Script
# Usage: ./scripts/backup.sh [backup_name]

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_NAME="${1:-tenderpulse-$(date +%Y%m%d-%H%M%S)}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "🗄️  Starting TenderPulse database backup..."
echo "📅 Backup name: $BACKUP_NAME"
echo "📁 Backup directory: $BACKUP_DIR"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable not set"
    exit 1
fi

# Create backup
BACKUP_FILE="$BACKUP_DIR/$BACKUP_NAME.sql"
echo "💾 Creating backup: $BACKUP_FILE"

pg_dump "$DATABASE_URL" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=custom \
    --file="$BACKUP_FILE.custom"

# Also create plain SQL backup for easier inspection
pg_dump "$DATABASE_URL" \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=plain \
    --file="$BACKUP_FILE"

# Compress backups
echo "🗜️  Compressing backups..."
gzip "$BACKUP_FILE"
gzip "$BACKUP_FILE.custom"

# Verify backup
if [ -f "$BACKUP_FILE.gz" ] && [ -f "$BACKUP_FILE.custom.gz" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE.gz" | cut -f1)
    echo "✅ Backup completed successfully!"
    echo "📊 Backup size: $BACKUP_SIZE"
    echo "📁 Files created:"
    echo "   - $BACKUP_FILE.gz (plain SQL)"
    echo "   - $BACKUP_FILE.custom.gz (pg_restore format)"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Clean up old backups (older than RETENTION_DAYS)
echo "🧹 Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "tenderpulse-*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "tenderpulse-*.sql.custom.gz" -mtime +$RETENTION_DAYS -delete

# List remaining backups
echo "📋 Current backups:"
ls -lh "$BACKUP_DIR"/tenderpulse-*.sql.gz 2>/dev/null || echo "   No backups found"

echo "🎉 Backup process completed!"

# Optional: Upload to cloud storage (uncomment and configure as needed)
# if [ -n "$AWS_S3_BUCKET" ]; then
#     echo "☁️  Uploading to S3..."
#     aws s3 cp "$BACKUP_FILE.gz" "s3://$AWS_S3_BUCKET/backups/"
#     aws s3 cp "$BACKUP_FILE.custom.gz" "s3://$AWS_S3_BUCKET/backups/"
# fi