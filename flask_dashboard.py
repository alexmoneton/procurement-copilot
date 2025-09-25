#!/usr/bin/env python3
"""
TenderPulse Flask Dashboard - Complete Customer Acquisition Management
Web interface for managing prospects, emails, and campaigns

Features:
- Dashboard showing prospects found
- Email preview and editing
- Send/schedule email functionality
- Response tracking
- Simple analytics (open rates, replies)
- User authentication
- Real-time updates
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import asdict

# Flask and related imports
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import secrets

# Import our prospect finder components
from advanced_ted_prospect_finder import (
    ConfigManager, ProspectDatabase, EmailTemplateGenerator, 
    EmailSender, TEDProspectFinder, ProspectExtractor
)

# Import matching system
from tender_intelligence import TenderMatcher, ClientProfileManager

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Simple user model for demo
class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

# In-memory user storage (use database in production)
# Create users with simple password hash
def simple_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

users = {
    1: User(1, 'admin', 'admin@tenderpulse.eu', simple_hash('admin123'))
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

# Initialize components
config_manager = ConfigManager()
db = ProspectDatabase(config_manager.get('database.path'))
tender_matcher = TenderMatcher()
profile_manager = ClientProfileManager()

@app.route('/')
@login_required
def dashboard():
    """Main dashboard showing key metrics"""
    
    # Get database statistics
    stats = db.get_stats()
    
    # Get recent prospects
    recent_prospects = db.get_prospects_by_status('found')[:10]
    
    # Get prospects by status
    prospects_by_status = stats.get('prospects_by_status', {})
    
    # Calculate conversion funnel
    total_prospects = sum(prospects_by_status.values())
    email_found = prospects_by_status.get('email_found', 0)
    contacted = prospects_by_status.get('contacted', 0)
    responded = prospects_by_status.get('responded', 0)
    converted = prospects_by_status.get('converted', 0)
    
    # Calculate rates
    email_rate = (email_found / total_prospects * 100) if total_prospects > 0 else 0
    contact_rate = (contacted / email_found * 100) if email_found > 0 else 0
    response_rate = (responded / contacted * 100) if contacted > 0 else 0
    conversion_rate = (converted / responded * 100) if responded > 0 else 0
    
    # Get recent activity
    recent_activity = get_recent_activity()
    
    # Get configuration for integration status
    config = {
        'apollo_io': config_manager.get('api_keys.apollo_io', ''),
        'hunter_io': config_manager.get('api_keys.hunter_io', ''),
        'sendgrid': config_manager.get('api_keys.sendgrid', '')
    }
    
    return render_template('dashboard.html',
                         stats=stats,
                         recent_prospects=recent_prospects,
                         prospects_by_status=prospects_by_status,
                         total_prospects=total_prospects,
                         email_rate=email_rate,
                         contact_rate=contact_rate,
                         response_rate=response_rate,
                         conversion_rate=conversion_rate,
                         recent_activity=recent_activity,
                         config=config)

@app.route('/prospects')
@login_required
def prospects():
    """Prospects management page"""
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    country = request.args.get('country', 'all')
    sector = request.args.get('sector', 'all')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    # Build query
    query = "SELECT * FROM prospects WHERE 1=1"
    params = []
    
    if status != 'all':
        query += " AND status = ?"
        params.append(status)
    
    if country != 'all':
        query += " AND country = ?"
        params.append(country)
    
    if sector != 'all':
        query += " AND sector = ?"
        params.append(sector)
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    # Execute query
    conn = sqlite3.connect(config_manager.get('database.path'))
    cursor = conn.cursor()
    cursor.execute(query, params)
    columns = [description[0] for description in cursor.description]
    prospects = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Get total count for pagination
    count_query = "SELECT COUNT(*) FROM prospects WHERE 1=1"
    count_params = []
    
    if status != 'all':
        count_query += " AND status = ?"
        count_params.append(status)
    
    if country != 'all':
        count_query += " AND country = ?"
        count_params.append(country)
    
    if sector != 'all':
        count_query += " AND sector = ?"
        count_params.append(sector)
    
    cursor.execute(count_query, count_params)
    total_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Get filter options
    filter_options = get_filter_options()
    
    return render_template('prospects.html',
                         prospects=prospects,
                         status=status,
                         country=country,
                         sector=sector,
                         page=page,
                         per_page=per_page,
                         total_count=total_count,
                         filter_options=filter_options)

@app.route('/prospect/<int:prospect_id>')
@login_required
def prospect_detail(prospect_id):
    """Individual prospect detail page"""
    
    # Get prospect details
    conn = sqlite3.connect(config_manager.get('database.path'))
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM prospects WHERE id = ?', (prospect_id,))
    columns = [description[0] for description in cursor.description]
    prospect = dict(zip(columns, cursor.fetchone())) if cursor.fetchone() else None
    
    if not prospect:
        flash('Prospect not found', 'error')
        return redirect(url_for('prospects'))
    
    # Get email campaigns for this prospect
    cursor.execute('''
        SELECT * FROM email_campaigns 
        WHERE prospect_id = ? 
        ORDER BY created_at DESC
    ''', (prospect_id,))
    columns = [description[0] for description in cursor.description]
    campaigns = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('prospect_detail.html', prospect=prospect, campaigns=campaigns)

@app.route('/email/<int:prospect_id>')
@login_required
def email_compose(prospect_id):
    """Email composition page"""
    
    # Get prospect details
    conn = sqlite3.connect(config_manager.get('database.path'))
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM prospects WHERE id = ?', (prospect_id,))
    columns = [description[0] for description in cursor.description]
    prospect = dict(zip(columns, cursor.fetchone())) if cursor.fetchone() else None
    
    if not prospect:
        flash('Prospect not found', 'error')
        return redirect(url_for('prospects'))
    
    conn.close()
    
    # Generate email template
    template_generator = EmailTemplateGenerator(config_manager)
    
    # Create a mock prospect object for template generation
    from advanced_ted_prospect_finder import ProspectCompany
    prospect_obj = ProspectCompany(
        company_name=prospect['company_name'],
        country=prospect['country'],
        sector=prospect['sector'],
        lost_tender_id=prospect['lost_tender_id'],
        lost_tender_title=prospect['lost_tender_title'],
        lost_tender_value=prospect['lost_tender_value'],
        lost_date=prospect['lost_date'],
        buyer_name=prospect['buyer_name'],
        winner_name=prospect['winner_name'],
        pain_level=prospect['pain_level'],
        email=prospect.get('email'),
        contact_name=prospect.get('contact_name')
    )
    
    email_content = template_generator.generate_personalized_email(prospect_obj)
    
    return render_template('email_compose.html', 
                         prospect=prospect, 
                         email_content=email_content)

@app.route('/send_email', methods=['POST'])
@login_required
def send_email():
    """Send email to prospect"""
    
    prospect_id = request.form.get('prospect_id')
    subject = request.form.get('subject')
    body = request.form.get('body')
    html_body = request.form.get('html_body')
    
    # Get prospect details
    conn = sqlite3.connect(config_manager.get('database.path'))
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM prospects WHERE id = ?', (prospect_id,))
    columns = [description[0] for description in cursor.description]
    prospect = dict(zip(columns, cursor.fetchone())) if cursor.fetchone() else None
    
    if not prospect or not prospect.get('email'):
        flash('Prospect or email not found', 'error')
        return redirect(url_for('prospects'))
    
    # Send email
    email_sender = EmailSender(config_manager)
    
    import asyncio
    result = asyncio.run(email_sender.send_email(
        to_email=prospect['email'],
        subject=subject,
        body=body,
        html_body=html_body,
        tags=[prospect['sector'].lower().replace(' ', '_'), prospect['country'].lower()]
    ))
    
    if result.get('status') == 'sent':
        # Update prospect status
        cursor.execute('''
            UPDATE prospects 
            SET status = 'contacted', updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), prospect_id))
        
        # Save email campaign
        cursor.execute('''
            INSERT INTO email_campaigns 
            (prospect_id, campaign_name, subject, body, status, mailgun_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (prospect_id, 'manual_send', subject, body, 'sent', result.get('id'), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        flash(f'Email sent successfully to {prospect["email"]}', 'success')
    else:
        conn.close()
        flash(f'Failed to send email: {result.get("error", "Unknown error")}', 'error')
    
    return redirect(url_for('prospect_detail', prospect_id=prospect_id))

@app.route('/campaigns')
@login_required
def campaigns():
    """Email campaigns overview"""
    
    # Get campaign statistics
    conn = sqlite3.connect(config_manager.get('database.path'))
    cursor = conn.cursor()
    
    # Get campaigns with prospect info
    cursor.execute('''
        SELECT c.*, p.company_name, p.country, p.sector, p.email
        FROM email_campaigns c
        JOIN prospects p ON c.prospect_id = p.id
        ORDER BY c.created_at DESC
        LIMIT 100
    ''')
    columns = [description[0] for description in cursor.description]
    campaigns = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Get campaign statistics
    cursor.execute('''
        SELECT 
            status,
            COUNT(*) as count,
            COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opened,
            COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked,
            COUNT(CASE WHEN replied_at IS NOT NULL THEN 1 END) as replied
        FROM email_campaigns 
        GROUP BY status
    ''')
    
    campaign_stats = {}
    for row in cursor.fetchall():
        status, count, opened, clicked, replied = row
        campaign_stats[status] = {
            'count': count,
            'opened': opened,
            'clicked': clicked,
            'replied': replied,
            'open_rate': (opened / count * 100) if count > 0 else 0,
            'click_rate': (clicked / count * 100) if count > 0 else 0,
            'reply_rate': (replied / count * 100) if count > 0 else 0
        }
    
    conn.close()
    
    return render_template('campaigns.html', campaigns=campaigns, campaign_stats=campaign_stats)

@app.route('/analytics')
@login_required
def analytics():
    """Analytics and reporting page"""
    
    # Get comprehensive analytics
    conn = sqlite3.connect(config_manager.get('database.path'))
    cursor = conn.cursor()
    
    # Prospect funnel analytics
    cursor.execute('''
        SELECT 
            status,
            COUNT(*) as count,
            AVG(pain_level) as avg_pain_level
        FROM prospects 
        GROUP BY status
    ''')
    funnel_data = dict(cursor.fetchall())
    
    # Sector performance
    cursor.execute('''
        SELECT 
            sector,
            COUNT(*) as total_prospects,
            COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted,
            AVG(pain_level) as avg_pain_level
        FROM prospects 
        GROUP BY sector
        ORDER BY total_prospects DESC
    ''')
    sector_performance = [dict(zip(['sector', 'total_prospects', 'converted', 'avg_pain_level'], row)) 
                         for row in cursor.fetchall()]
    
    # Country performance
    cursor.execute('''
        SELECT 
            country,
            COUNT(*) as total_prospects,
            COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted,
            AVG(pain_level) as avg_pain_level
        FROM prospects 
        GROUP BY country
        ORDER BY total_prospects DESC
    ''')
    country_performance = [dict(zip(['country', 'total_prospects', 'converted', 'avg_pain_level'], row)) 
                          for row in cursor.fetchall()]
    
    # Daily activity
    cursor.execute('''
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as prospects_found
        FROM prospects 
        WHERE created_at >= date('now', '-30 days')
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    ''')
    daily_activity = [dict(zip(['date', 'prospects_found'], row)) for row in cursor.fetchall()]
    
    # Email performance
    cursor.execute('''
        SELECT 
            DATE(c.created_at) as date,
            COUNT(*) as emails_sent,
            COUNT(CASE WHEN c.opened_at IS NOT NULL THEN 1 END) as emails_opened,
            COUNT(CASE WHEN c.replied_at IS NOT NULL THEN 1 END) as emails_replied
        FROM email_campaigns c
        WHERE c.created_at >= date('now', '-30 days')
        GROUP BY DATE(c.created_at)
        ORDER BY date DESC
    ''')
    email_performance = [dict(zip(['date', 'emails_sent', 'emails_opened', 'emails_replied'], row)) 
                        for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('analytics.html',
                         funnel_data=funnel_data,
                         sector_performance=sector_performance,
                         country_performance=country_performance,
                         daily_activity=daily_activity,
                         email_performance=email_performance)

@app.route('/find_prospects', methods=['POST'])
@login_required
def find_prospects():
    """Trigger prospect finding from web interface"""
    
    # This would trigger the prospect finding process
    # For now, we'll just show a success message
    flash('Prospect finding process started. Check back in a few minutes.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/api/prospects')
@login_required
def api_prospects():
    """API endpoint for prospects data"""
    
    status = request.args.get('status', 'all')
    limit = int(request.args.get('limit', 50))
    
    query = "SELECT * FROM prospects WHERE 1=1"
    params = []
    
    if status != 'all':
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    conn = sqlite3.connect(config_manager.get('database.path'))
    cursor = conn.cursor()
    cursor.execute(query, params)
    columns = [description[0] for description in cursor.description]
    prospects = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(prospects)

@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics"""
    
    stats = db.get_stats()
    return jsonify(stats)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find user
        user = None
        for u in users.values():
            if u.username == username:
                user = u
                break
        
        if user and user.password_hash == simple_hash(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Helper functions
def get_recent_activity():
    """Get recent activity for dashboard"""
    conn = sqlite3.connect(config_manager.get('database.path'))
    cursor = conn.cursor()
    
    # Get recent prospects
    cursor.execute('''
        SELECT 'prospect' as type, company_name as title, created_at, status
        FROM prospects 
        WHERE created_at >= date('now', '-7 days')
        ORDER BY created_at DESC
        LIMIT 10
    ''')
    
    activities = []
    for row in cursor.fetchall():
        activities.append({
            'type': row[0],
            'title': row[1],
            'date': row[2],
            'status': row[3]
        })
    
    conn.close()
    return activities

def get_filter_options():
    """Get filter options for prospects page"""
    conn = sqlite3.connect(config_manager.get('database.path'))
    cursor = conn.cursor()
    
    # Get unique countries
    cursor.execute('SELECT DISTINCT country FROM prospects WHERE country IS NOT NULL ORDER BY country')
    countries = [row[0] for row in cursor.fetchall()]
    
    # Get unique sectors
    cursor.execute('SELECT DISTINCT sector FROM prospects WHERE sector IS NOT NULL ORDER BY sector')
    sectors = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'countries': countries,
        'sectors': sectors
    }

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.route('/settings')
@login_required
def settings():
    """Settings page"""
    
    # Get current configuration
    config = {
        'apollo_io': config_manager.get('api_keys.apollo_io', ''),
        'hunter_io': config_manager.get('api_keys.hunter_io', ''),
        'sendgrid': config_manager.get('api_keys.sendgrid', '')
    }
    
    email_config = {
        'from_email': config_manager.get('email.from_email', ''),
        'from_name': config_manager.get('email.from_name', ''),
        'reply_to': config_manager.get('email.reply_to', '')
    }
    
    return render_template('settings.html',
                         config=config,
                         email_config=email_config)

# Matching system routes
@app.route('/matching')
@login_required
def matching():
    """Tender matching dashboard for clients"""
    user_id = current_user.id
    
    # Get client profile
    profile = profile_manager.get_profile(user_id)
    
    # Get matching tenders
    matching_tenders = tender_matcher.get_matching_tenders(user_id, limit=10)
    
    return render_template('matching.html', 
                         profile=profile, 
                         matching_tenders=matching_tenders)

@app.route('/profile')
@login_required
def profile():
    """Client profile management"""
    user_id = current_user.id
    profile = profile_manager.get_profile(user_id)
    
    return render_template('profile.html', profile=profile)

@app.route('/profile', methods=['POST'])
@login_required
def update_profile():
    """Update client profile"""
    user_id = current_user.id
    
    profile_data = {
        'company_name': request.form.get('company_name'),
        'target_value_range': [
            int(request.form.get('min_value', 50000)),
            int(request.form.get('max_value', 2000000))
        ],
        'preferred_countries': request.form.getlist('countries'),
        'cpv_expertise': request.form.getlist('cpv_codes'),
        'company_size': request.form.get('company_size'),
        'experience_level': request.form.get('experience_level')
    }
    
    # Update or create profile
    existing_profile = profile_manager.get_profile(user_id)
    if existing_profile:
        success = profile_manager.update_profile(user_id, profile_data)
    else:
        profile_id = profile_manager.create_profile(user_id, profile_data)
        success = profile_id is not None
    
    if success:
        flash('Profile updated successfully!', 'success')
    else:
        flash('Error updating profile. Please try again.', 'error')
    
    return redirect(url_for('profile'))

@app.route('/tender/<tender_id>')
@login_required
def tender_details(tender_id):
    """View detailed tender information with winning strategy"""
    user_id = current_user.id
    profile = profile_manager.get_profile(user_id)
    
    if not profile:
        flash('Please set up your profile first to view tender details.', 'warning')
        return redirect(url_for('profile'))
    
    # Get matching tenders and find the specific one
    matching_tenders = tender_matcher.get_matching_tenders(user_id, limit=50)
    tender = next((t for t in matching_tenders if t['id'] == tender_id), None)
    
    if not tender:
        flash('Tender not found or not matching your profile.', 'error')
        return redirect(url_for('matching'))
    
    return render_template('tender_details.html', tender=tender, profile=profile)

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
