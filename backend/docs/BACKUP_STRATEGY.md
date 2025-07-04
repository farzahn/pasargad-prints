# Database Backup Strategy - Pasargad Prints

## Overview

This document outlines the comprehensive database backup strategy for Pasargad Prints production environment. The strategy ensures data integrity, availability, and disaster recovery capabilities.

## Backup Components

### 1. Automated Database Backups

- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 30 days (configurable)
- **Storage**: AWS S3 with encryption
- **Compression**: gzip compression
- **Encryption**: AES-256-CBC encryption

### 2. Backup Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │───▶│  Backup Script  │───▶│     AWS S3      │
│   Production    │    │  (Automated)    │    │   (Encrypted)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Notifications  │
                       │  (Email/Slack)  │
                       └─────────────────┘
```

## Backup Scripts

### 1. Database Backup Script

**Location**: `/app/scripts/backup_database.sh`

**Features**:
- Full database backup using `pg_dump`
- Compression using gzip
- Encryption using OpenSSL
- S3 upload with metadata
- Automatic cleanup of old backups
- Comprehensive logging
- Error handling and notifications

**Usage**:
```bash
# Run manual backup
./scripts/backup_database.sh

# View backup logs
tail -f /var/log/pasargad_prints_backup.log
```

### 2. Database Restore Script

**Location**: `/app/scripts/restore_database.sh`

**Features**:
- Download and decrypt backups from S3
- Restore to existing or new database
- Connection management
- Verification of restored data
- Comprehensive logging

**Usage**:
```bash
# List available backups
./scripts/restore_database.sh --list

# Restore specific backup
./scripts/restore_database.sh --file backup_20240101_120000.sql.gz.enc

# Restore to new database
./scripts/restore_database.sh --new-db test_db --file backup.sql.gz.enc

# Force restore without confirmation
./scripts/restore_database.sh --force --file backup.sql.gz.enc
```

### 3. Notification Scripts

**Email Notifications**: `/app/scripts/send_backup_notification.py`
**Restore Notifications**: `/app/scripts/send_restore_notification.py`

## Backup Schedule

### Automated Backups

Backups are scheduled using cron jobs:

```bash
# Daily backup at 2:00 AM UTC
0 2 * * * /app/scripts/backup_database.sh

# Weekly backup verification at 3:00 AM UTC on Sundays
0 3 * * 0 /app/scripts/verify_backup.sh

# Monthly cleanup of old backups
0 4 1 * * /app/scripts/cleanup_old_backups.sh
```

### Manual Backups

Manual backups can be triggered before:
- Major deployments
- Database migrations
- System maintenance
- Testing activities

## Storage Configuration

### AWS S3 Setup

```bash
# S3 Bucket Configuration
BACKUP_S3_BUCKET=your-backup-bucket-name
S3_PREFIX=database-backups

# Storage Classes
- Recent backups (0-30 days): STANDARD_IA
- Archived backups (30-90 days): GLACIER
- Long-term storage (90+ days): DEEP_ARCHIVE
```

### Encryption Configuration

```bash
# Encryption Settings
BACKUP_ENCRYPTION_KEY=your-32-byte-encryption-key
ENCRYPTION_ALGORITHM=AES-256-CBC

# S3 Server-Side Encryption
S3_SERVER_SIDE_ENCRYPTION=AES256
```

## Backup Verification

### Automated Verification

1. **File Integrity**: MD5 checksums
2. **Encryption Verification**: Decryption test
3. **Database Validation**: Test restore to temporary database
4. **Size Verification**: Compare with previous backups

### Manual Verification

```bash
# Verify backup integrity
./scripts/verify_backup.sh --file backup_20240101_120000.sql.gz.enc

# Test restore to temporary database
./scripts/restore_database.sh --new-db temp_test --file backup.sql.gz.enc
```

## Monitoring and Alerting

### Backup Status Monitoring

- **Success Notifications**: Email and Slack
- **Failure Alerts**: Immediate notification to administrators
- **Missing Backup Alerts**: Daily check for successful backups
- **Storage Monitoring**: S3 bucket usage and costs

### Metrics Tracked

1. **Backup Success Rate**: Percentage of successful backups
2. **Backup Size**: Monitor growth trends
3. **Backup Duration**: Track performance
4. **Recovery Time**: Measure restore performance
5. **Storage Costs**: Monitor S3 usage and costs

## Disaster Recovery

### Recovery Point Objective (RPO)

- **Maximum Data Loss**: 24 hours
- **Backup Frequency**: Daily
- **Critical Data**: Real-time replication for orders and payments

### Recovery Time Objective (RTO)

- **Database Restore**: 2-4 hours
- **Application Recovery**: 1-2 hours
- **Full Service Recovery**: 4-6 hours

### Recovery Procedures

1. **Identify Failure**: Monitoring alerts
2. **Assess Impact**: Determine scope of data loss
3. **Select Backup**: Choose appropriate backup point
4. **Execute Restore**: Run restore procedures
5. **Verify Recovery**: Test application functionality
6. **Resume Operations**: Bring services online

## Security Considerations

### Encryption

- **At Rest**: AES-256-CBC encryption of backup files
- **In Transit**: TLS/SSL for S3 uploads
- **Key Management**: Secure key storage and rotation

### Access Control

- **IAM Roles**: Principle of least privilege
- **S3 Bucket Policies**: Restrict access to backup files
- **Audit Logging**: Track all backup operations

### Compliance

- **Data Retention**: 30-day retention policy
- **Audit Trail**: Complete logging of all operations
- **Access Monitoring**: Regular review of access patterns

## Backup Testing

### Regular Testing Schedule

- **Monthly**: Full restore test to staging environment
- **Quarterly**: Disaster recovery drill
- **Annually**: Complete recovery scenario testing

### Test Procedures

1. **Functional Testing**: Verify data integrity
2. **Performance Testing**: Measure restore times
3. **Application Testing**: Ensure application compatibility
4. **User Acceptance**: Validate business functionality

## Troubleshooting

### Common Issues

1. **Backup Failure**: Check disk space and permissions
2. **S3 Upload Failure**: Verify AWS credentials and network
3. **Encryption Failure**: Check encryption key availability
4. **Large Backup Size**: Review data retention policies

### Error Codes

- **Exit Code 1**: General backup failure
- **Exit Code 2**: Database connection failure
- **Exit Code 3**: S3 upload failure
- **Exit Code 4**: Encryption failure
- **Exit Code 5**: Cleanup failure

### Log Files

- **Backup Log**: `/var/log/pasargad_prints_backup.log`
- **Restore Log**: `/var/log/pasargad_prints_restore.log`
- **Notification Log**: `/var/log/pasargad_prints_backup_notifications.log`

## Maintenance

### Regular Tasks

1. **Monthly**: Review backup success rates
2. **Quarterly**: Update backup scripts and documentation
3. **Annually**: Review and update disaster recovery procedures
4. **As Needed**: Rotate encryption keys

### Performance Optimization

- **Parallel Backups**: For large databases
- **Incremental Backups**: For frequently changing data
- **Compression Optimization**: Balance size vs. speed
- **Network Optimization**: Optimize S3 transfer speeds

## Cost Management

### Storage Optimization

- **Lifecycle Policies**: Automatic transition to cheaper storage
- **Compression**: Reduce storage requirements
- **Deduplication**: Eliminate redundant data
- **Retention Policies**: Remove old backups automatically

### Monitoring Costs

- **S3 Storage Costs**: Monthly usage reports
- **Data Transfer Costs**: Monitor upload/download charges
- **Request Costs**: Track API usage
- **Overall Budget**: Set alerts for cost overruns

## Contact Information

### Backup Administrator

- **Primary**: DevOps Team (devops@pasargadprints.com)
- **Secondary**: System Administrator (admin@pasargadprints.com)
- **Emergency**: On-call Engineer (oncall@pasargadprints.com)

### Escalation Matrix

1. **Level 1**: Automated alerts to DevOps team
2. **Level 2**: Manager notification after 1 hour
3. **Level 3**: Executive notification after 4 hours
4. **Level 4**: Customer notification if service impact

## Documentation Updates

- **Version**: 1.0
- **Last Updated**: 2024-01-01
- **Next Review**: 2024-04-01
- **Owner**: DevOps Team