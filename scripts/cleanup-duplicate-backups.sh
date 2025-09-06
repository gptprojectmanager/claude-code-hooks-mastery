#!/bin/bash

# 🧹 Claude Backup Duplicate Cleaner - using Desktop Commander  
# Removes duplicate backup files based on content hash

BACKUP_DIR="/Users/sam/.claude-backups"
cleanup_count=0
duplicate_count=0
temp_hashes="/tmp/claude-hashes-$$"

echo "🧹 Starting cleanup of duplicate backups in $BACKUP_DIR"

# Create temporary files for processing
temp_file="/tmp/claude-cleanup-$$"
> "$temp_hashes"  # Create empty hash tracking file

# Get all backup files with their modification time, sorted by newest first
find "$BACKUP_DIR" -name "claude_*.json" -type f -exec stat -f "%m %N" {} \; 2>/dev/null | sort -nr > "$temp_file"

while read -r file_time file_path; do
    if [[ -f "$file_path" ]]; then
        file_hash=$(md5 -q "$file_path" 2>/dev/null || echo "no-hash-$$")
        
        # Check if we've seen this hash before
        if grep -q "^${file_hash}:" "$temp_hashes" 2>/dev/null; then
            # This is a duplicate, get the original file name
            original_file=$(grep "^${file_hash}:" "$temp_hashes" | cut -d':' -f2)
            echo "🔄 Removing duplicate: $(basename "$file_path") (same as $(basename "$original_file"))"
            rm -f "$file_path"
            duplicate_count=$((duplicate_count + 1))
        else
            # First time seeing this hash, record it
            echo "${file_hash}:${file_path}" >> "$temp_hashes"
            echo "✅ Keeping: $(basename "$file_path")"
        fi
    fi
done < "$temp_file"

# Clean up temp files
rm -f "$temp_file" "$temp_hashes"

echo "✅ Cleanup completed: Removed $duplicate_count duplicate backup(s)"

# Show remaining files count
remaining=$(find "$BACKUP_DIR" -name "claude_*.json" -type f | wc -l | tr -d ' ')
echo "📁 Remaining backup files: $remaining"

# Show some statistics
if [[ "$remaining" -gt 0 ]]; then
    oldest=$(find "$BACKUP_DIR" -name "claude_*.json" -type f -exec stat -f "%m %N" {} \; | sort -n | head -1 | cut -d' ' -f2-)
    newest=$(find "$BACKUP_DIR" -name "claude_*.json" -type f -exec stat -f "%m %N" {} \; | sort -n | tail -1 | cut -d' ' -f2-)
    
    echo "📊 Statistics:"
    echo "   Oldest: $(basename "$oldest")"
    echo "   Newest: $(basename "$newest")"
fi