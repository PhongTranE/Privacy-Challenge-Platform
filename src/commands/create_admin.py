import click
from flask import current_app
from src.extensions import db
from src.models.user import UserModel
from src.modules.auth.models import RoleModel

@click.command("createadmin")
def createadmin():
    """Creates a new admin via Flask CLI."""

    app = current_app._get_current_object()
    
    with app.app_context():
        username = click.prompt("Enter admin username", default="admin")
        email = click.prompt("Enter admin email (optional)", default="", show_default=False) or None
        password = click.prompt("Enter password", hide_input=True, confirmation_prompt=True)

        # Check if the user already exists
        admin = db.session.execute(db.select(UserModel).where(UserModel.username == username)).scalars().first()
        if admin:
            click.echo("Admin user already exists.")
            return
        
        admin = UserModel(username=username, password=password, email=email)

        admin_role = db.session.execute(db.select(RoleModel).where(RoleModel.name == "Administrator")).scalars().first()
        if admin_role:
            admin.roles.append(admin_role)
        db.session.add(admin)
        db.session.commit()

        click.echo(f"Admin created: {username} (Email: {email or 'None'})")
