import click
from flask import current_app
from src.seed import run_seeding

@click.command("seed")
def seed():
    """Seeds the database with initial data (roles, admin users, etc.)."""
    app = current_app._get_current_object()
    logger = app.logger
    
    with app.app_context():
        logger.info("Starting database seeding...")
        try:
            run_seeding()
            click.echo("Database seeding completed.")        
            logger.info("Seeding completed successfully.")
        except Exception as e:
            click.echo(f"Sedding failed: {e}")
            logger.error(f"Seeding failed: {e}")
