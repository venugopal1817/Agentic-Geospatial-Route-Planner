"""
Tests for Validation Agent and Validator Service.
"""

import pytest
from app.services.validator import VillageValidator, ValidationResult, validate_village_batch_for_routing
from app.agents.validation_agent import ValidationAgent, run_validation_agent


class TestVillageValidator:
    """Test the pure validation logic"""
    
    def test_valid_coordinates(self):
        """Test that valid coordinates pass validation"""
        result = VillageValidator.validate_single_village(
            name="Balapur",
            canonical_name="Balapur OG",
            district="Ranga Reddy",
            subdistric="Saroornagar",
            latitude=17.3456,
            longitude=78.5678,
            use_osm=False
        )
        
        assert result.is_valid is True
        assert result.confidence_score >= 0.5
        assert result.validation_source == "exact"
    
    def test_invalid_latitude(self):
        """Test that invalid latitude is caught"""
        result = VillageValidator.validate_single_village(
            name="Balapur",
            canonical_name="Balapur OG",
            district="Ranga Reddy",
            subdistric="Saroornagar",
            latitude=91.0,  # Out of range
            longitude=78.5678,
            use_osm=False
        )
        
        assert result.is_valid is False
        assert result.confidence_score == 0.0
    
    def test_invalid_longitude(self):
        """Test that invalid longitude is caught"""
        result = VillageValidator.validate_single_village(
            name="Balapur",
            canonical_name="Balapur OG",
            district="Ranga Reddy",
            subdistric="Saroornagar",
            latitude=17.3456,
            longitude=181.0,  # Out of range
            use_osm=False
        )
        
        assert result.is_valid is False
        assert result.confidence_score == 0.0
    
    def test_missing_district_reduces_confidence(self):
        """Test that missing district reduces confidence score"""
        result = VillageValidator.validate_single_village(
            name="Balapur",
            canonical_name="Balapur OG",
            district="",  # Missing
            subdistric="Saroornagar",
            latitude=17.3456,
            longitude=78.5678,
            use_osm=False
        )
        
        assert result.is_valid is True  # Still valid, but lower confidence
        assert result.confidence_score < 1.0
        assert "district" in result.warnings[0].lower()
    
    def test_batch_validation(self):
        """Test validating multiple villages"""
        villages = [
            {
                "name": "Balapur",
                "canonical_name": "Balapur OG",
                "district": "Ranga Reddy",
                "subdistric": "Saroornagar",
                "latitude": 17.3456,
                "longitude": 78.5678
            },
            {
                "name": "Mallapur",
                "canonical_name": "Mallapur OG",
                "district": "Ranga Reddy",
                "subdistric": "Saroornagar",
                "latitude": 17.3412,
                "longitude": 78.5612
            }
        ]
        
        results = VillageValidator.validate_batch(villages, use_osm=False)
        
        assert len(results) == 2
        assert all(r.is_valid for r in results)
        assert all(r.confidence_score >= 0.5 for r in results)
    
    def test_validate_batch_for_routing(self):
        """Test high-level batch validation function"""
        villages = [
            {
                "name": "Balapur",
                "village": "Balapur OG",
                "district": "Ranga Reddy",
                "subdistric": "Saroornagar",
                "latitude": 17.3456,
                "longitude": 78.5678
            }
        ]
        
        result = validate_village_batch_for_routing(villages, use_osm_validation=False)
        
        assert "valid" in result
        assert "warnings" in result
        assert "invalid" in result
        assert len(result["valid"]) >= 0


class TestValidationAgent:
    """Test the LangGraph Validation Agent"""
    
    def test_agent_initialization(self):
        """Test agent can be instantiated"""
        agent = ValidationAgent(use_osm=False)
        assert agent is not None
        assert agent.graph is not None
    
    def test_simple_validation_workflow(self):
        """Test end-to-end validation workflow"""
        agent = ValidationAgent(use_osm=False)
        
        matched_villages = [
            {
                "name": "Balapur",
                "village": "Balapur OG",
                "canonical_name": "Balapur OG",
                "district": "Ranga Reddy",
                "subdistric": "Saroornagar",
                "latitude": 17.3456,
                "longitude": 78.5678
            },
            {
                "name": "Mallapur",
                "village": "Mallapur OG",
                "canonical_name": "Mallapur OG",
                "district": "Ranga Reddy",
                "subdistric": "Saroornagar",
                "latitude": 17.3412,
                "longitude": 78.5612
            }
        ]
        
        result = agent.validate(matched_villages, source_location="Hyderabad")
        
        assert result["status"] == "complete"
        assert len(result["validated_villages"]) >= 0
        assert isinstance(result["clarification_needed"], bool)
    
    def test_high_confidence_results(self):
        """Test workflow with high-confidence results (no clarification needed)"""
        agent = ValidationAgent(use_osm=False)
        
        matched_villages = [
            {
                "name": "Balapur",
                "village": "Balapur OG",
                "canonical_name": "Balapur OG",
                "district": "Ranga Reddy",
                "subdistric": "Saroornagar",
                "latitude": 17.3456,
                "longitude": 78.5678
            }
        ]
        
        result = agent.validate(matched_villages, source_location="Hyderabad")
        
        # With good data, should not need clarification
        assert result["status"] == "complete"
        assert len(result["validated_villages"]) > 0
    
    def test_convenience_function(self):
        """Test the convenience function for quick validation"""
        matched_villages = [
            {
                "name": "Balapur",
                "village": "Balapur OG",
                "canonical_name": "Balapur OG",
                "district": "Ranga Reddy",
                "subdistric": "Saroornagar",
                "latitude": 17.3456,
                "longitude": 78.5678
            }
        ]
        
        result = run_validation_agent(matched_villages, source_location="Hyderabad")
        
        assert result["status"] == "complete"
        assert isinstance(result["validated_villages"], list)
    
    def test_validation_preserves_coordinates(self):
        """Test that validation preserves coordinate accuracy"""
        agent = ValidationAgent(use_osm=False)
        
        lat, lon = 17.3456, 78.5678
        
        matched_villages = [
            {
                "name": "Balapur",
                "village": "Balapur OG",
                "canonical_name": "Balapur OG",
                "district": "Ranga Reddy",
                "subdistric": "Saroornagar",
                "latitude": lat,
                "longitude": lon
            }
        ]
        
        result = agent.validate(matched_villages)
        
        assert len(result["validated_villages"]) > 0
        validated = result["validated_villages"][0]
        assert validated["latitude"] == lat
        assert validated["longitude"] == lon


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
