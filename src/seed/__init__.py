from .seed_admin import create_admin
from .seed_roles import insert_roles
from flask import current_app

def run_seeding():
    """Runs all seed functions based on config."""
    app = current_app._get_current_object()
    logger = app.logger
    config = app.config

    insert_roles() 
    logger.info("Roles seeded successfully.") 

    if config.get("SEED_ADMIN", False):
        create_admin()
        logger.info("Admin user created.")
