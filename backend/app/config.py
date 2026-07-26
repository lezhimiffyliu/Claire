"""Small config/secrets helper — reads values from environment variables."""
import os


def get_secret(name: str, default=None):
    """Return a secret/config value from the environment."""
    return os.environ.get(name, default)
