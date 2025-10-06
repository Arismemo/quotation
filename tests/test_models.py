"""Tests for database models."""

from sqlalchemy.orm import Session

from app.db.models import AppSettings, User, WorkerProfile


class TestModels:
    """Test database models."""

    def test_user_model(self, test_db_session: Session):
        """Test User model creation."""
        user = User(username="testuser", password_hash="hashed_password")
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"

    def test_app_settings_model(self, test_db_session: Session):
        """Test AppSettings model creation."""
        settings = AppSettings(
            profit_margin=0.30, waste_rate=0.10, material_density=1.166
        )
        test_db_session.add(settings)
        test_db_session.commit()
        test_db_session.refresh(settings)

        assert settings.id is not None
        assert settings.profit_margin == 0.30

    def test_worker_profile_model(self, test_db_session: Session):
        """Test WorkerProfile model creation."""
        profile = WorkerProfile(
            name="test_worker", monthly_salary=5000.0, machines_operated=2
        )
        test_db_session.add(profile)
        test_db_session.commit()
        test_db_session.refresh(profile)

        assert profile.id is not None
        assert profile.name == "test_worker"
        assert profile.monthly_salary == 5000.0
