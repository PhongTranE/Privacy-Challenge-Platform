from flask import Flask
from src.commands.create_admin import createadmin
from src.commands.seed import seed

def register_commands(app: Flask):
    """Registers all Flask CLI commands."""
    app.cli.add_command(createadmin)
    app.cli.add_command(seed)