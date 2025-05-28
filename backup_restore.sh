#!/bin/bash
"""
Backup and Restore Script for Face Recognition Attendance System
Compatible with Raspberry Pi OS Debian 12 (bookworm) 64-bit
"""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/attendance_backups"
DATA_DIR="$SCRIPT_DIR/data"
BACKUP_PREFIX="attendance_backup"
MAX_BACKUPS=10

# Functions
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

create_backup() {
    print_info "Creating backup of attendance data..."
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Generate backup filename with timestamp
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_PREFIX}_${TIMESTAMP}.tar.gz"
    
    # Check if data directory exists
    if [ ! -d "$DATA_DIR" ]; then
        print_error "Data directory not found: $DATA_DIR"
        return 1
    fi
    
    # Create compressed backup
    if tar -czf "$BACKUP_FILE" -C "$SCRIPT_DIR" data/ attendance.csv 2>/dev/null; then
        print_success "Backup created: $BACKUP_FILE"
        
        # Clean up old backups (keep only last MAX_BACKUPS)
        cd "$BACKUP_DIR"
        ls -t ${BACKUP_PREFIX}_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm
        print_info "Old backups cleaned up (keeping last $MAX_BACKUPS)"
        
        return 0
    else
        print_error "Failed to create backup"
        return 1
    fi
}

restore_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        print_info "Available backups:"
        if [ -d "$BACKUP_DIR" ]; then
            ls -la "$BACKUP_DIR"/${BACKUP_PREFIX}_*.tar.gz 2>/dev/null | while read -r line; do
                echo "  $line"
            done
        else
            print_warning "No backup directory found"
            return 1
        fi
        
        echo
        read -p "Enter backup filename (or full path): " backup_file
    fi
    
    # Check if backup file exists
    if [ ! -f "$backup_file" ] && [ -f "$BACKUP_DIR/$backup_file" ]; then
        backup_file="$BACKUP_DIR/$backup_file"
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        return 1
    fi
    
    print_warning "This will overwrite existing attendance data!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Restoring from backup: $backup_file"
        
        # Create backup of current data before restore
        if [ -d "$DATA_DIR" ]; then
            create_backup
        fi
        
        # Extract backup
        if tar -xzf "$backup_file" -C "$SCRIPT_DIR"; then
            print_success "Data restored successfully"
            return 0
        else
            print_error "Failed to restore backup"
            return 1
        fi
    else
        print_info "Restore cancelled"
        return 0
    fi
}

list_backups() {
    print_info "Available backups:"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_warning "No backup directory found"
        return 1
    fi
    
    local count=0
    for backup in "$BACKUP_DIR"/${BACKUP_PREFIX}_*.tar.gz; do
        if [ -f "$backup" ]; then
            local size=$(du -h "$backup" | cut -f1)
            local date=$(stat -c %y "$backup" | cut -d' ' -f1,2 | cut -d'.' -f1)
            printf "  %-40s %s %s\n" "$(basename "$backup")" "$size" "$date"
            ((count++))
        fi
    done
    
    if [ $count -eq 0 ]; then
        print_warning "No backups found"
    else
        print_info "Total backups: $count"
    fi
}

export_csv() {
    print_info "Exporting attendance data to CSV..."
    
    local csv_file="$SCRIPT_DIR/attendance.csv"
    local export_file="$HOME/attendance_export_$(date +%Y%m%d_%H%M%S).csv"
    
    if [ -f "$csv_file" ]; then
        cp "$csv_file" "$export_file"
        print_success "Data exported to: $export_file"
    else
        print_error "No attendance.csv file found"
        return 1
    fi
}

show_stats() {
    print_info "Attendance Data Statistics:"
    
    local csv_file="$SCRIPT_DIR/attendance.csv"
    
    if [ ! -f "$csv_file" ]; then
        print_error "No attendance.csv file found"
        return 1
    fi
    
    local total_records=$(tail -n +2 "$csv_file" | wc -l)
    local unique_people=$(tail -n +2 "$csv_file" | cut -d',' -f1 | sort | uniq | wc -l)
    local date_range=$(tail -n +2 "$csv_file" | cut -d',' -f3 | sort | (head -n1; tail -n1) | tr '\n' ' ')
    
    echo "  Total records: $total_records"
    echo "  Unique people: $unique_people"
    echo "  Date range: $date_range"
    
    print_info "Recent entries (last 5):"
    tail -n 5 "$csv_file" | while IFS=, read -r name time date status; do
        echo "  $date $time - $name ($status)"
    done
}

show_help() {
    echo "Face Recognition Attendance System - Backup & Restore Tool"
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  backup          Create a backup of attendance data"
    echo "  restore [FILE]  Restore from backup (interactive if no file specified)"
    echo "  list            List all available backups"
    echo "  export          Export attendance data to CSV"
    echo "  stats           Show attendance data statistics"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 backup"
    echo "  $0 restore"
    echo "  $0 restore attendance_backup_20241201_120000.tar.gz"
    echo "  $0 list"
}

# Main execution
case "$1" in
    backup)
        create_backup
        ;;
    restore)
        restore_backup "$2"
        ;;
    list)
        list_backups
        ;;
    export)
        export_csv
        ;;
    stats)
        show_stats
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Face Recognition Attendance System - Backup & Restore"
        echo "======================================================"
        echo ""
        echo "Choose an option:"
        echo "1) Create backup"
        echo "2) Restore backup"
        echo "3) List backups"
        echo "4) Export to CSV"
        echo "5) Show statistics"
        echo "6) Help"
        echo "0) Exit"
        echo ""
        read -p "Enter choice [0-6]: " choice
        
        case $choice in
            1) create_backup ;;
            2) restore_backup ;;
            3) list_backups ;;
            4) export_csv ;;
            5) show_stats ;;
            6) show_help ;;
            0) exit 0 ;;
            *) print_error "Invalid choice" ;;
        esac
        ;;
esac
