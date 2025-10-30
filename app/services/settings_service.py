"""Settings service for creating snapshots and managing app settings."""

from typing import Any

from sqlalchemy.orm import Session

from app.db import crud


def create_settings_snapshot(db: Session) -> dict[str, Any]:
    """Create a snapshot of current settings for historical tracking.

    This function extracts all current settings and worker profiles
    into a dictionary format suitable for storing in history records.

    Args:
        db: Database session

    Returns:
        Dictionary containing settings and worker profiles snapshot
    """
    try:
        app_settings = crud.get_app_settings(db)
        worker_profiles = crud.get_worker_profiles(db)

        # Build settings snapshot with defaults
        settings_data = {
            "profit_margin": app_settings.profit_margin if app_settings else 0.30,
            "waste_rate": app_settings.waste_rate if app_settings else 0.10,
            "material_density": (
                app_settings.material_density if app_settings else 1.166
            ),
            "material_price_per_gram": (
                app_settings.material_price_per_gram if app_settings else 0.01
            ),
            "mold_edge_length": app_settings.mold_edge_length if app_settings else 26.0,
            "mold_spacing": app_settings.mold_spacing if app_settings else 1.0,
            "base_molds_per_shift": (
                app_settings.base_molds_per_shift if app_settings else 120.0
            ),
            "working_days_per_month": (
                app_settings.working_days_per_month if app_settings else 26
            ),
            "shifts_per_day": app_settings.shifts_per_day if app_settings else 2,
            "needles_per_machine": (
                app_settings.needles_per_machine if app_settings else 18
            ),
            "setup_fee_per_color": (
                app_settings.setup_fee_per_color if app_settings else 20.0
            ),
            "base_setup_fee": app_settings.base_setup_fee if app_settings else 15.0,
            "coloring_fee_per_color_per_shift": (
                app_settings.coloring_fee_per_color_per_shift if app_settings else 5.0
            ),
            "other_salary_per_cell_shift": (
                app_settings.other_salary_per_cell_shift if app_settings else 50.0
            ),
            "rent_per_cell_shift": (
                app_settings.rent_per_cell_shift if app_settings else 40.0
            ),
            "electricity_fee_per_cell_shift": (
                app_settings.electricity_fee_per_cell_shift if app_settings else 60.0
            ),
            "color_output_map": app_settings.color_output_map if app_settings else None,
        }

        # Build worker profiles snapshot
        worker_profiles_data = [
            {
                "name": profile.name,
                "monthly_salary": profile.monthly_salary,
                "machines_operated": profile.machines_operated,
            }
            for profile in worker_profiles
        ]

        return {
            "settings": settings_data,
            "worker_profiles": worker_profiles_data,
        }

    except Exception:
        # Return empty snapshot if there's an error
        return {"settings": {}, "worker_profiles": []}


def get_settings_value(
    db: Session, setting_name: str, default_value: Any = None
) -> Any:
    """Get a specific setting value with fallback to default.

    Args:
        db: Database session
        setting_name: Name of the setting to retrieve
        default_value: Default value if setting not found

    Returns:
        Setting value or default
    """
    try:
        app_settings = crud.get_app_settings(db)
        if app_settings and hasattr(app_settings, setting_name):
            return getattr(app_settings, setting_name)
        return default_value
    except Exception:
        return default_value


def update_settings_batch(db: Session, settings_data: dict[str, Any]) -> bool:
    """Update multiple settings in a single transaction.

    Args:
        db: Database session
        settings_data: Dictionary of setting names and values

    Returns:
        True if successful, False otherwise
    """
    try:
        app_settings = crud.get_app_settings(db)
        if not app_settings:
            # Create new settings if none exist
            app_settings = crud.create_app_settings(db, settings_data)
        else:
            # Update existing settings
            for key, value in settings_data.items():
                if hasattr(app_settings, key):
                    setattr(app_settings, key, value)
            db.commit()
        return True
    except Exception:
        db.rollback()
        return False
