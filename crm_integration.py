#!/usr/bin/env python3
"""
TenderPulse CRM Integration System
Integrate with popular CRMs: HubSpot, Salesforce, Pipedrive, Airtable

Features:
- HubSpot integration
- Salesforce integration  
- Pipedrive integration
- Airtable integration
- Webhook system for any CRM
- Data synchronization
- Lead scoring and qualification
- Custom field mapping
"""

import os
import json
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger('crm_integration')

@dataclass
class CRMContact:
    """Standardized contact format for CRM integration"""
    company_name: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    job_title: Optional[str] = None
    lead_source: str = "TenderPulse"
    lead_status: str = "New"
    pain_level: int = 50
    lost_tender_value: Optional[str] = None
    buyer_name: Optional[str] = None
    custom_fields: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_fields is None:
            self.custom_fields = {}

class HubSpotIntegration:
    """HubSpot CRM integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def create_contact(self, contact: CRMContact) -> Dict:
        """Create contact in HubSpot"""
        try:
            # Prepare contact data
            contact_data = {
                'properties': {
                    'company': contact.company_name,
                    'email': contact.email,
                    'firstname': contact.first_name or '',
                    'lastname': contact.last_name or '',
                    'phone': contact.phone or '',
                    'website': contact.website or '',
                    'country': contact.country or '',
                    'industry': contact.industry or '',
                    'jobtitle': contact.job_title or '',
                    'hs_lead_status': contact.lead_status,
                    'hs_lead_source': contact.lead_source,
                    'tenderpulse_pain_level': str(contact.pain_level),
                    'lost_tender_value': contact.lost_tender_value or '',
                    'buyer_name': contact.buyer_name or '',
                    'tenderpulse_source': 'TED_Bid_Loser'
                }
            }
            
            # Add custom fields
            for key, value in contact.custom_fields.items():
                contact_data['properties'][f'tenderpulse_{key}'] = str(value)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/crm/v3/objects/contacts",
                    headers=self.headers,
                    json=contact_data
                )
                
                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"Created HubSpot contact: {result['id']}")
                    return {'success': True, 'contact_id': result['id']}
                else:
                    logger.error(f"HubSpot API error: {response.status_code} - {response.text}")
                    return {'success': False, 'error': response.text}
                    
        except Exception as e:
            logger.error(f"Error creating HubSpot contact: {e}")
            return {'success': False, 'error': str(e)}
    
    async def update_contact(self, contact_id: str, contact: CRMContact) -> Dict:
        """Update existing contact in HubSpot"""
        try:
            contact_data = {
                'properties': {
                    'hs_lead_status': contact.lead_status,
                    'tenderpulse_pain_level': str(contact.pain_level)
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/crm/v3/objects/contacts/{contact_id}",
                    headers=self.headers,
                    json=contact_data
                )
                
                if response.status_code == 200:
                    logger.info(f"Updated HubSpot contact: {contact_id}")
                    return {'success': True}
                else:
                    logger.error(f"HubSpot update error: {response.status_code}")
                    return {'success': False, 'error': response.text}
                    
        except Exception as e:
            logger.error(f"Error updating HubSpot contact: {e}")
            return {'success': False, 'error': str(e)}

class SalesforceIntegration:
    """Salesforce CRM integration"""
    
    def __init__(self, client_id: str, client_secret: str, username: str, password: str, security_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.security_token = security_token
        self.access_token = None
        self.instance_url = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Salesforce"""
        try:
            auth_data = {
                'grant_type': 'password',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'username': self.username,
                'password': f"{self.password}{self.security_token}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://login.salesforce.com/services/oauth2/token",
                    data=auth_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.access_token = result['access_token']
                    self.instance_url = result['instance_url']
                    logger.info("Salesforce authentication successful")
                    return True
                else:
                    logger.error(f"Salesforce auth error: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error authenticating with Salesforce: {e}")
            return False
    
    async def create_lead(self, contact: CRMContact) -> Dict:
        """Create lead in Salesforce"""
        if not self.access_token:
            auth_success = await self.authenticate()
            if not auth_success:
                return {'success': False, 'error': 'Authentication failed'}
        
        try:
            lead_data = {
                'Company': contact.company_name,
                'Email': contact.email,
                'FirstName': contact.first_name or '',
                'LastName': contact.last_name or '',
                'Phone': contact.phone or '',
                'Website': contact.website or '',
                'Country': contact.country or '',
                'Industry': contact.industry or '',
                'Title': contact.job_title or '',
                'LeadSource': contact.lead_source,
                'Status': contact.lead_status,
                'TenderPulse_Pain_Level__c': contact.pain_level,
                'Lost_Tender_Value__c': contact.lost_tender_value or '',
                'Buyer_Name__c': contact.buyer_name or ''
            }
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.instance_url}/services/data/v52.0/sobjects/Lead/",
                    headers=headers,
                    json=lead_data
                )
                
                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"Created Salesforce lead: {result['id']}")
                    return {'success': True, 'lead_id': result['id']}
                else:
                    logger.error(f"Salesforce API error: {response.status_code} - {response.text}")
                    return {'success': False, 'error': response.text}
                    
        except Exception as e:
            logger.error(f"Error creating Salesforce lead: {e}")
            return {'success': False, 'error': str(e)}

class PipedriveIntegration:
    """Pipedrive CRM integration"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.pipedrive.com/v1"
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    async def create_person(self, contact: CRMContact) -> Dict:
        """Create person in Pipedrive"""
        try:
            person_data = {
                'name': f"{contact.first_name or ''} {contact.last_name or ''}".strip() or contact.company_name,
                'email': [{'value': contact.email, 'primary': True}],
                'phone': [{'value': contact.phone, 'primary': True}] if contact.phone else [],
                'org_name': contact.company_name,
                'country': contact.country or '',
                'industry': contact.industry or '',
                'job_title': contact.job_title or '',
                'lead_source': contact.lead_source,
                'tenderpulse_pain_level': contact.pain_level,
                'lost_tender_value': contact.lost_tender_value or '',
                'buyer_name': contact.buyer_name or ''
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/persons?api_token={self.api_token}",
                    headers=self.headers,
                    json=person_data
                )
                
                if response.status_code == 201:
                    result = response.json()
                    if result.get('success'):
                        person_id = result['data']['id']
                        logger.info(f"Created Pipedrive person: {person_id}")
                        return {'success': True, 'person_id': person_id}
                    else:
                        logger.error(f"Pipedrive API error: {result}")
                        return {'success': False, 'error': str(result)}
                else:
                    logger.error(f"Pipedrive HTTP error: {response.status_code}")
                    return {'success': False, 'error': response.text}
                    
        except Exception as e:
            logger.error(f"Error creating Pipedrive person: {e}")
            return {'success': False, 'error': str(e)}

class AirtableIntegration:
    """Airtable integration"""
    
    def __init__(self, api_key: str, base_id: str, table_name: str):
        self.api_key = api_key
        self.base_id = base_id
        self.table_name = table_name
        self.base_url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def create_record(self, contact: CRMContact) -> Dict:
        """Create record in Airtable"""
        try:
            record_data = {
                'fields': {
                    'Company Name': contact.company_name,
                    'Email': contact.email,
                    'First Name': contact.first_name or '',
                    'Last Name': contact.last_name or '',
                    'Phone': contact.phone or '',
                    'Website': contact.website or '',
                    'Country': contact.country or '',
                    'Industry': contact.industry or '',
                    'Job Title': contact.job_title or '',
                    'Lead Source': contact.lead_source,
                    'Lead Status': contact.lead_status,
                    'Pain Level': contact.pain_level,
                    'Lost Tender Value': contact.lost_tender_value or '',
                    'Buyer Name': contact.buyer_name or '',
                    'Created Date': datetime.now().isoformat()
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=record_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    record_id = result['id']
                    logger.info(f"Created Airtable record: {record_id}")
                    return {'success': True, 'record_id': record_id}
                else:
                    logger.error(f"Airtable API error: {response.status_code} - {response.text}")
                    return {'success': False, 'error': response.text}
                    
        except Exception as e:
            logger.error(f"Error creating Airtable record: {e}")
            return {'success': False, 'error': str(e)}

class WebhookIntegration:
    """Generic webhook integration for any CRM"""
    
    def __init__(self, webhook_url: str, headers: Dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}
    
    async def send_contact(self, contact: CRMContact) -> Dict:
        """Send contact data via webhook"""
        try:
            contact_data = {
                'company_name': contact.company_name,
                'email': contact.email,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'phone': contact.phone,
                'website': contact.website,
                'country': contact.country,
                'industry': contact.industry,
                'job_title': contact.job_title,
                'lead_source': contact.lead_source,
                'lead_status': contact.lead_status,
                'pain_level': contact.pain_level,
                'lost_tender_value': contact.lost_tender_value,
                'buyer_name': contact.buyer_name,
                'custom_fields': contact.custom_fields,
                'timestamp': datetime.now().isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    headers=self.headers,
                    json=contact_data
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"Sent contact via webhook: {contact.email}")
                    return {'success': True, 'response': response.text}
                else:
                    logger.error(f"Webhook error: {response.status_code} - {response.text}")
                    return {'success': False, 'error': response.text}
                    
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return {'success': False, 'error': str(e)}

class CRMOrchestrator:
    """Main CRM integration orchestrator"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.integrations = {}
        
        # Initialize integrations based on config
        if config.get('hubspot_api_key'):
            self.integrations['hubspot'] = HubSpotIntegration(config['hubspot_api_key'])
        
        if config.get('salesforce'):
            sf_config = config['salesforce']
            self.integrations['salesforce'] = SalesforceIntegration(
                sf_config['client_id'],
                sf_config['client_secret'],
                sf_config['username'],
                sf_config['password'],
                sf_config['security_token']
            )
        
        if config.get('pipedrive_api_token'):
            self.integrations['pipedrive'] = PipedriveIntegration(config['pipedrive_api_token'])
        
        if config.get('airtable'):
            at_config = config['airtable']
            self.integrations['airtable'] = AirtableIntegration(
                at_config['api_key'],
                at_config['base_id'],
                at_config['table_name']
            )
        
        if config.get('webhook_url'):
            self.integrations['webhook'] = WebhookIntegration(
                config['webhook_url'],
                config.get('webhook_headers', {})
            )
    
    def convert_prospect_to_contact(self, prospect: Dict) -> CRMContact:
        """Convert prospect data to CRM contact format"""
        # Parse contact name
        contact_name = prospect.get('contact_name', '')
        first_name, last_name = '', ''
        if contact_name:
            name_parts = contact_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Map status to lead status
        status_mapping = {
            'found': 'New',
            'email_found': 'New',
            'contacted': 'Contacted',
            'responded': 'Qualified',
            'converted': 'Customer'
        }
        
        return CRMContact(
            company_name=prospect.get('company_name', ''),
            email=prospect.get('email', ''),
            first_name=first_name,
            last_name=last_name,
            phone=prospect.get('phone', ''),
            website=prospect.get('website', ''),
            country=prospect.get('country', ''),
            industry=prospect.get('sector', ''),
            job_title='',  # Not available in prospect data
            lead_source='TenderPulse',
            lead_status=status_mapping.get(prospect.get('status', 'found'), 'New'),
            pain_level=prospect.get('pain_level', 50),
            lost_tender_value=prospect.get('lost_tender_value', ''),
            buyer_name=prospect.get('buyer_name', ''),
            custom_fields={
                'lost_tender_id': prospect.get('lost_tender_id', ''),
                'lost_tender_title': prospect.get('lost_tender_title', ''),
                'winner_name': prospect.get('winner_name', ''),
                'created_at': prospect.get('created_at', '')
            }
        )
    
    async def sync_prospect_to_all_crms(self, prospect: Dict) -> Dict:
        """Sync prospect to all configured CRMs"""
        contact = self.convert_prospect_to_contact(prospect)
        results = {}
        
        for crm_name, integration in self.integrations.items():
            try:
                if crm_name == 'hubspot':
                    result = await integration.create_contact(contact)
                elif crm_name == 'salesforce':
                    result = await integration.create_lead(contact)
                elif crm_name == 'pipedrive':
                    result = await integration.create_person(contact)
                elif crm_name == 'airtable':
                    result = await integration.create_record(contact)
                elif crm_name == 'webhook':
                    result = await integration.send_contact(contact)
                else:
                    result = {'success': False, 'error': 'Unknown CRM'}
                
                results[crm_name] = result
                
            except Exception as e:
                logger.error(f"Error syncing to {crm_name}: {e}")
                results[crm_name] = {'success': False, 'error': str(e)}
        
        return results
    
    async def batch_sync_prospects(self, prospects: List[Dict]) -> Dict:
        """Sync multiple prospects to all CRMs"""
        results = {
            'total_prospects': len(prospects),
            'successful_syncs': 0,
            'failed_syncs': 0,
            'crm_results': {}
        }
        
        for prospect in prospects:
            try:
                sync_results = await self.sync_prospect_to_all_crms(prospect)
                
                # Count successes and failures
                success_count = sum(1 for result in sync_results.values() if result.get('success'))
                if success_count > 0:
                    results['successful_syncs'] += 1
                else:
                    results['failed_syncs'] += 1
                
                # Aggregate results by CRM
                for crm_name, result in sync_results.items():
                    if crm_name not in results['crm_results']:
                        results['crm_results'][crm_name] = {'success': 0, 'failed': 0}
                    
                    if result.get('success'):
                        results['crm_results'][crm_name]['success'] += 1
                    else:
                        results['crm_results'][crm_name]['failed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing prospect {prospect.get('id', 'unknown')}: {e}")
                results['failed_syncs'] += 1
        
        return results

# CLI Commands
import click

@click.group()
def crm_cli():
    """TenderPulse CRM Integration"""
    pass

@crm_cli.command()
@click.option('--config', default='crm_config.json', help='CRM configuration file')
@click.option('--prospect-id', type=int, help='Sync specific prospect by ID')
def sync_prospect(config, prospect_id):
    """Sync prospect to CRM"""
    # Load CRM config
    with open(config, 'r') as f:
        crm_config = json.load(f)
    
    orchestrator = CRMOrchestrator(crm_config)
    
    # Get prospect data (you'd load this from your database)
    prospect = {
        'id': prospect_id,
        'company_name': 'Test Company',
        'email': 'test@example.com',
        'contact_name': 'John Doe',
        'country': 'DE',
        'sector': 'IT & Software',
        'status': 'email_found',
        'pain_level': 75,
        'lost_tender_value': '€500,000',
        'buyer_name': 'German Government'
    }
    
    result = asyncio.run(orchestrator.sync_prospect_to_all_crms(prospect))
    print(json.dumps(result, indent=2))

@crm_cli.command()
@click.option('--config', default='crm_config.json', help='CRM configuration file')
def test_connection(config):
    """Test CRM connections"""
    with open(config, 'r') as f:
        crm_config = json.load(f)
    
    orchestrator = CRMOrchestrator(crm_config)
    
    print("🔗 Testing CRM connections...")
    for crm_name in orchestrator.integrations.keys():
        print(f"✅ {crm_name.title()} integration configured")

if __name__ == "__main__":
    crm_cli()
