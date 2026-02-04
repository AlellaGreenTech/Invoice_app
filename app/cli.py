"""Flask CLI commands for database management."""
import click
from flask import current_app
from app.extensions import db
from app.models import Category


def register_commands(app):
    """Register CLI commands with the Flask app."""

    @app.cli.command('seed-categories')
    def seed_categories():
        """Seed default invoice categories."""
        from app.invoices.categorizer import InvoiceCategorizer

        categories = InvoiceCategorizer.get_default_categories()

        for category_name in categories:
            # Check if category already exists
            existing = Category.query.filter_by(name=category_name).first()
            if not existing:
                category = Category(
                    name=category_name,
                    description=f'Default category: {category_name}',
                    is_default=True
                )
                db.session.add(category)
                click.echo(f'Created category: {category_name}')
            else:
                click.echo(f'Category already exists: {category_name}')

        db.session.commit()
        click.echo('✓ Default categories seeded successfully')

    @app.cli.command('init-db')
    def init_db():
        """Initialize the database."""
        db.create_all()
        click.echo('✓ Database initialized')

    @app.cli.command('drop-db')
    @click.confirmation_option(prompt='Are you sure you want to drop all tables?')
    def drop_db():
        """Drop all database tables."""
        db.drop_all()
        click.echo('✓ Database tables dropped')

    @app.cli.command('reset-db')
    @click.confirmation_option(prompt='Are you sure you want to reset the database?')
    def reset_db():
        """Reset the database (drop and recreate)."""
        db.drop_all()
        db.create_all()
        click.echo('✓ Database reset successfully')
