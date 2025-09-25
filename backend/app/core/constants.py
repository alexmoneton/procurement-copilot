"""Application constants and helper dictionaries."""

# Top 50 CPV families with human-readable labels
CPV_FAMILIES = {
    "72000000": "IT services: consulting, software development, Internet and support",
    "45000000": "Construction work",
    "48000000": "Software package and information systems",
    "79000000": "Business services: law, marketing, consulting, recruitment, printing and security",
    "80000000": "Education and training services",
    "71000000": "Architectural, construction, engineering and inspection services",
    "73000000": "Research and development services and related consultancy services",
    "75000000": "Administration, defence and social security services",
    "76000000": "Services related to the oil and gas industry",
    "77000000": "Agricultural, forestry, horticultural, aquacultural and apicultural services",
    "78000000": "Transport services (excl. Waste transport)",
    "79000000": "Business services: law, marketing, consulting, recruitment, printing and security",
    "80000000": "Education and training services",
    "85000000": "Health and social work services",
    "90000000": "Sewage-, refuse-, cleaning- and environmental services",
    "92000000": "Recreational, cultural and sporting services",
    "93000000": "Other community, social and personal services",
    "95000000": "Repair and maintenance services",
    "96000000": "Agricultural, forestry, horticultural, aquacultural and apicultural services",
    "98000000": "Other community, social and personal services",
    "03000000": "Agricultural, farming, fishing, forestry and related products",
    "09000000": "Petroleum products, fuel, electricity and other sources of energy",
    "14000000": "Mining, basic metals and related products",
    "15000000": "Food, beverages, tobacco and related products",
    "16000000": "Agricultural machinery",
    "18000000": "Clothing, footwear, luggage articles and accessories",
    "19000000": "Leather and textile fabrics, plastic and rubber materials",
    "22000000": "Printed matter and related products",
    "24000000": "Chemical products",
    "30000000": "Office and computing machinery, equipment and supplies except furniture and software packages",
    "31000000": "Electrical machinery, apparatus, equipment and consumables; lighting",
    "32000000": "Radio, television, communication, telecommunication and related equipment",
    "33000000": "Medical equipments, pharmaceuticals and personal care products",
    "34000000": "Transport equipment and auxiliary products to transportation",
    "35000000": "Security, fire-fighting, police and defence equipment",
    "37000000": "Musical instruments, sport goods, games, toys, handicraft, art materials and accessories",
    "38000000": "Laboratory, optical and precision equipments (excl. glasses)",
    "39000000": "Furniture (incl. office furniture), furnishings, domestic appliances (excl. lighting) and cleaning products",
    "41000000": "Water collection, treatment and supply",
    "42000000": "Industrial machinery",
    "43000000": "Machinery for mining, quarrying, construction equipment",
    "44000000": "Construction structures and materials; auxiliary products to construction (except electric apparatus)",
    "50000000": "Repair and maintenance services of motor vehicles and motorcycles",
    "51000000": "Installation services (except software)",
    "60000000": "Transport services (excl. Waste transport)",
    "61000000": "Support services for land, water, air and other transport",
    "62000000": "Public utilities",
    "63000000": "Supporting and auxiliary transport services; travel agencies services",
    "64000000": "Postal and telecommunications services",
    "65000000": "Public utilities",
    "66000000": "Financial and insurance services",
    "67000000": "Real estate services",
    "68000000": "Real estate services",
    "69000000": "Legal and accounting services",
    "70000000": "Real estate services",
    "71000000": "Architectural, construction, engineering and inspection services",
    "72000000": "IT services: consulting, software development, Internet and support",
    "73000000": "Research and development services and related consultancy services",
    "74000000": "Business services: law, marketing, consulting, recruitment, printing and security",
    "75000000": "Administration, defence and social security services",
    "76000000": "Services related to the oil and gas industry",
    "77000000": "Agricultural, forestry, horticultural, aquacultural and apicultural services",
    "78000000": "Transport services (excl. Waste transport)",
    "79000000": "Business services: law, marketing, consulting, recruitment, printing and security",
    "80000000": "Education and training services",
    "81000000": "Information technology services",
    "82000000": "Public utilities",
    "83000000": "Public utilities",
    "84000000": "Public utilities",
    "85000000": "Health and social work services",
    "86000000": "Public utilities",
    "87000000": "Public utilities",
    "88000000": "Public utilities",
    "89000000": "Public utilities",
    "90000000": "Sewage-, refuse-, cleaning- and environmental services",
    "91000000": "Public utilities",
    "92000000": "Recreational, cultural and sporting services",
    "93000000": "Other community, social and personal services",
    "94000000": "Public utilities",
    "95000000": "Repair and maintenance services",
    "96000000": "Agricultural, forestry, horticultural, aquacultural and apicultural services",
    "97000000": "Public utilities",
    "98000000": "Other community, social and personal services",
    "99000000": "Public utilities",
}

# EU-27 countries with their codes and names
EU_COUNTRIES = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DK": "Denmark",
    "EE": "Estonia",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",
    "GR": "Greece",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LV": "Latvia",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MT": "Malta",
    "NL": "Netherlands",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "ES": "Spain",
    "SE": "Sweden",
}

# Additional European countries (non-EU)
OTHER_EUROPEAN_COUNTRIES = {
    "AL": "Albania",
    "BA": "Bosnia and Herzegovina",
    "IS": "Iceland",
    "LI": "Liechtenstein",
    "MK": "North Macedonia",
    "MD": "Moldova",
    "ME": "Montenegro",
    "NO": "Norway",
    "RS": "Serbia",
    "CH": "Switzerland",
    "TR": "Turkey",
    "UA": "Ukraine",
    "GB": "United Kingdom",
}

# All European countries
ALL_EUROPEAN_COUNTRIES = {**EU_COUNTRIES, **OTHER_EUROPEAN_COUNTRIES}

# Currency codes and symbols
CURRENCIES = {
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "CHF": "CHF",
    "SEK": "kr",
    "NOK": "kr",
    "DKK": "kr",
    "PLN": "zł",
    "CZK": "Kč",
    "HUF": "Ft",
    "RON": "lei",
    "BGN": "лв",
    "HRK": "kn",
    "RSD": "дин",
    "MKD": "ден",
    "ALL": "L",
    "BAM": "KM",
    "ISK": "kr",
    "MDL": "L",
    "UAH": "₴",
    "TRY": "₺",
}

# Tender sources
TENDER_SOURCES = {
    "TED": "Tenders Electronic Daily",
    "BOAMP": "Bulletin Officiel des Annonces de Marchés Publics",
    "PLACE": "Plataforma de Contratación del Sector Público",
    "TEDES": "Tenders Electronic Daily España",
    "SIMAP": "Système d'Information pour les Marchés Publics",
    "TEDEX": "Tenders Electronic Daily Express",
}

# Notification frequencies
NOTIFICATION_FREQUENCIES = {
    "DAILY": "Daily",
    "WEEKLY": "Weekly",
    "MONTHLY": "Monthly",
    "IMMEDIATE": "Immediate",
}

# Outreach campaign types
OUTREACH_CAMPAIGNS = {
    "missed_opportunities": "Missed Opportunities",
    "cross_border_expansion": "Cross-Border Expansion",
    "reactivation": "Reactivation",
}

# Outreach targeting strategies
OUTREACH_STRATEGIES = {
    "lost_bidders": "Active but Losing SMEs",
    "cross_border": "Cross-Border Potential",
    "lapsed": "Lapsed Bidders",
}

# Subscription plans
SUBSCRIPTION_PLANS = {
    "starter": {
        "name": "Starter",
        "price": 99,
        "currency": "EUR",
        "filters": 1,
        "description": "Perfect for small businesses",
    },
    "pro": {
        "name": "Pro",
        "price": 199,
        "currency": "EUR",
        "filters": 5,
        "description": "Ideal for growing companies",
    },
    "team": {
        "name": "Team",
        "price": 399,
        "currency": "EUR",
        "filters": 15,
        "description": "Built for teams and enterprises",
    },
}

# Industry sectors (mapped to CPV codes)
INDUSTRY_SECTORS = {
    "it_services": {
        "name": "IT Services",
        "cpv_codes": ["72000000", "48000000", "81000000"],
        "keywords": ["software", "development", "IT", "digital", "technology"],
    },
    "construction": {
        "name": "Construction",
        "cpv_codes": ["45000000", "71000000", "44000000"],
        "keywords": ["construction", "building", "infrastructure", "civil works"],
    },
    "consulting": {
        "name": "Consulting",
        "cpv_codes": ["79000000", "80000000", "73000000"],
        "keywords": ["consulting", "advisory", "strategy", "management"],
    },
    "healthcare": {
        "name": "Healthcare",
        "cpv_codes": ["85000000", "33000000"],
        "keywords": ["health", "medical", "pharmaceutical", "care"],
    },
    "education": {
        "name": "Education",
        "cpv_codes": ["80000000", "92000000"],
        "keywords": ["education", "training", "learning", "academic"],
    },
    "transport": {
        "name": "Transport",
        "cpv_codes": ["60000000", "34000000", "78000000"],
        "keywords": ["transport", "logistics", "shipping", "delivery"],
    },
    "energy": {
        "name": "Energy",
        "cpv_codes": ["09000000", "76000000"],
        "keywords": ["energy", "power", "electricity", "renewable"],
    },
    "environment": {
        "name": "Environment",
        "cpv_codes": ["90000000", "77000000"],
        "keywords": ["environment", "waste", "recycling", "sustainability"],
    },
}


def get_cpv_label(cpv_code: str) -> str:
    """Get human-readable label for CPV code."""
    # Get the 8-digit CPV code (first 8 characters)
    cpv_8_digit = cpv_code[:8] if len(cpv_code) >= 8 else cpv_code

    # Try to find exact match first
    if cpv_8_digit in CPV_FAMILIES:
        return CPV_FAMILIES[cpv_8_digit]

    # Try to find by family (first 2 digits)
    cpv_family = cpv_code[:2] + "000000"
    if cpv_family in CPV_FAMILIES:
        return CPV_FAMILIES[cpv_family]

    # Return the code if no match found
    return cpv_code


def get_country_name(country_code: str) -> str:
    """Get country name from country code."""
    return ALL_EUROPEAN_COUNTRIES.get(country_code.upper(), country_code)


def get_currency_symbol(currency_code: str) -> str:
    """Get currency symbol from currency code."""
    return CURRENCIES.get(currency_code.upper(), currency_code)


def get_industry_sector(cpv_codes: list) -> str:
    """Get industry sector from CPV codes."""
    for sector, data in INDUSTRY_SECTORS.items():
        if any(cpv in data["cpv_codes"] for cpv in cpv_codes):
            return data["name"]
    return "Other"


def format_currency(amount: float, currency: str = "EUR") -> str:
    """Format currency amount with symbol."""
    symbol = get_currency_symbol(currency)
    if currency == "EUR":
        return f"€{amount:,.0f}"
    elif currency == "USD":
        return f"${amount:,.0f}"
    elif currency == "GBP":
        return f"£{amount:,.0f}"
    else:
        return f"{amount:,.0f} {currency}"
