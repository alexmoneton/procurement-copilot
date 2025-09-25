"""CPV (Common Procurement Vocabulary) mapping and keyword matching utilities."""

import re
from typing import Dict, List, Optional, Set

from loguru import logger


class CPVMapper:
    """CPV code mapping and keyword matching utilities."""

    def __init__(self):
        self.logger = logger.bind(service="cpv_mapper")
        self.cpv_mappings = self._load_cpv_mappings()
        self.keyword_mappings = self._load_keyword_mappings()

    def _load_cpv_mappings(self) -> Dict[str, Dict[str, str]]:
        """Load CPV code mappings."""
        # This is a simplified mapping - in production, you'd load from a database or file
        return {
            "03000000": {
                "name": "Agricultural, farming, fishing, forestry and related products",
                "keywords": [
                    "agriculture",
                    "farming",
                    "fishing",
                    "forestry",
                    "crops",
                    "livestock",
                ],
            },
            "09000000": {
                "name": "Petroleum products, fuel, electricity and other sources of energy",
                "keywords": [
                    "petroleum",
                    "fuel",
                    "electricity",
                    "energy",
                    "gas",
                    "oil",
                    "power",
                ],
            },
            "15000000": {
                "name": "Food, beverages, tobacco and related products",
                "keywords": [
                    "food",
                    "beverages",
                    "tobacco",
                    "catering",
                    "restaurant",
                    "meals",
                ],
            },
            "16000000": {
                "name": "Agricultural machinery",
                "keywords": [
                    "agricultural",
                    "machinery",
                    "tractor",
                    "harvester",
                    "farming equipment",
                ],
            },
            "18000000": {
                "name": "Clothing, footwear, luggage articles and accessories",
                "keywords": ["clothing", "footwear", "luggage", "uniforms", "textiles"],
            },
            "22000000": {
                "name": "Printed matter and related products",
                "keywords": ["printing", "books", "publications", "documents", "paper"],
            },
            "24000000": {
                "name": "Chemical products",
                "keywords": [
                    "chemical",
                    "pharmaceutical",
                    "medicine",
                    "drugs",
                    "laboratory",
                ],
            },
            "30000000": {
                "name": "Office and computing machinery, equipment and supplies except furniture and software packages",
                "keywords": [
                    "office",
                    "computing",
                    "hardware",
                    "equipment",
                    "supplies",
                ],
            },
            "31000000": {
                "name": "Electrical machinery, apparatus, equipment and consumables; lighting",
                "keywords": [
                    "electrical",
                    "machinery",
                    "lighting",
                    "electronics",
                    "cables",
                ],
            },
            "32000000": {
                "name": "Radio, television, communication, telecommunication and related equipment",
                "keywords": [
                    "radio",
                    "television",
                    "communication",
                    "telecommunication",
                    "broadcasting",
                ],
            },
            "34000000": {
                "name": "Transport equipment and auxiliary products to transportation",
                "keywords": [
                    "transport",
                    "vehicles",
                    "automotive",
                    "aircraft",
                    "ships",
                    "trains",
                ],
            },
            "35000000": {
                "name": "Security, fire-fighting, police and defence equipment",
                "keywords": [
                    "security",
                    "fire-fighting",
                    "police",
                    "defence",
                    "military",
                    "weapons",
                ],
            },
            "37000000": {
                "name": "Musical instruments, sport goods, games, toys, handicraft, art materials and accessories",
                "keywords": ["musical", "sport", "games", "toys", "handicraft", "art"],
            },
            "38000000": {
                "name": "Laboratory, optical and precision equipments (excl. glasses)",
                "keywords": [
                    "laboratory",
                    "optical",
                    "precision",
                    "scientific",
                    "instruments",
                ],
            },
            "39000000": {
                "name": "Furniture (incl. office furniture), furnishings, domestic appliances (excl. lighting) and cleaning products",
                "keywords": [
                    "furniture",
                    "furnishings",
                    "appliances",
                    "cleaning",
                    "office furniture",
                ],
            },
            "41000000": {
                "name": "Water collection, treatment and supply",
                "keywords": ["water", "treatment", "supply", "wastewater", "sewage"],
            },
            "42000000": {
                "name": "Industrial machinery",
                "keywords": [
                    "industrial",
                    "machinery",
                    "manufacturing",
                    "production",
                    "equipment",
                ],
            },
            "43000000": {
                "name": "Machinery for mining, quarrying, construction equipment",
                "keywords": [
                    "mining",
                    "quarrying",
                    "construction",
                    "excavation",
                    "bulldozer",
                ],
            },
            "44000000": {
                "name": "Construction structures and materials; auxiliary products to construction (except electric apparatus)",
                "keywords": [
                    "construction",
                    "materials",
                    "building",
                    "cement",
                    "steel",
                    "concrete",
                ],
            },
            "45000000": {
                "name": "Construction work",
                "keywords": [
                    "construction",
                    "building",
                    "renovation",
                    "infrastructure",
                    "civil works",
                ],
            },
            "48000000": {
                "name": "Software package and information systems",
                "keywords": [
                    "software",
                    "information systems",
                    "IT",
                    "computer programs",
                    "applications",
                ],
            },
            "50000000": {
                "name": "Repair and maintenance services",
                "keywords": [
                    "repair",
                    "maintenance",
                    "service",
                    "upkeep",
                    "restoration",
                ],
            },
            "51000000": {
                "name": "Installation services (except software)",
                "keywords": [
                    "installation",
                    "setup",
                    "assembly",
                    "fitting",
                    "mounting",
                ],
            },
            "55000000": {
                "name": "Hotel, restaurant and retail trade services",
                "keywords": [
                    "hotel",
                    "restaurant",
                    "retail",
                    "catering",
                    "hospitality",
                ],
            },
            "60000000": {
                "name": "Transport services (excl. Waste transport)",
                "keywords": [
                    "transport",
                    "shipping",
                    "logistics",
                    "freight",
                    "delivery",
                ],
            },
            "63000000": {
                "name": "Supporting and auxiliary transport services; travel agencies services",
                "keywords": [
                    "supporting",
                    "auxiliary",
                    "travel",
                    "agencies",
                    "tourism",
                ],
            },
            "64000000": {
                "name": "Postal and telecommunications services",
                "keywords": [
                    "postal",
                    "telecommunications",
                    "mail",
                    "phone",
                    "internet",
                ],
            },
            "65000000": {
                "name": "Public utilities",
                "keywords": [
                    "utilities",
                    "public",
                    "infrastructure",
                    "services",
                    "facilities",
                ],
            },
            "66000000": {
                "name": "Financial and insurance services",
                "keywords": [
                    "financial",
                    "insurance",
                    "banking",
                    "investment",
                    "pension",
                ],
            },
            "70000000": {
                "name": "Real estate services",
                "keywords": [
                    "real estate",
                    "property",
                    "leasing",
                    "rental",
                    "accommodation",
                ],
            },
            "71000000": {
                "name": "Architectural, construction, engineering and inspection services",
                "keywords": [
                    "architectural",
                    "construction",
                    "engineering",
                    "inspection",
                    "design",
                ],
            },
            "72000000": {
                "name": "IT services: consulting, software development, Internet and support",
                "keywords": [
                    "IT",
                    "consulting",
                    "software development",
                    "internet",
                    "support",
                    "technology",
                ],
            },
            "73000000": {
                "name": "Research and development services and related consultancy services",
                "keywords": [
                    "research",
                    "development",
                    "R&D",
                    "consultancy",
                    "innovation",
                ],
            },
            "75000000": {
                "name": "Administration, defence and social security services",
                "keywords": [
                    "administration",
                    "defence",
                    "social security",
                    "government",
                    "public",
                ],
            },
            "76000000": {
                "name": "Services related to the oil and gas industry",
                "keywords": [
                    "oil",
                    "gas",
                    "petroleum",
                    "energy",
                    "drilling",
                    "extraction",
                ],
            },
            "77000000": {
                "name": "Agricultural, forestry, horticultural, aquacultural and apicultural services",
                "keywords": [
                    "agricultural",
                    "forestry",
                    "horticultural",
                    "aquacultural",
                    "apicultural",
                ],
            },
            "79000000": {
                "name": "Business services: law, marketing, consulting, recruitment, printing and security",
                "keywords": [
                    "business",
                    "law",
                    "marketing",
                    "consulting",
                    "recruitment",
                    "security",
                ],
            },
            "80000000": {
                "name": "Education and training services",
                "keywords": [
                    "education",
                    "training",
                    "learning",
                    "teaching",
                    "courses",
                ],
            },
            "85000000": {
                "name": "Health and social work services",
                "keywords": [
                    "health",
                    "social work",
                    "medical",
                    "healthcare",
                    "welfare",
                ],
            },
            "90000000": {
                "name": "Sewage, refuse, cleaning and environmental services",
                "keywords": [
                    "sewage",
                    "refuse",
                    "cleaning",
                    "environmental",
                    "waste",
                    "recycling",
                ],
            },
            "92000000": {
                "name": "Recreational, cultural and sporting services",
                "keywords": [
                    "recreational",
                    "cultural",
                    "sporting",
                    "entertainment",
                    "leisure",
                ],
            },
            "98000000": {
                "name": "Other community, social and personal services",
                "keywords": ["community", "social", "personal", "services", "other"],
            },
        }

    def _load_keyword_mappings(self) -> Dict[str, List[str]]:
        """Load keyword to CPV code mappings."""
        keyword_mappings = {}

        for cpv_code, data in self.cpv_mappings.items():
            for keyword in data["keywords"]:
                if keyword not in keyword_mappings:
                    keyword_mappings[keyword] = []
                keyword_mappings[keyword].append(cpv_code)

        return keyword_mappings

    def get_cpv_info(self, cpv_code: str) -> Optional[Dict[str, str]]:
        """Get information about a CPV code."""
        # Normalize CPV code (remove dots, take first 8 digits)
        normalized_code = self._normalize_cpv_code(cpv_code)

        # Try exact match first
        if normalized_code in self.cpv_mappings:
            return self.cpv_mappings[normalized_code]

        # Try parent categories (first 6, 4, 2 digits)
        for length in [6, 4, 2]:
            parent_code = normalized_code[:length].ljust(8, "0")
            if parent_code in self.cpv_mappings:
                return self.cpv_mappings[parent_code]

        return None

    def find_cpv_codes_by_keywords(self, text: str) -> List[str]:
        """Find CPV codes based on keywords in text."""
        if not text:
            return []

        text_lower = text.lower()
        found_codes = set()

        # Search for keyword matches
        for keyword, cpv_codes in self.keyword_mappings.items():
            if keyword in text_lower:
                found_codes.update(cpv_codes)

        # Search for CPV codes directly in text
        cpv_pattern = r"\b\d{8}\b"
        direct_codes = re.findall(cpv_pattern, text)
        for code in direct_codes:
            normalized = self._normalize_cpv_code(code)
            if self.get_cpv_info(normalized):
                found_codes.add(normalized)

        return list(found_codes)

    def suggest_cpv_codes(self, title: str, summary: str = None) -> List[str]:
        """Suggest CPV codes based on title and summary."""
        text = title
        if summary:
            text += " " + summary

        return self.find_cpv_codes_by_keywords(text)

    def _normalize_cpv_code(self, cpv_code: str) -> str:
        """Normalize CPV code to 8-digit format."""
        if not cpv_code:
            return ""

        # Remove dots and spaces
        cleaned = re.sub(r"[.\s]", "", str(cpv_code))

        # Take first 8 digits
        if len(cleaned) >= 8:
            return cleaned[:8]
        else:
            # Pad with zeros
            return cleaned.ljust(8, "0")

    def get_cpv_hierarchy(self, cpv_code: str) -> List[Dict[str, str]]:
        """Get CPV code hierarchy (parent categories)."""
        normalized_code = self._normalize_cpv_code(cpv_code)
        hierarchy = []

        # Add current code
        info = self.get_cpv_info(normalized_code)
        if info:
            hierarchy.append(
                {
                    "code": normalized_code,
                    "name": info["name"],
                    "level": self._get_cpv_level(normalized_code),
                }
            )

        # Add parent categories
        for length in [6, 4, 2]:
            parent_code = normalized_code[:length].ljust(8, "0")
            if parent_code != normalized_code:
                parent_info = self.get_cpv_info(parent_code)
                if parent_info:
                    hierarchy.append(
                        {
                            "code": parent_code,
                            "name": parent_info["name"],
                            "level": self._get_cpv_level(parent_code),
                        }
                    )

        return hierarchy

    def _get_cpv_level(self, cpv_code: str) -> int:
        """Get CPV code level (2, 4, 6, or 8 digits)."""
        if not cpv_code:
            return 0

        # Count non-zero digits from the end
        code = cpv_code.rstrip("0")
        return len(code)

    def validate_cpv_codes(self, cpv_codes: List[str]) -> List[str]:
        """Validate and normalize a list of CPV codes."""
        valid_codes = []

        for code in cpv_codes:
            normalized = self._normalize_cpv_code(code)
            if normalized and self.get_cpv_info(normalized):
                valid_codes.append(normalized)
            else:
                self.logger.warning(f"Invalid CPV code: {code}")

        return valid_codes


# Global instance
cpv_mapper = CPVMapper()
