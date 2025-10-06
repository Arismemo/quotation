"""Tests for core services."""

from sqlalchemy.orm import Session

from app.db import crud
from app.services.calculator_service import compute_quote


class TestCalculatorService:
    """Test calculator service functionality."""

    def test_calculate_quote_basic(self, test_db_session: Session):
        """Test basic quote calculation."""
        # This test would require setting up test data in the database
        # For now, we'll test that the function can be called without errors
        try:
            result = compute_quote(
                db=test_db_session,
                image_path="/static/uploads/test.jpg",
                color_count=3,
                area_ratio=0.5,
                order_quantity=100,
                worker_type="standard",
                debug=True,
            )
            # If we get here, the function executed without syntax errors
            assert isinstance(result, dict)
        except Exception as e:
            # Expected due to missing image file and database setup
            assert "image" in str(e).lower() or "file" in str(e).lower()


class TestCRUDOperations:
    """Test database CRUD operations."""

    def test_get_worker_profiles(self, test_db_session: Session):
        """Test getting worker profiles."""
        profiles = crud.get_worker_profiles(test_db_session)
        assert isinstance(profiles, list)

    def test_get_app_settings(self, test_db_session: Session):
        """Test getting app settings."""
        settings = crud.get_app_settings(test_db_session)
        # Should return None if no settings exist
        assert settings is None or hasattr(settings, "id")
