from .seed_admin import create_admin
from .seed_roles import insert_roles
from .seed_metrics import insert_metrics
from .seed_aggregations import insert_aggregations
from flask import current_app

def run_seeding():
    """Runs all seed functions based on config."""
    app = current_app._get_current_object()
    logger = app.logger
    config = app.config

    insert_roles()
    logger.info("Roles seeded successfully.")

    insert_metrics()  
    logger.info("Metrics seeded successfully.")

    insert_aggregations()  
    logger.info("Aggregations seeded successfully.")

    if config.get("SEED_ADMIN", False):
        create_admin()
        logger.info("Admin user created.")
