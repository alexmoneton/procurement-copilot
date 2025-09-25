#!/usr/bin/env python3
"""
TenderPulse Backup and Logging System
Comprehensive backup, logging, and monitoring system

Features:
- Automated database backups
- CSV data exports
- Log file management
- Performance monitoring
- Error tracking and alerting
- Data retention policies
- Cloud backup integration
- System health monitoring
"""

import os
import json
import sqlite3
import gzip
import shutil
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psutil
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('backup_system')

@dataclass
class BackupConfig:
    """Backup configuration"""
    backup_dir: str = "backups"
    retention_days: int = 30
    compression: bool = True
    cloud_backup: bool = False
    cloud_provider: str = "aws_s3"  # aws_s3, google_cloud, azure
    email_alerts: bool = True
    alert_email: str = "admin@tenderpulse.eu"
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    database_size: int
    total_prospects: int
    daily_prospects: int
    email_success_rate: float
    error_count: int

class DatabaseBackupManager:
    """Database backup management"""
    
    def __init__(self, db_path: str, config: BackupConfig):
        self.db_path = db_path
        self.config = config
        self.backup_dir = config.backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_full_backup(self) -> str:
        """Create full database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"ted_prospects_full_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Compress if enabled
            if self.config.compression:
                compressed_path = f"{backup_path}.gz"
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_path)
                backup_path = compressed_path
            
            logger.info(f"Full database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating full backup: {e}")
            raise
    
    def create_incremental_backup(self) -> str:
        """Create incremental backup (only new/changed data)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"ted_prospects_incremental_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get data modified in last 24 hours
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            
            # Export recent prospects
            cursor.execute('''
                SELECT * FROM prospects 
                WHERE updated_at > ? OR created_at > ?
            ''', (yesterday, yesterday))
            
            columns = [description[0] for description in cursor.description]
            recent_prospects = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Export recent email campaigns
            cursor.execute('''
                SELECT * FROM email_campaigns 
                WHERE created_at > ?
            ''', (yesterday,))
            
            columns = [description[0] for description in cursor.description]
            recent_campaigns = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            
            # Create incremental backup data
            backup_data = {
                'timestamp': timestamp,
                'type': 'incremental',
                'prospects': recent_prospects,
                'campaigns': recent_campaigns,
                'backup_date': datetime.now().isoformat()
            }
            
            # Save to file
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            # Compress if enabled
            if self.config.compression:
                compressed_path = f"{backup_path}.gz"
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_path)
                backup_path = compressed_path
            
            logger.info(f"Incremental backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating incremental backup: {e}")
            raise
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            # Handle compressed backups
            if backup_path.endswith('.gz'):
                temp_path = backup_path[:-3]  # Remove .gz
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_path = temp_path
            
            # Create backup of current database
            current_backup = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.db_path, current_backup)
            
            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            
            # Clean up temp file if it was compressed
            if temp_path != backup_path:
                os.remove(temp_path)
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Clean up old backup files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        logger.info(f"Deleted old backup: {filename}")
            
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")

class DataExporter:
    """Data export utilities"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def export_prospects_csv(self, output_path: str, filters: Dict = None) -> bool:
        """Export prospects to CSV"""
        try:
            import csv
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query with filters
            query = "SELECT * FROM prospects WHERE 1=1"
            params = []
            
            if filters:
                if filters.get('status'):
                    query += " AND status = ?"
                    params.append(filters['status'])
                
                if filters.get('country'):
                    query += " AND country = ?"
                    params.append(filters['country'])
                
                if filters.get('date_from'):
                    query += " AND created_at >= ?"
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    query += " AND created_at <= ?"
                    params.append(filters['date_to'])
            
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            prospects = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            
            # Write to CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if prospects:
                    writer = csv.DictWriter(f, fieldnames=prospects[0].keys())
                    writer.writeheader()
                    writer.writerows(prospects)
            
            logger.info(f"Exported {len(prospects)} prospects to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting prospects: {e}")
            return False
    
    def export_campaigns_csv(self, output_path: str) -> bool:
        """Export email campaigns to CSV"""
        try:
            import csv
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT c.*, p.company_name, p.email, p.country, p.sector
                FROM email_campaigns c
                JOIN prospects p ON c.prospect_id = p.id
                ORDER BY c.created_at DESC
            ''')
            
            columns = [description[0] for description in cursor.description]
            campaigns = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            
            # Write to CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if campaigns:
                    writer = csv.DictWriter(f, fieldnames=campaigns[0].keys())
                    writer.writeheader()
                    writer.writerows(campaigns)
            
            logger.info(f"Exported {len(campaigns)} campaigns to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting campaigns: {e}")
            return False
    
    def export_analytics_json(self, output_path: str) -> bool:
        """Export analytics data to JSON"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get comprehensive analytics
            analytics = {}
            
            # Prospect statistics
            cursor.execute('SELECT status, COUNT(*) FROM prospects GROUP BY status')
            analytics['prospects_by_status'] = dict(cursor.fetchall())
            
            # Sector performance
            cursor.execute('''
                SELECT sector, COUNT(*) as total, 
                       AVG(pain_level) as avg_pain_level,
                       COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted
                FROM prospects 
                GROUP BY sector
                ORDER BY total DESC
            ''')
            analytics['sector_performance'] = [
                dict(zip(['sector', 'total', 'avg_pain_level', 'converted'], row))
                for row in cursor.fetchall()
            ]
            
            # Country performance
            cursor.execute('''
                SELECT country, COUNT(*) as total,
                       AVG(pain_level) as avg_pain_level,
                       COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted
                FROM prospects 
                GROUP BY country
                ORDER BY total DESC
            ''')
            analytics['country_performance'] = [
                dict(zip(['country', 'total', 'avg_pain_level', 'converted'], row))
                for row in cursor.fetchall()
            ]
            
            # Email campaign performance
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opened,
                    COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked,
                    COUNT(CASE WHEN replied_at IS NOT NULL THEN 1 END) as replied
                FROM email_campaigns
            ''')
            result = cursor.fetchone()
            analytics['email_performance'] = {
                'total_sent': result[0],
                'opened': result[1],
                'clicked': result[2],
                'replied': result[3],
                'open_rate': (result[1] / result[0] * 100) if result[0] > 0 else 0,
                'click_rate': (result[2] / result[0] * 100) if result[0] > 0 else 0,
                'reply_rate': (result[3] / result[0] * 100) if result[0] > 0 else 0
            }
            
            # Daily activity (last 30 days)
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as prospects_found
                FROM prospects 
                WHERE created_at >= date('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''')
            analytics['daily_activity'] = [
                dict(zip(['date', 'prospects_found'], row))
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            # Add metadata
            analytics['export_timestamp'] = datetime.now().isoformat()
            analytics['export_version'] = '1.0'
            
            # Write to JSON
            with open(output_path, 'w') as f:
                json.dump(analytics, f, indent=2)
            
            logger.info(f"Analytics exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting analytics: {e}")
            return False

class SystemMonitor:
    """System performance monitoring"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Database metrics
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prospect metrics
            cursor.execute('SELECT COUNT(*) FROM prospects')
            total_prospects = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM prospects WHERE date(created_at) = date("now")')
            daily_prospects = cursor.fetchone()[0]
            
            # Email success rate
            cursor.execute('SELECT COUNT(*) FROM email_campaigns WHERE status = "sent"')
            sent_emails = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM email_campaigns WHERE status = "bounced"')
            bounced_emails = cursor.fetchone()[0]
            
            email_success_rate = ((sent_emails - bounced_emails) / sent_emails * 100) if sent_emails > 0 else 100
            
            # Error count (from log files)
            error_count = self.count_recent_errors()
            
            conn.close()
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                database_size=db_size,
                total_prospects=total_prospects,
                daily_prospects=daily_prospects,
                email_success_rate=email_success_rate,
                error_count=error_count
            )
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0,
                memory_percent=0,
                disk_percent=0,
                database_size=0,
                total_prospects=0,
                daily_prospects=0,
                email_success_rate=0,
                error_count=0
            )
    
    def count_recent_errors(self) -> int:
        """Count recent errors from log files"""
        try:
            error_count = 0
            log_files = ['system.log', 'automation.log', 'ted_finder.log']
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        for line in f:
                            if 'ERROR' in line and 'today' in line.lower():
                                error_count += 1
            
            return error_count
            
        except Exception as e:
            logger.error(f"Error counting recent errors: {e}")
            return 0
    
    def check_system_health(self) -> Dict:
        """Check overall system health"""
        metrics = self.get_system_metrics()
        
        health_status = {
            'overall_status': 'healthy',
            'issues': [],
            'metrics': metrics.__dict__
        }
        
        # Check CPU usage
        if metrics.cpu_percent > 80:
            health_status['issues'].append(f"High CPU usage: {metrics.cpu_percent}%")
            health_status['overall_status'] = 'warning'
        
        # Check memory usage
        if metrics.memory_percent > 85:
            health_status['issues'].append(f"High memory usage: {metrics.memory_percent}%")
            health_status['overall_status'] = 'warning'
        
        # Check disk usage
        if metrics.disk_percent > 90:
            health_status['issues'].append(f"High disk usage: {metrics.disk_percent}%")
            health_status['overall_status'] = 'critical'
        
        # Check email success rate
        if metrics.email_success_rate < 80:
            health_status['issues'].append(f"Low email success rate: {metrics.email_success_rate}%")
            health_status['overall_status'] = 'warning'
        
        # Check error count
        if metrics.error_count > 10:
            health_status['issues'].append(f"High error count: {metrics.error_count}")
            health_status['overall_status'] = 'warning'
        
        return health_status

class AlertManager:
    """Alert and notification management"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
    
    def send_email_alert(self, subject: str, message: str) -> bool:
        """Send email alert"""
        if not self.config.email_alerts or not self.config.smtp_username:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_username
            msg['To'] = self.config.alert_email
            msg['Subject'] = f"TenderPulse Alert: {subject}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.config.smtp_username, self.config.alert_email, text)
            server.quit()
            
            logger.info(f"Email alert sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False
    
    def send_slack_alert(self, webhook_url: str, message: str) -> bool:
        """Send Slack alert"""
        try:
            payload = {
                'text': f"🚨 TenderPulse Alert: {message}",
                'username': 'TenderPulse Bot',
                'icon_emoji': ':warning:'
            }
            
            response = requests.post(webhook_url, json=payload)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False

class BackupOrchestrator:
    """Main backup and logging orchestrator"""
    
    def __init__(self, db_path: str, config: BackupConfig):
        self.db_path = db_path
        self.config = config
        self.backup_manager = DatabaseBackupManager(db_path, config)
        self.data_exporter = DataExporter(db_path)
        self.system_monitor = SystemMonitor(db_path)
        self.alert_manager = AlertManager(config)
    
    def run_full_backup(self) -> Dict:
        """Run full backup process"""
        results = {
            'success': True,
            'backups_created': [],
            'errors': []
        }
        
        try:
            # Create full database backup
            db_backup = self.backup_manager.create_full_backup()
            results['backups_created'].append(db_backup)
            
            # Export CSV data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_backup = os.path.join(self.config.backup_dir, f"prospects_export_{timestamp}.csv")
            if self.data_exporter.export_prospects_csv(csv_backup):
                results['backups_created'].append(csv_backup)
            
            # Export analytics
            analytics_backup = os.path.join(self.config.backup_dir, f"analytics_{timestamp}.json")
            if self.data_exporter.export_analytics_json(analytics_backup):
                results['backups_created'].append(analytics_backup)
            
            # Clean up old backups
            self.backup_manager.cleanup_old_backups()
            
            logger.info(f"Full backup completed: {len(results['backups_created'])} files created")
            
        except Exception as e:
            logger.error(f"Error in full backup: {e}")
            results['success'] = False
            results['errors'].append(str(e))
            
            # Send alert
            self.alert_manager.send_email_alert(
                "Backup Failed",
                f"Full backup failed with error: {e}"
            )
        
        return results
    
    def run_incremental_backup(self) -> Dict:
        """Run incremental backup process"""
        results = {
            'success': True,
            'backup_created': None,
            'errors': []
        }
        
        try:
            backup_path = self.backup_manager.create_incremental_backup()
            results['backup_created'] = backup_path
            
            logger.info(f"Incremental backup completed: {backup_path}")
            
        except Exception as e:
            logger.error(f"Error in incremental backup: {e}")
            results['success'] = False
            results['errors'].append(str(e))
        
        return results
    
    def check_system_health(self) -> Dict:
        """Check system health and send alerts if needed"""
        health = self.system_monitor.check_system_health()
        
        if health['overall_status'] in ['warning', 'critical']:
            message = f"System health: {health['overall_status']}\n"
            message += f"Issues: {', '.join(health['issues'])}\n"
            message += f"Metrics: {json.dumps(health['metrics'], indent=2)}"
            
            self.alert_manager.send_email_alert("System Health Alert", message)
        
        return health

# CLI Commands
import click

@click.group()
def backup_cli():
    """TenderPulse Backup and Logging System"""
    pass

@backup_cli.command()
@click.option('--db-path', default='ted_prospects.db', help='Database path')
@click.option('--backup-dir', default='backups', help='Backup directory')
def full_backup(db_path, backup_dir):
    """Create full backup"""
    config = BackupConfig(backup_dir=backup_dir)
    orchestrator = BackupOrchestrator(db_path, config)
    
    results = orchestrator.run_full_backup()
    
    if results['success']:
        print(f"✅ Full backup completed successfully")
        print(f"📁 Created {len(results['backups_created'])} backup files")
        for backup in results['backups_created']:
            print(f"   - {backup}")
    else:
        print(f"❌ Backup failed")
        for error in results['errors']:
            print(f"   - {error}")

@backup_cli.command()
@click.option('--db-path', default='ted_prospects.db', help='Database path')
@click.option('--backup-dir', default='backups', help='Backup directory')
def incremental_backup(db_path, backup_dir):
    """Create incremental backup"""
    config = BackupConfig(backup_dir=backup_dir)
    orchestrator = BackupOrchestrator(db_path, config)
    
    results = orchestrator.run_incremental_backup()
    
    if results['success']:
        print(f"✅ Incremental backup completed: {results['backup_created']}")
    else:
        print(f"❌ Incremental backup failed")
        for error in results['errors']:
            print(f"   - {error}")

@backup_cli.command()
@click.option('--db-path', default='ted_prospects.db', help='Database path')
def system_health(db_path):
    """Check system health"""
    config = BackupConfig()
    orchestrator = BackupOrchestrator(db_path, config)
    
    health = orchestrator.check_system_health()
    
    print(f"🏥 System Health: {health['overall_status'].upper()}")
    print(f"📊 Metrics:")
    for key, value in health['metrics'].items():
        print(f"   {key}: {value}")
    
    if health['issues']:
        print(f"⚠️  Issues:")
        for issue in health['issues']:
            print(f"   - {issue}")

if __name__ == "__main__":
    backup_cli()
