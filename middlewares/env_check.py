import os
import logging

logger = logging.getLogger(__name__)

class EnvCheckMiddleware:
    """A simple class to check for mandatory environment variables on startup."""
    
    @staticmethod
    def check_env_vars() -> None:
        """Checks for BOT_TOKEN and ADMINS. Exits if not found."""
        bot_token = os.getenv("BOT_TOKEN")
        admins = os.getenv("ADMINS")

        if not bot_token:
            logger.critical("FATAL: BOT_TOKEN is not set in the environment variables!")
            raise ValueError("BOT_TOKEN must be set.")

        if not admins:
            logger.warning("WARNING: ADMINS environment variable is not set. Admin commands will not be available.")
