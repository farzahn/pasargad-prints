"""
Custom configuration loader for Pasargad Prints
This module ensures that the .env file is loaded from the project root directory.
"""

import os
from pathlib import Path
from decouple import Config, RepositoryEnv

# Get the backend directory (where this file is located)
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Get the project root directory (parent of backend)
PROJECT_ROOT = BACKEND_DIR.parent

# Path to the .env file in the project root
ENV_FILE_PATH = PROJECT_ROOT / '.env'

# Create a custom config instance that explicitly uses the root .env file
if ENV_FILE_PATH.exists():
    # Use RepositoryEnv to explicitly specify the .env file location
    config = Config(RepositoryEnv(str(ENV_FILE_PATH)))
else:
    # Fallback to default config if .env doesn't exist
    # This will use environment variables
    from decouple import config as default_config
    config = default_config

# Export the config instance
__all__ = ['config', 'BACKEND_DIR', 'PROJECT_ROOT', 'ENV_FILE_PATH']