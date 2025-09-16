"""Deduplication utilities for tender data."""

import hashlib
import re
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger


class TenderDeduplicator:
    """Deduplication service for tender data."""
    
    def __init__(self):
        self.logger = logger.bind(service="deduplicator")
    
    def find_duplicates(
        self, 
        tenders: List[Dict], 
        similarity_threshold: float = 0.8
    ) -> List[Tuple[Dict, Dict, float]]:
        """Find duplicate tenders based on similarity."""
        duplicates = []
        
        for i, tender1 in enumerate(tenders):
            for j, tender2 in enumerate(tenders[i + 1:], i + 1):
                similarity = self._calculate_similarity(tender1, tender2)
                
                if similarity >= similarity_threshold:
                    duplicates.append((tender1, tender2, similarity))
                    self.logger.debug(
                        f"Found duplicate: {tender1.get('tender_ref')} <-> {tender2.get('tender_ref')} "
                        f"(similarity: {similarity:.2f})"
                    )
        
        return duplicates
    
    def _calculate_similarity(self, tender1: Dict, tender2: Dict) -> float:
        """Calculate similarity score between two tenders."""
        scores = []
        
        # Title similarity (weight: 0.4)
        title_sim = self._text_similarity(
            tender1.get("title", ""),
            tender2.get("title", "")
        )
        scores.append(("title", title_sim, 0.4))
        
        # Buyer similarity (weight: 0.3)
        buyer_sim = self._text_similarity(
            tender1.get("buyer_name", ""),
            tender2.get("buyer_name", "")
        )
        scores.append(("buyer", buyer_sim, 0.3))
        
        # CPV codes similarity (weight: 0.2)
        cpv_sim = self._cpv_similarity(
            tender1.get("cpv_codes", []),
            tender2.get("cpv_codes", [])
        )
        scores.append(("cpv", cpv_sim, 0.2))
        
        # Value similarity (weight: 0.1)
        value_sim = self._value_similarity(
            tender1.get("value_amount"),
            tender2.get("value_amount")
        )
        scores.append(("value", value_sim, 0.1))
        
        # Calculate weighted average
        total_weight = sum(weight for _, _, weight in scores)
        weighted_sum = sum(score * weight for _, score, weight in scores)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using multiple methods."""
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        if norm1 == norm2:
            return 1.0
        
        # Jaccard similarity on words
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        jaccard = intersection / union if union > 0 else 0.0
        
        # Levenshtein distance similarity
        levenshtein = self._levenshtein_similarity(norm1, norm2)
        
        # Combine both methods
        return (jaccard + levenshtein) / 2
    
    def _cpv_similarity(self, cpv1: List[str], cpv2: List[str]) -> float:
        """Calculate CPV codes similarity."""
        if not cpv1 or not cpv2:
            return 0.0
        
        set1 = set(cpv1)
        set2 = set(cpv2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _value_similarity(self, value1: Optional[float], value2: Optional[float]) -> float:
        """Calculate value similarity."""
        if value1 is None or value2 is None:
            return 0.5  # Neutral score when one value is missing
        
        if value1 == 0 and value2 == 0:
            return 1.0
        
        if value1 == 0 or value2 == 0:
            return 0.0
        
        # Calculate relative difference
        diff = abs(value1 - value2)
        avg = (value1 + value2) / 2
        
        relative_diff = diff / avg if avg > 0 else 1.0
        
        # Convert to similarity (0-1 scale)
        return max(0.0, 1.0 - relative_diff)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and extra whitespace
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        
        return text.strip()
    
    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """Calculate Levenshtein distance similarity."""
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        # Calculate Levenshtein distance
        distance = self._levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        
        return 1.0 - (distance / max_len) if max_len > 0 else 0.0
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def generate_fingerprint(self, tender: Dict) -> str:
        """Generate a unique fingerprint for a tender."""
        # Create a normalized representation
        normalized = {
            "title": self._normalize_text(tender.get("title", "")),
            "buyer": self._normalize_text(tender.get("buyer_name", "")),
            "cpv": sorted(tender.get("cpv_codes", [])),
            "country": tender.get("buyer_country", "").upper(),
        }
        
        # Create hash
        fingerprint_str = str(sorted(normalized.items()))
        return hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    def group_by_fingerprint(self, tenders: List[Dict]) -> Dict[str, List[Dict]]:
        """Group tenders by their fingerprint."""
        groups = {}
        
        for tender in tenders:
            fingerprint = self.generate_fingerprint(tender)
            if fingerprint not in groups:
                groups[fingerprint] = []
            groups[fingerprint].append(tender)
        
        return groups
    
    def select_best_tender(self, tenders: List[Dict]) -> Dict:
        """Select the best tender from a group of duplicates."""
        if not tenders:
            return {}
        
        if len(tenders) == 1:
            return tenders[0]
        
        # Scoring criteria
        best_tender = None
        best_score = -1
        
        for tender in tenders:
            score = self._score_tender_quality(tender)
            
            if score > best_score:
                best_score = score
                best_tender = tender
        
        return best_tender or tenders[0]
    
    def _score_tender_quality(self, tender: Dict) -> float:
        """Score tender quality for selection."""
        score = 0.0
        
        # Title completeness (0-0.3)
        title = tender.get("title", "")
        if title and len(title.strip()) > 10:
            score += 0.3
        
        # Summary completeness (0-0.2)
        summary = tender.get("summary", "")
        if summary and len(summary.strip()) > 20:
            score += 0.2
        
        # CPV codes presence (0-0.2)
        cpv_codes = tender.get("cpv_codes", [])
        if cpv_codes:
            score += 0.2
        
        # Buyer information (0-0.1)
        buyer_name = tender.get("buyer_name", "")
        if buyer_name:
            score += 0.1
        
        # Value information (0-0.1)
        value_amount = tender.get("value_amount")
        if value_amount and value_amount > 0:
            score += 0.1
        
        # URL presence (0-0.1)
        url = tender.get("url", "")
        if url:
            score += 0.1
        
        return score
    
    def deduplicate_tenders(self, tenders: List[Dict]) -> List[Dict]:
        """Remove duplicates from a list of tenders."""
        if not tenders:
            return []
        
        # Group by fingerprint
        groups = self.group_by_fingerprint(tenders)
        
        # Select best tender from each group
        deduplicated = []
        for group in groups.values():
            best_tender = self.select_best_tender(group)
            deduplicated.append(best_tender)
        
        self.logger.info(
            f"Deduplication: {len(tenders)} -> {len(deduplicated)} tenders "
            f"({len(tenders) - len(deduplicated)} duplicates removed)"
        )
        
        return deduplicated


# Global instance
deduplicator = TenderDeduplicator()
