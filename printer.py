
import logging
import dotenv
import os


DEBUG = bool(os.getenv("DEBUG")) or False
DEBUG = True

# Create a logger
logger = logging.getLogger("AtoZBot")
logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Create console handler (optional)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)  # Show only INFO and above in console
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)