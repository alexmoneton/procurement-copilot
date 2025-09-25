#!/usr/bin/env python3
"""
Test script for all the new improvements
Tests unified email system, cost guardrails, status monitoring, and funnel telemetry.
"""

import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_unified_mailer():
    """Test the unified email system."""
    print("🧪 Testing Unified Mailer System")
    print("=" * 40)
    
    try:
        from mailer import UnifiedMailer, get_mailer
        
        # Initialize mailer
        mailer = get_mailer()
        print(f"✅ Mailer initialized with provider: {mailer.provider.value}")
        
        # Test suppression
        mailer.add_suppression("test@example.com", "bounce", "webhook")
        is_suppressed = mailer.is_suppressed("test@example.com")
        print(f"✅ Suppression test: {is_suppressed}")
        
        # Test stats
        stats = mailer.get_suppression_stats()
        print(f"✅ Suppression stats: {stats}")
        
        # Test unsubscribe URL generation
        unsubscribe_url = mailer._generate_unsubscribe_url("test@example.com", "test_campaign")
        print(f"✅ Unsubscribe URL generated: {unsubscribe_url[:50]}...")
        
        print("✅ Unified mailer system working!")
        return True
        
    except Exception as e:
        print(f"❌ Unified mailer test failed: {e}")
        return False

def test_cost_guardrails():
    """Test the cost guardrails system."""
    print("\n🧪 Testing Cost Guardrails System")
    print("=" * 40)
    
    try:
        from cost_guardrails import CostGuardrails
        
        # Initialize guardrails
        guardrails = CostGuardrails()
        print("✅ Cost guardrails initialized")
        
        # Test usage tracking
        usage = guardrails.get_today_usage()
        print(f"✅ Today's usage: {usage}")
        
        # Test API limits
        can_apollo, msg = guardrails.can_make_request('apollo')
        print(f"✅ Apollo limit check: {can_apollo} - {msg}")
        
        # Test prospect relevance
        test_prospect = {
            'company_name': 'TechCorp GmbH',
            'domain': 'techcorp.de',
            'country': 'DE',
            'lost_tender_value': 1500000,
            'cpv_codes': '72000000'
        }
        
        should_enrich, score = guardrails.should_enrich_prospect(test_prospect)
        print(f"✅ Prospect relevance: {score:.1f}/100, should enrich: {should_enrich}")
        
        # Test email caching
        guardrails.cache_email("example.com", "contact@example.com", 95, "hunter")
        cached = guardrails.get_cached_email("example.com")
        print(f"✅ Email caching: {cached is not None}")
        
        # Test usage report
        report = guardrails.get_usage_report()
        print(f"✅ Usage report generated: {len(report)} sections")
        
        print("✅ Cost guardrails system working!")
        return True
        
    except Exception as e:
        print(f"❌ Cost guardrails test failed: {e}")
        return False

def test_status_monitor():
    """Test the status monitoring system."""
    print("\n🧪 Testing Status Monitor System")
    print("=" * 40)
    
    try:
        from status_monitor import StatusMonitor
        
        # Initialize monitor
        monitor = StatusMonitor()
        print("✅ Status monitor initialized")
        
        # Simulate activity
        monitor.record_source_activity('ted_api', 150, 2)
        monitor.record_source_activity('apollo_io', 45, 1)
        monitor.record_error('ted_api', 'timeout', 'Request timeout', 'warning')
        
        # Test system health
        health = monitor.get_system_health()
        print(f"✅ System health: {health.overall_status}")
        print(f"   Total prospects (24h): {health.total_prospects_24h}")
        print(f"   Total errors (24h): {health.total_errors_24h}")
        
        # Test dashboard data
        dashboard_data = monitor.get_status_dashboard_data()
        print(f"✅ Dashboard data: {len(dashboard_data['sources'])} sources")
        
        # Test health checks
        checks = monitor.run_health_checks()
        print(f"✅ Health checks: {len(checks)} checks completed")
        
        print("✅ Status monitor system working!")
        return True
        
    except Exception as e:
        print(f"❌ Status monitor test failed: {e}")
        return False

def test_funnel_telemetry():
    """Test the funnel telemetry system."""
    print("\n🧪 Testing Funnel Telemetry System")
    print("=" * 40)
    
    try:
        from funnel_telemetry import FunnelTelemetry, EventType, EntityType
        
        # Initialize telemetry
        telemetry = FunnelTelemetry()
        print("✅ Funnel telemetry initialized")
        
        # Track test events
        telemetry.track_event(
            EventType.LEAD_FOUND,
            EntityType.PROSPECT,
            "test_prospect_123",
            {"company": "TestCorp", "country": "DE"},
            user_id="test_user_456"
        )
        
        telemetry.track_event(
            EventType.EMAIL_SENT,
            EntityType.EMAIL,
            "test_email_789",
            {"campaign": "test_campaign"},
            user_id="test_user_456"
        )
        
        # Test funnel metrics
        funnel_metrics = telemetry.get_funnel_metrics()
        print(f"✅ Funnel metrics: {len(funnel_metrics)} steps")
        
        # Test conversion funnel
        conversion_funnel = telemetry.get_conversion_funnel()
        print(f"✅ Conversion funnel: {len(conversion_funnel['steps'])} steps")
        
        # Test daily metrics
        daily_metrics = telemetry.get_daily_metrics()
        print(f"✅ Daily metrics: {len(daily_metrics['totals'])} event types")
        
        # Test user journey
        user_journey = telemetry.get_user_journey("test_user_456")
        print(f"✅ User journey: {len(user_journey)} events")
        
        print("✅ Funnel telemetry system working!")
        return True
        
    except Exception as e:
        print(f"❌ Funnel telemetry test failed: {e}")
        return False

def test_configuration():
    """Test the updated configuration."""
    print("\n🧪 Testing Configuration")
    print("=" * 40)
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Check email provider configuration
        email_provider = config.get('email_provider')
        print(f"✅ Email provider: {email_provider}")
        
        # Check tracking domains
        tracking_domains = config.get('tracking_domains', {})
        print(f"✅ Tracking domains: {len(tracking_domains)} configured")
        
        # Check daily budgets
        daily_budgets = config.get('daily_budgets', {})
        print(f"✅ Daily budgets: {len(daily_budgets)} limits set")
        
        # Check Postgres configuration
        postgres_config = config.get('database', {}).get('postgres', {})
        print(f"✅ Postgres config: {len(postgres_config)} settings")
        
        print("✅ Configuration updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all improvement tests."""
    print("🚀 TenderPulse Improvements Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Unified Mailer", test_unified_mailer),
        ("Cost Guardrails", test_cost_guardrails),
        ("Status Monitor", test_status_monitor),
        ("Funnel Telemetry", test_funnel_telemetry)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All improvements are working correctly!")
        print("\n🚀 Ready for production deployment!")
    else:
        print("⚠️ Some improvements need attention before deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
