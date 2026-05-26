import argparse
import logging
import sys

from alembic.config import Config
from alembic import command

from app.core.database import SessionLocal
from app.core.redis import redis_client
from app.core.security import get_password_hash
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def migrate():
    """Runs database migrations using Alembic."""
    logger.info("Running database migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations completed successfully.")

def create_admin(username, email, password):
    """Creates a new superuser."""
    logger.info(f"Creating admin user: {username} ({email})")
    with SessionLocal() as db:
        user = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if user:
            logger.warning("User with this username or email already exists.")
            return
        
        new_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_superuser=True,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        logger.info("Admin user created successfully.")

def clear_cache():
    """Clears the Redis cache."""
    logger.info("Clearing Redis cache...")
    if redis_client:
        redis_client.flushdb()
        logger.info("Cache cleared successfully.")
    else:
        logger.error("Redis client not configured or connected.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Coworking App CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("migrate", help="Run database migrations")
    
    admin_parser = subparsers.add_parser("create-admin", help="Create an admin user")
    admin_parser.add_argument("--username", required=True, help="Admin username")
    admin_parser.add_argument("--email", required=True, help="Admin email")
    admin_parser.add_argument("--password", required=True, help="Admin password")

    subparsers.add_parser("clear-cache", help="Clear the Redis cache")

    args = parser.parse_args()

    if args.command == "migrate":
        migrate()
    elif args.command == "create-admin":
        create_admin(args.username, args.email, args.password)
    elif args.command == "clear-cache":
        clear_cache()

if __name__ == "__main__":
    main()