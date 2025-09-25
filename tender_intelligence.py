"""
TenderPulse Intelligence Engine - Integrated for Flask Dashboard
Transform raw tender data into actionable insights for clients
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re
import sqlite3
import json

class TenderIntelligence:
    """Transform raw tender data into actionable insights"""
    
    def __init__(self):
        self.cpv_descriptions = {
            '45000000': 'Construction work',
            '72000000': 'IT services',
            '50000000': 'Repair and maintenance services',
            '79000000': 'Business services',
            '71000000': 'Architectural and engineering services',
            '73000000': 'Research and development services',
            '80000000': 'Education and training services',
            '85000000': 'Health and social work services',
            '90000000': 'Sewage, refuse, cleaning services',
            '92000000': 'Recreational, cultural and sporting services'
        }
        
        self.country_difficulty = {
            'DE': {'difficulty': 0.7, 'avg_bidders': 8, 'success_tips': 'German tenders require precise technical specs'},
            'FR': {'difficulty': 0.6, 'avg_bidders': 6, 'success_tips': 'French buyers prefer local partnerships'},
            'NL': {'difficulty': 0.5, 'avg_bidders': 5, 'success_tips': 'Dutch procurement values sustainability highly'},
            'IT': {'difficulty': 0.8, 'avg_bidders': 12, 'success_tips': 'Italian tenders often have complex bureaucracy'},
            'ES': {'difficulty': 0.6, 'avg_bidders': 7, 'success_tips': 'Spanish regions have varying requirements'},
            'PL': {'difficulty': 0.4, 'avg_bidders': 4, 'success_tips': 'Polish market has growing opportunities'},
            'SE': {'difficulty': 0.5, 'avg_bidders': 5, 'success_tips': 'Swedish procurement emphasizes innovation'},
            'NO': {'difficulty': 0.6, 'avg_bidders': 6, 'success_tips': 'Norwegian tenders often require local presence'}
        }
    
    def calculate_smart_score(self, tender: Dict, user_profile: Dict) -> int:
        """Calculate intelligent opportunity score (0-100)"""
        score = 50  # Base score
        
        # Value match (sweet spot scoring)
        tender_value = self.extract_value(tender.get('value_amount', 0))
        user_sweet_spot = user_profile.get('target_value_range', [50000, 2000000])
        
        if user_sweet_spot[0] <= tender_value <= user_sweet_spot[1]:
            score += 25
        elif tender_value < user_sweet_spot[0]:
            score -= 10  # Too small
        elif tender_value > user_sweet_spot[1] * 2:
            score -= 20  # Too big
        
        # Geographic preference
        country = tender.get('buyer_country', '')
        if country in user_profile.get('preferred_countries', []):
            score += 15
        
        # CPV match
        tender_cpvs = tender.get('cpv_codes', [])
        user_cpvs = user_profile.get('cpv_expertise', [])
        if any(cpv[:2] == user_cpv[:2] for cpv in tender_cpvs for user_cpv in user_cpvs):
            score += 20
        
        # Competition level (fewer bidders = higher score)
        expected_bidders = self.country_difficulty.get(country, {}).get('avg_bidders', 6)
        if expected_bidders <= 4:
            score += 15
        elif expected_bidders >= 10:
            score -= 10
        
        # Deadline pressure (more time = higher score for preparation)
        days_until_deadline = self.calculate_days_until_deadline(tender.get('deadline_date'))
        if days_until_deadline >= 30:
            score += 10
        elif days_until_deadline <= 7:
            score -= 15
        
        return max(0, min(100, int(score)))
    
    def generate_winning_strategy(self, tender: Dict, user_profile: Dict) -> Dict:
        """Generate specific advice for winning this tender"""
        country = tender.get('buyer_country', '')
        country_info = self.country_difficulty.get(country, {})
        
        strategy = {
            'success_probability': f"{self.calculate_smart_score(tender, user_profile)}%",
            'competition_level': self.estimate_competition(tender),
            'key_success_factors': [
                country_info.get('success_tips', 'Focus on technical excellence'),
                self.get_cpv_specific_advice(tender.get('cpv_codes', [])),
                self.get_value_specific_advice(tender.get('value_amount', 0))
            ],
            'preparation_checklist': self.generate_checklist(tender, country),
            'deadline_strategy': self.get_deadline_strategy(tender.get('deadline_date'))
        }
        return strategy
    
    def estimate_competition(self, tender: Dict) -> str:
        """Estimate number of expected bidders"""
        country = tender.get('buyer_country', '')
        base_competition = self.country_difficulty.get(country, {}).get('avg_bidders', 6)
        
        # Adjust based on tender characteristics
        tender_value = self.extract_value(tender.get('value_amount', 0))
        if tender_value > 5000000:  # €5M+
            base_competition += 3  # High-value attracts more bidders
        elif tender_value < 100000:  # €100K-
            base_competition -= 2  # Small tenders get less attention
        
        return f"{max(2, base_competition-1)}-{base_competition+2} bidders expected"
    
    def generate_checklist(self, tender: Dict, country: str) -> List[str]:
        """Generate country-specific compliance checklist"""
        base_checklist = [
            "Register on national procurement platform",
            "Prepare technical specifications document",
            "Obtain required certifications",
            "Prepare financial statements",
            "Draft project timeline",
            "Calculate detailed pricing"
        ]
        
        country_specific = {
            'DE': ["Obtain German tax certificate", "Prepare detailed Leistungsverzeichnis"],
            'FR': ["Register for French SIRET number", "Prepare MAPA documentation"],
            'NL': ["Complete DigiD business registration", "Prepare sustainability statement"],
            'IT': ["Obtain Italian fiscal code", "Prepare anti-mafia certification"],
            'ES': ["Register in Spanish ROLECE", "Prepare regional language documents"],
            'PL': ["Register in Polish REGON database", "Prepare Polish language documents"],
            'SE': ["Register in Swedish company database", "Prepare environmental impact statement"],
            'NO': ["Register for Norwegian organization number", "Prepare local content requirements"]
        }
        
        return base_checklist + country_specific.get(country, [])
    
    def extract_value(self, value) -> int:
        """Extract numeric value from various formats"""
        if isinstance(value, (int, float)):
            return int(value)
        
        if isinstance(value, str):
            # Extract numbers from value string
            numbers = re.findall(r'[\d,]+', value)
            if numbers:
                try:
                    clean_number = numbers[0].replace(',', '')
                    return int(clean_number)
                except:
                    pass
        
        return 0
    
    def calculate_days_until_deadline(self, deadline_str: Optional[str]) -> int:
        """Calculate days until deadline"""
        if not deadline_str:
            return 30  # Default assumption
        
        try:
            # Handle various date formats
            clean_date = deadline_str.split('+')[0].split('T')[0]
            deadline = datetime.strptime(clean_date, '%Y-%m-%d').date()
            today = datetime.now().date()
            return (deadline - today).days
        except:
            return 30  # Default assumption
    
    def get_cpv_specific_advice(self, cpv_codes: List[str]) -> str:
        """Get advice specific to CPV category"""
        if not cpv_codes:
            return "Focus on clear technical specifications"
        
        main_cpv = cpv_codes[0][:2] if cpv_codes else ""
        
        advice_map = {
            '45': 'Construction: Emphasize safety certifications and previous project portfolio',
            '72': 'IT Services: Highlight security clearances and technical certifications',
            '50': 'Maintenance: Focus on response times and preventive maintenance capabilities',
            '79': 'Business Services: Emphasize methodology and previous client success stories',
            '71': 'Engineering: Showcase technical expertise and regulatory compliance',
            '73': 'R&D: Highlight innovation track record and research partnerships'
        }
        
        return advice_map.get(main_cpv, "Focus on technical excellence and compliance")
    
    def get_value_specific_advice(self, value: int) -> str:
        """Get advice based on contract value"""
        if value < 100000:
            return "Small contract: Focus on competitive pricing and quick delivery"
        elif value < 1000000:
            return "Medium contract: Balance price competitiveness with quality guarantees"
        else:
            return "Large contract: Emphasize track record, partnerships, and risk management"
    
    def get_deadline_strategy(self, deadline_str: Optional[str]) -> str:
        """Get strategy based on deadline timing"""
        days_left = self.calculate_days_until_deadline(deadline_str)
        
        if days_left <= 7:
            return "⚠️ URGENT: Focus on existing capabilities, minimal customization"
        elif days_left <= 21:
            return "⏰ MODERATE: Prepare detailed proposal with some customization"
        else:
            return "✅ AMPLE TIME: Full proposal development with partnerships and customization"


class ClientProfileManager:
    """Manage client profiles for tender matching"""
    
    def __init__(self, db_path: str = "client_profiles.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize client profiles database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_name TEXT NOT NULL,
                target_value_range TEXT NOT NULL,
                preferred_countries TEXT NOT NULL,
                cpv_expertise TEXT NOT NULL,
                company_size TEXT,
                experience_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_profile(self, user_id: int, profile_data: Dict) -> int:
        """Create a new client profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO client_profiles 
            (user_id, company_name, target_value_range, preferred_countries, 
             cpv_expertise, company_size, experience_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            profile_data['company_name'],
            json.dumps(profile_data['target_value_range']),
            json.dumps(profile_data['preferred_countries']),
            json.dumps(profile_data['cpv_expertise']),
            profile_data.get('company_size', ''),
            profile_data.get('experience_level', '')
        ))
        
        profile_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return profile_id
    
    def get_profile(self, user_id: int) -> Optional[Dict]:
        """Get client profile by user ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM client_profiles WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'company_name': row[2],
                'target_value_range': json.loads(row[3]),
                'preferred_countries': json.loads(row[4]),
                'cpv_expertise': json.loads(row[5]),
                'company_size': row[6],
                'experience_level': row[7],
                'created_at': row[8],
                'updated_at': row[9]
            }
        
        return None
    
    def update_profile(self, user_id: int, profile_data: Dict) -> bool:
        """Update existing client profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE client_profiles 
            SET company_name = ?, target_value_range = ?, preferred_countries = ?,
                cpv_expertise = ?, company_size = ?, experience_level = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (
            profile_data['company_name'],
            json.dumps(profile_data['target_value_range']),
            json.dumps(profile_data['preferred_countries']),
            json.dumps(profile_data['cpv_expertise']),
            profile_data.get('company_size', ''),
            profile_data.get('experience_level', ''),
            user_id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success


class TenderMatcher:
    """Match tenders with client profiles"""
    
    def __init__(self):
        self.intelligence = TenderIntelligence()
        self.profile_manager = ClientProfileManager()
    
    def get_matching_tenders(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get tenders matching client profile"""
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            return []
        
        # Get sample tenders (in real implementation, this would query the TED database)
        sample_tenders = self.get_sample_tenders()
        
        # Calculate smart scores and filter
        matching_tenders = []
        for tender in sample_tenders:
            score = self.intelligence.calculate_smart_score(tender, profile)
            if score >= 50:  # Only show tenders with 50%+ match
                tender['smart_score'] = score
                tender['winning_strategy'] = self.intelligence.generate_winning_strategy(tender, profile)
                matching_tenders.append(tender)
        
        # Sort by smart score
        matching_tenders.sort(key=lambda x: x['smart_score'], reverse=True)
        
        return matching_tenders[:limit]
    
    def get_sample_tenders(self) -> List[Dict]:
        """Get sample tenders for demonstration"""
        return [
            {
                'id': 'TED-001',
                'title': 'Germany-Berlin: IT consulting services for digital transformation',
                'value_amount': 850000,
                'buyer_country': 'DE',
                'buyer_name': 'Berlin Municipality',
                'deadline_date': '2024-11-15',
                'cpv_codes': ['72000000'],
                'url': 'https://ted.europa.eu/udl?uri=TED:NOTICE:001',
                'summary': 'Digital transformation consulting services for municipal operations'
            },
            {
                'id': 'TED-002',
                'title': 'France-Paris: Construction of sustainable office building',
                'value_amount': 2500000,
                'buyer_country': 'FR',
                'buyer_name': 'Paris City Council',
                'deadline_date': '2024-12-01',
                'cpv_codes': ['45000000'],
                'url': 'https://ted.europa.eu/udl?uri=TED:NOTICE:002',
                'summary': 'Construction of energy-efficient office building with green certifications'
            },
            {
                'id': 'TED-003',
                'title': 'Netherlands-Amsterdam: Software development for public services',
                'value_amount': 650000,
                'buyer_country': 'NL',
                'buyer_name': 'Amsterdam Municipality',
                'deadline_date': '2024-10-30',
                'cpv_codes': ['72000000'],
                'url': 'https://ted.europa.eu/udl?uri=TED:NOTICE:003',
                'summary': 'Development of citizen portal and digital services platform'
            },
            {
                'id': 'TED-004',
                'title': 'Italy-Rome: Business consulting for public administration',
                'value_amount': 450000,
                'buyer_country': 'IT',
                'buyer_name': 'Rome Municipality',
                'deadline_date': '2024-11-20',
                'cpv_codes': ['79000000'],
                'url': 'https://ted.europa.eu/udl?uri=TED:NOTICE:004',
                'summary': 'Organizational consulting and process optimization for municipal services'
            },
            {
                'id': 'TED-005',
                'title': 'Spain-Madrid: Environmental consulting services',
                'value_amount': 320000,
                'buyer_country': 'ES',
                'buyer_name': 'Madrid City Council',
                'deadline_date': '2024-11-10',
                'cpv_codes': ['90000000'],
                'url': 'https://ted.europa.eu/udl?uri=TED:NOTICE:005',
                'summary': 'Environmental impact assessment and sustainability consulting'
            }
        ]
