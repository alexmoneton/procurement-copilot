"""Company data resolution service for enriching supplier information."""

import csv
import io
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.crud import CompanyCRUD
from ..db.schemas import CompanyCreate


class CompanyResolutionService:
    """Service for resolving and enriching company data."""

    def __init__(self):
        self.logger = logger.bind(service="company_resolution")

    async def resolve_company_from_name(
        self, db: AsyncSession, company_name: str, country: str
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to resolve company information from name and country.
        For MVP, this is a placeholder that could be enhanced with:
        - Company registry APIs
        - Domain search APIs
        - Email finding services
        """
        self.logger.info(f"Resolving company: {company_name} in {country}")

        # Check if company already exists in database
        existing_company = await CompanyCRUD.get_by_name_and_country(
            db, company_name, country
        )

        if existing_company:
            self.logger.info(f"Found existing company: {existing_company.id}")
            return {
                "id": existing_company.id,
                "name": existing_company.name,
                "domain": existing_company.domain,
                "email": existing_company.email,
                "country": existing_company.country,
                "is_suppressed": existing_company.is_suppressed,
            }

        # For MVP, create company with basic info
        # In production, this would call external APIs to find domain/email
        company_data = CompanyCreate(
            name=company_name,
            country=country.upper(),
            domain=None,  # Would be resolved via API
            email=None,  # Would be resolved via API
        )

        try:
            new_company = await CompanyCRUD.create(db, company_data)
            self.logger.info(f"Created new company: {new_company.id}")
            return {
                "id": new_company.id,
                "name": new_company.name,
                "domain": new_company.domain,
                "email": new_company.email,
                "country": new_company.country,
                "is_suppressed": new_company.is_suppressed,
            }
        except Exception as e:
            self.logger.error(f"Error creating company: {e}")
            return None

    async def import_companies_from_csv(
        self, db: AsyncSession, csv_content: str, has_header: bool = True
    ) -> Dict[str, Any]:
        """
        Import companies from CSV content.
        Expected columns: name, domain, email, country
        """
        self.logger.info("Importing companies from CSV")

        results = {"imported": 0, "updated": 0, "errors": 0, "error_details": []}

        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content))

            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
                try:
                    # Extract data from row
                    name = row.get("name", "").strip()
                    domain = row.get("domain", "").strip() or None
                    email = row.get("email", "").strip() or None
                    country = row.get("country", "").strip().upper()

                    if not name or not country:
                        results["errors"] += 1
                        results["error_details"].append(
                            f"Row {row_num}: Missing name or country"
                        )
                        continue

                    # Validate country code (should be 2 characters)
                    if len(country) != 2:
                        results["errors"] += 1
                        results["error_details"].append(
                            f"Row {row_num}: Invalid country code '{country}'"
                        )
                        continue

                    # Validate email format if provided
                    if email and "@" not in email:
                        results["errors"] += 1
                        results["error_details"].append(
                            f"Row {row_num}: Invalid email format '{email}'"
                        )
                        continue

                    # Validate domain format if provided
                    if domain and "." not in domain:
                        results["errors"] += 1
                        results["error_details"].append(
                            f"Row {row_num}: Invalid domain format '{domain}'"
                        )
                        continue

                    # Create or update company
                    company_data = CompanyCreate(
                        name=name, domain=domain, email=email, country=country
                    )

                    # Check if company already exists
                    existing = await CompanyCRUD.get_by_name_and_country(
                        db, name, country
                    )

                    if existing:
                        # Update existing company
                        from ..db.schemas import CompanyUpdate

                        update_data = CompanyUpdate(domain=domain, email=email)
                        updated_company = await CompanyCRUD.update(
                            db, existing.id, update_data
                        )
                        if updated_company:
                            results["updated"] += 1
                        else:
                            results["errors"] += 1
                            results["error_details"].append(
                                f"Row {row_num}: Failed to update company"
                            )
                    else:
                        # Create new company
                        new_company = await CompanyCRUD.create(db, company_data)
                        if new_company:
                            results["imported"] += 1
                        else:
                            results["errors"] += 1
                            results["error_details"].append(
                                f"Row {row_num}: Failed to create company"
                            )

                except Exception as e:
                    results["errors"] += 1
                    results["error_details"].append(f"Row {row_num}: {str(e)}")
                    self.logger.error(f"Error processing row {row_num}: {e}")

        except Exception as e:
            self.logger.error(f"Error parsing CSV: {e}")
            results["errors"] += 1
            results["error_details"].append(f"CSV parsing error: {str(e)}")

        self.logger.info(
            f"CSV import completed: {results['imported']} imported, "
            f"{results['updated']} updated, {results['errors']} errors"
        )

        return results

    async def enrich_company_data(
        self, db: AsyncSession, company_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Enrich company data using external APIs.
        This is a placeholder for future implementation.
        """
        self.logger.info(f"Enriching company data for: {company_id}")

        # Placeholder for external API calls
        # In production, this would:
        # 1. Call company registry APIs
        # 2. Search for company website/domain
        # 3. Find contact emails
        # 4. Update company record

        return {
            "status": "placeholder",
            "message": "Company enrichment not implemented yet",
        }

    async def find_company_domain(
        self, company_name: str, country: str
    ) -> Optional[str]:
        """
        Find company domain using search APIs.
        This is a placeholder for future implementation.
        """
        self.logger.info(f"Finding domain for: {company_name} in {country}")

        # Placeholder for domain search
        # In production, this would use:
        # - Google Custom Search API
        # - Company registry APIs
        # - Domain suggestion services

        return None

    async def find_company_email(self, company_name: str, domain: str) -> Optional[str]:
        """
        Find company email using email finding services.
        This is a placeholder for future implementation.
        """
        self.logger.info(f"Finding email for: {company_name} at {domain}")

        # Placeholder for email finding
        # In production, this would use:
        # - Hunter.io API
        # - Clearbit API
        # - Email finding services

        return None

    async def validate_company_data(
        self, company_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate company data and return validation results."""
        validation_results = {"is_valid": True, "errors": [], "warnings": []}

        # Validate required fields
        if not company_data.get("name"):
            validation_results["is_valid"] = False
            validation_results["errors"].append("Company name is required")

        if not company_data.get("country"):
            validation_results["is_valid"] = False
            validation_results["errors"].append("Country is required")
        elif len(company_data.get("country", "")) != 2:
            validation_results["is_valid"] = False
            validation_results["errors"].append("Country must be a 2-letter code")

        # Validate email format
        email = company_data.get("email")
        if email and "@" not in email:
            validation_results["is_valid"] = False
            validation_results["errors"].append("Invalid email format")

        # Validate domain format
        domain = company_data.get("domain")
        if domain and "." not in domain:
            validation_results["is_valid"] = False
            validation_results["errors"].append("Invalid domain format")

        # Warnings
        if not email and not domain:
            validation_results["warnings"].append("No contact information available")

        return validation_results


# Global service instance
company_resolution_service = CompanyResolutionService()
