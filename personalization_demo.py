#!/usr/bin/env python3
"""
Personalization Demo - Shows how the same template looks for different prospects
"""

from advanced_ted_prospect_finder import EmailTemplateGenerator, ConfigManager, ProspectCompany

def create_demo_prospects():
    """Create 3 different prospects to show personalization"""
    return [
        ProspectCompany(
            company_name='TechCorp GmbH',
            country='Germany', 
            sector='IT & Software',
            lost_tender_id='TED-111111',
            lost_tender_title='Germany-Munich: Software development services',
            lost_tender_value='€1,200,000',
            buyer_name='Munich Municipality',
            winner_name='CompetitorA Ltd',
            lost_date='2024-09-20T00:00:00+02:00',
            pain_level=85,
            contact_name='Sarah Weber',
            email='s.weber@techcorp.de',
            status='email_found'
        ),
        ProspectCompany(
            company_name='DataSolutions Ltd',
            country='France', 
            sector='Data Analytics',
            lost_tender_id='TED-222222',
            lost_tender_title='France-Paris: Data analysis and visualization services',
            lost_tender_value='€650,000',
            buyer_name='Paris City Council',
            winner_name='CompetitorB Ltd',
            lost_date='2024-09-18T00:00:00+02:00',
            pain_level=70,
            contact_name='Pierre Dubois',
            email='p.dubois@datasolutions.fr',
            status='email_found'
        ),
        ProspectCompany(
            company_name='GreenTech Solutions',
            country='Netherlands', 
            sector='Environmental Services',
            lost_tender_id='TED-333333',
            lost_tender_title='Netherlands-Amsterdam: Environmental consulting services',
            lost_tender_value='€450,000',
            buyer_name='Amsterdam Municipality',
            winner_name='CompetitorC Ltd',
            lost_date='2024-09-22T00:00:00+02:00',
            pain_level=60,
            contact_name='Emma van der Berg',
            email='e.vanderberg@greentech.nl',
            status='email_found'
        )
    ]

def show_personalization_demo():
    """Show how the same template personalizes for different prospects"""
    
    print("🎯 PERSONALIZATION DEMO - SAME TEMPLATE, DIFFERENT PROSPECTS")
    print("=" * 80)
    print()
    
    config = ConfigManager()
    generator = EmailTemplateGenerator(config)
    prospects = create_demo_prospects()
    
    for i, prospect in enumerate(prospects, 1):
        print(f"📧 PROSPECT {i}: {prospect.company_name} ({prospect.country})")
        print("-" * 60)
        print(f"Lost Tender: {prospect.lost_tender_title}")
        print(f"Value: {prospect.lost_tender_value}")
        print(f"Buyer: {prospect.buyer_name}")
        print(f"Contact: {prospect.contact_name}")
        print()
        
        # Generate email
        email = generator.generate_personalized_email(prospect)
        
        print(f"Subject: {email['subject']}")
        print()
        print("Email Body:")
        print(email['body'])
        print()
        print("=" * 80)
        print()
    
    print("🔍 PERSONALIZATION ANALYSIS:")
    print("=" * 80)
    print()
    print("✅ WHAT CHANGES PER PROSPECT:")
    print("   • Contact name: Sarah vs Pierre vs Emma")
    print("   • Company name: TechCorp vs DataSolutions vs GreenTech")
    print("   • Contract value: €1.2M vs €650K vs €450K")
    print("   • City: Munich vs Paris vs Amsterdam")
    print("   • Sector: IT & Software vs Data Analytics vs Environmental")
    print("   • Similar opportunities: Frankfurt vs Lyon vs Rotterdam")
    print("   • TED links: Different tender IDs")
    print("   • Dates: Different award dates")
    print()
    print("✅ WHAT STAYS THE SAME:")
    print("   • Email structure and flow")
    print("   • Signature (Alex, TenderPulse)")
    print("   • Trial link")
    print("   • General messaging approach")
    print()
    print("🚨 RESULT: Each prospect gets a UNIQUE, personalized email!")
    print("   No two prospects will receive identical content.")
    print("   All personalization is based on their specific lost tender data.")

if __name__ == "__main__":
    show_personalization_demo()
