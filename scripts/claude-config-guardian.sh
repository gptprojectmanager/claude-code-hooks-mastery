#!/bin/bash

# 🛡️ Claude Configuration Guardian
# Protects .claude.json from Claude Code's auto-deletion bug
# Issues: #1788, #2763, #1676

set -euo pipefail

CLAUDE_JSON="$HOME/.claude.json"
BACKUP_DIR="$HOME/.claude-backups"
PROJECT_BACKUP="$(pwd)/.claude-backup.json"
LOCK_FILE="/tmp/claude-guardian.lock"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Create lock to prevent multiple instances
if [[ -f "$LOCK_FILE" ]]; then
    if kill -0 "$(cat "$LOCK_FILE")" 2>/dev/null; then
        error "Another instance is already running"
        exit 1
    else
        rm -f "$LOCK_FILE"
    fi
fi
echo $$ > "$LOCK_FILE"

# Cleanup on exit
trap 'rm -f "$LOCK_FILE"' EXIT

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to create backup with deduplication and rate limiting
create_backup() {
    local reason="$1"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local readable_date=$(date '+%Y-%m-%d %H:%M:%S')
    local backup_file="$BACKUP_DIR/claude_${timestamp}_${reason}.json"
    
    # Check if source file exists
    if [[ ! -f "$CLAUDE_JSON" ]]; then
        warn "No claude.json file found to backup"
        return 1
    fi
    
    # RATE LIMITING: Don't backup if last one was too recent (except manual)
    if [[ "$reason" != "manual" ]]; then
        local latest_backup=$(find "$BACKUP_DIR" -name "claude_*.json" -type f -exec stat -f "%m %N" {} \; 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
        if [[ -n "$latest_backup" ]]; then
            local latest_time=$(stat -f%m "$latest_backup" 2>/dev/null || echo "0")
            local current_time=$(date +%s)
            local time_diff=$((current_time - latest_time))
            
            # Don't backup if last one was less than 5 minutes ago (300 seconds)
            if [[ "$time_diff" -lt 300 ]]; then
                log "⏱️  Skipping backup: last one was ${time_diff}s ago (minimum 5 minutes required)"
                return 0
            fi
        fi
    fi
    
    # DEDUPLICATION: Check if content has changed
    local current_hash=$(md5 -q "$CLAUDE_JSON" 2>/dev/null || echo "no-hash")
    local latest_backup=$(find "$BACKUP_DIR" -name "claude_*.json" -type f | sort -r | head -1)
    
    if [[ -n "$latest_backup" ]] && [[ -f "$latest_backup" ]]; then
        local latest_hash=$(md5 -q "$latest_backup" 2>/dev/null || echo "different-hash")
        if [[ "$current_hash" == "$latest_hash" ]]; then
            log "🔄 Skipping backup: content unchanged (hash: ${current_hash:0:8}...)"
            return 0
        fi
    fi
    
    # Create backup (content has changed or is first backup)
    cp "$CLAUDE_JSON" "$backup_file"
    cp "$CLAUDE_JSON" "$PROJECT_BACKUP"  # Also backup to project
    local file_size=$(stat -f%z "$CLAUDE_JSON" 2>/dev/null || echo "0")
    success "Backup created: $(basename $backup_file)"
    log "📅 Date: $readable_date | Size: ${file_size} bytes | Hash: ${current_hash:0:8}..."
    return 0
}

# Function to restore from backup
restore_from_backup() {
    local backup_source="$1"
    
    if [[ -f "$backup_source" ]] && [[ -s "$backup_source" ]]; then
        cp "$backup_source" "$CLAUDE_JSON"
        success "Configuration restored from $backup_source"
        return 0
    else
        error "Backup source is empty or missing: $backup_source"
        return 1
    fi
}


# Function to cleanup old backups and duplicates
cleanup_old_backups() {
    local retention_days=5
    local cutoff_time=$(($(date +%s) - (retention_days * 86400)))
    local cleanup_count=0
    local duplicate_count=0
    
    log "🧹 Cleaning up backups older than $retention_days days and duplicates..."
    
    # First, cleanup by age
    find "$BACKUP_DIR" -name "claude_*.json" -type f | while read -r backup_file; do
        local file_time=$(stat -f%m "$backup_file" 2>/dev/null || echo "0")
        
        if [[ "$file_time" -lt "$cutoff_time" ]]; then
            local readable_date=$(date -r "$file_time" '+%Y-%m-%d %H:%M:%S')
            log "   🗑️  Removing old backup: $(basename "$backup_file") from $readable_date"
            rm -f "$backup_file"
            cleanup_count=$((cleanup_count + 1))
        fi
    done
    
    # Then, cleanup duplicates (keep newest of each identical content)
    log "🔍 Removing duplicate backups..."
    local temp_file="/tmp/claude-cleanup-$$"
    local temp_hashes="/tmp/claude-hashes-$$"
    
    # Create temporary files
    find "$BACKUP_DIR" -name "claude_*.json" -type f -exec stat -f "%m %N" {} \; 2>/dev/null | sort -nr > "$temp_file"
    > "$temp_hashes"  # Create empty hash tracking file
    
    # Track seen hashes and remove duplicates (without associative arrays)
    while read -r file_time file_path; do
        if [[ -f "$file_path" ]]; then
            local file_hash=$(md5 -q "$file_path" 2>/dev/null || echo "no-hash-$$")
            
            # Check if we've seen this hash before
            if grep -q "^${file_hash}:" "$temp_hashes" 2>/dev/null; then
                # This is a duplicate, get the original file name
                local original_file=$(grep "^${file_hash}:" "$temp_hashes" | head -1 | cut -d':' -f2)
                log "   🔄 Removing duplicate: $(basename "$file_path") (same as $(basename "$original_file"))"
                rm -f "$file_path"
                duplicate_count=$((duplicate_count + 1))
            else
                # First time seeing this hash, record it
                echo "${file_hash}:${file_path}" >> "$temp_hashes"
            fi
        fi
    done < "$temp_file"
    
    rm -f "$temp_file" "$temp_hashes"
    
    if [[ "$cleanup_count" -gt 0 ]] || [[ "$duplicate_count" -gt 0 ]]; then
        success "Cleaned up $cleanup_count old backup(s) and $duplicate_count duplicate(s)"
    else
        log "📁 No backups to clean up"
    fi
}

# Main guardian function - STARTUP ONLY MODE
guard_config() {
    log "🛡️  Claude Configuration Guardian - Startup Backup Mode"
    
    # Clean up old backups first (retention policy: 5 days)
    cleanup_old_backups
    
    # Create backup only at startup - NO CONTINUOUS MONITORING
    create_backup "startup"
    
    log "✅ Startup backup completed successfully"
    log "📝 Guardian configured for startup-only backups (no continuous monitoring)"
    log "🔄 To backup manually: $0 backup"
    log "💾 To restore from backup: $0 restore [backup_file]"
    
    # Exit after startup backup - no continuous monitoring
    exit 0
}

# Command handling
case "${1:-guard}" in
    "guard")
        guard_config
        ;;
    "backup")
        create_backup "manual"
        ;;
    "restore")
        if [[ -n "${2:-}" ]]; then
            restore_from_backup "$2"
        elif [[ -f "$PROJECT_BACKUP" ]] && [[ -s "$PROJECT_BACKUP" ]]; then
            restore_from_backup "$PROJECT_BACKUP"
        else
            error "No backup file specified and no project backup available"
            exit 1
        fi
        ;;
    "status")
        echo "📊 Claude Configuration Status (Simplified):"
        echo "Main config: $(if [[ -f "$CLAUDE_JSON" ]] && [[ -s "$CLAUDE_JSON" ]]; then echo "✅ Exists"; else echo "❌ Missing/Empty"; fi)"
        echo "Project backup: $(if [[ -f "$PROJECT_BACKUP" ]] && [[ -s "$PROJECT_BACKUP" ]]; then echo "✅ Exists"; else echo "❌ Missing/Empty"; fi)"
        
        total_backups=$(find "$BACKUP_DIR" -name "claude_*.json" -type f | wc -l | tr -d ' ')
        old_backups=$(find "$BACKUP_DIR" -name "claude_*.json" -type f -mtime +5 | wc -l | tr -d ' ')
        
        echo "Available backups: $total_backups"
        if [[ "$old_backups" -gt 0 ]]; then
            echo "Old backups (>5 days): $old_backups (will be cleaned up automatically)"
        fi
        
        # Show last backup info
        latest_backup=$(find "$BACKUP_DIR" -name "claude_*.json" -type f | sort -r | head -1)
        if [[ -n "$latest_backup" ]]; then
            backup_time=$(stat -f%m "$latest_backup" 2>/dev/null || echo "0")
            hours_ago=$(( ($(date +%s) - backup_time) / 3600 ))
            echo "Last backup: $(basename "$latest_backup") (${hours_ago}h ago)"
        fi
        ;;
    "list-backups")
        echo "📁 Available backups (simplified view):"
        cutoff_time=$(($(date +%s) - (5 * 86400)))
        ls -la "$BACKUP_DIR"/*.json 2>/dev/null | while read -r line; do
            file=$(echo "$line" | awk '{print $NF}')
            file_time=$(stat -f%m "$file" 2>/dev/null || echo "0")
            
            if [[ -s "$file" ]]; then
                if [[ "$file_time" -lt "$cutoff_time" ]]; then
                    echo "🗑️  $line (OLD - will be cleaned up)"
                else
                    echo "✅ $line"
                fi
            else
                echo "❌ $line (EMPTY)"
            fi
        done
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    *)
        echo "Usage: $0 {guard|backup|restore [file]|status|list-backups|cleanup}"
        exit 1
        ;;
esac