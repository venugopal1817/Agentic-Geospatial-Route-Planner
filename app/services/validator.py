"""
Validation Service: Pure validation logic for village records.

Responsibilities:
- Verify village records against multiple sources
- Calculate confidence scores
- Handle fallback validation strategies
"""

import requests
import math
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validating a single village"""
    name: str
    canonical_name: str
    district: str
    subdistric: str
    latitude: float
    longitude: float
    is_valid: bool
    confidence_score: float  # 0-1
    validation_source: str  # "exact", "osm", "fallback"
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class VillageValidator:
    """
    Validates village records against multiple data sources.
    
    Strategy:
    1. Verify coordinates are in valid range (lat: -90 to 90, lon: -180 to 180)
    2. Cross-check with OpenStreetMap via Nominatim (if not in test mode)
    3. Return confidence score based on validation sources
    """
    
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    
    @staticmethod
    def _is_valid_coordinates(lat: float, lon: float) -> bool:
        """Check if coordinates are within valid geographic bounds."""
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate Euclidean distance between two coordinate pairs.
        For use in proximity validation.
        """
        return math.sqrt((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2)
    
    @classmethod
    def validate_single_village(
        cls,
        name: str,
        canonical_name: str,
        district: str,
        subdistric: str,
        latitude: float,
        longitude: float,
        use_osm: bool = False
    ) -> ValidationResult:
        """
        Validate a single village record.
        
        Args:
            name: Original input name
            canonical_name: Canonical village name from dataset
            district: District name
            subdistric: Subdistrict name
            latitude: Village latitude
            longitude: Village longitude
            use_osm: Whether to cross-check with OpenStreetMap (default: False for speed)
        
        Returns:
            ValidationResult with confidence score
        """
        warnings = []
        confidence_score = 1.0
        validation_source = "exact"
        
        # Step 1: Validate coordinates
        if not cls._is_valid_coordinates(latitude, longitude):
            return ValidationResult(
                name=name,
                canonical_name=canonical_name,
                district=district,
                subdistric=subdistric,
                latitude=latitude,
                longitude=longitude,
                is_valid=False,
                confidence_score=0.0,
                validation_source="invalid_coords",
                warnings=["Invalid geographic coordinates"]
            )
        
        # Step 2: Basic sanity checks
        if not canonical_name or canonical_name.strip() == "":
            warnings.append("Empty canonical name")
            confidence_score -= 0.3
        
        if not district or district.strip() == "":
            warnings.append("Empty district")
            confidence_score -= 0.2
        
        # Step 3: OpenStreetMap cross-check (optional, slower)
        if use_osm:
            osm_result = cls._check_nominatim(canonical_name, district)
            if osm_result:
                osm_lat, osm_lon = osm_result
                distance = cls._calculate_distance(latitude, longitude, osm_lat, osm_lon)
                
                # If coordinates are more than 0.1° apart (~10km), flag as warning
                if distance > 0.1:
                    warnings.append(f"Coordinates differ from OSM by {distance:.4f}°")
                    confidence_score -= 0.15
                
                validation_source = "osm"
            else:
                warnings.append("Not found in OpenStreetMap")
                confidence_score -= 0.1
        
        # Ensure score stays in [0, 1]
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        return ValidationResult(
            name=name,
            canonical_name=canonical_name,
            district=district,
            subdistric=subdistric,
            latitude=latitude,
            longitude=longitude,
            is_valid=confidence_score >= 0.5,
            confidence_score=confidence_score,
            validation_source=validation_source,
            warnings=warnings
        )
    
    @classmethod
    def validate_batch(
        cls,
        villages: List[Dict],
        use_osm: bool = False
    ) -> List[ValidationResult]:
        """
        Validate multiple villages.
        
        Args:
            villages: List of village dicts with keys: name, canonical_name, district, subdistric, latitude, longitude
            use_osm: Whether to cross-check with OpenStreetMap
        
        Returns:
            List of ValidationResult objects
        """
        results = []
        for village in villages:
            result = cls.validate_single_village(
                name=village.get("name", ""),
                canonical_name=village.get("canonical_name", village.get("village", "")),
                district=village.get("district", ""),
                subdistric=village.get("subdistric", ""),
                latitude=village.get("latitude", 0.0),
                longitude=village.get("longitude", 0.0),
                use_osm=use_osm
            )
            results.append(result)
        return results
    
    @staticmethod
    def _check_nominatim(village_name: str, district: str) -> Optional[tuple]:
        """
        Query OpenStreetMap Nominatim API for a village.
        
        Returns:
            Tuple of (latitude, longitude) if found, else None
        """
        try:
            query = f"{village_name}, {district}, India"
            response = requests.get(
                VillageValidator.NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "json",
                    "limit": 1
                },
                timeout=5
            )
            
            if response.status_code == 200 and response.json():
                result = response.json()[0]
                return (float(result["lat"]), float(result["lon"]))
        except (requests.RequestException, KeyError, ValueError, IndexError):
            pass
        
        return None


def validate_village_batch_for_routing(
    matched_villages: List[Dict],
    use_osm_validation: bool = False
) -> Dict:
    """
    High-level function: Validate a batch of matched villages for routing.
    
    Returns:
        {
            "valid": [ValidationResult, ...],
            "warnings": [ValidationResult, ...],
            "invalid": [ValidationResult, ...]
        }
    """
    validator = VillageValidator()
    results = validator.validate_batch(matched_villages, use_osm=use_osm_validation)
    
    return {
        "valid": [r for r in results if r.is_valid and r.confidence_score >= 0.8],
        "warnings": [r for r in results if r.is_valid and 0.5 <= r.confidence_score < 0.8],
        "invalid": [r for r in results if not r.is_valid]
    }
