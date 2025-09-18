
# --- Config loading, type check, and logging setup helpers ---
import os
import yaml
import logging
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, cast
from string import Template
import schedule

# susi/config.py
"""
Centralized configuration constants and mappings for the Susi project.
"""

# Config keys
LOGGING_KEY = "logging"
LOG_FILE_KEY = "file"
LOG_LEVEL_KEY = "level"
TEMPLATE_KEY = "template"
AWS_KEY = "aws"
SCHEDULE_KEY = "schedule"
ONEDRIVE_KEY = "onedrive"
EMAIL_KEY = "email"
INSTAGRAM_KEY = "instagram"

# AWS subkeys
S3_BUCKET_KEY = "s3_bucket"
REGION_KEY = "region"
PROFILE_KEY = "profile"
ACCESS_KEY_ID = "access_key_id"
SECRET_ACCESS_KEY = "secret_access_key"
S3_URL_PREFIX_KEY = "s3_url_prefix"

# Schedule subkeys
IMAGE_DAY_KEY = "image_day"
IMAGE_TIME_KEY = "image_time"
INSTAGRAM_DAY_KEY = "instagram_day"
INSTAGRAM_TIME_KEY = "instagram_time"

# Logging format
LOG_FORMAT = (
    '%(asctime)s %(levelname)s %(name)s %(funcName)s:%(lineno)d %(message)s'
)

# Day map for scheduling
DAY_MAP = {
    'monday': schedule.every().monday,
    'tuesday': schedule.every().tuesday,
    'wednesday': schedule.every().wednesday,
    'thursday': schedule.every().thursday,
    'friday': schedule.every().friday,
    'saturday': schedule.every().saturday,
    'sunday': schedule.every().sunday,
}

GENAI_API_URL = os.getenv("LOCAL_GENAI_API_URL")

SYSTEM_PROMPT = (
    "You are a social media expert. Write an engaging Instagram post for the given target group, "
    "using the provided topic and news article summaries. The post should be concise, friendly, and suitable for Instagram. "
    "Do not mention that you are an AI or that you used news articles. Just create a natural, human-sounding post. "
    "Respond ONLY with the Instagram post text, no explanations, no reasoning, no <think> or system messages."
)

LINKEDIN_SYSTEM_PROMPT = (
    "You are a social media expert. Write a professional, engaging LinkedIn post for the given target group, "
    "using the provided topic and news article summaries. The post should be longer, more detailed, and suitable for LinkedIn. "
    "Do not mention that you are an AI or that you used news articles. Just create a natural, human-sounding post. "
    "Respond ONLY with the LinkedIn post text, no explanations, no reasoning, no <think> or system messages."
)


def resolve_env_vars(obj: Any) -> Any:
    """
    Recursively resolve environment variable references in a config object.
    Supports ${VAR} syntax in strings.
    """
    if isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(i) for i in obj]
    elif isinstance(obj, str):
        if obj.startswith('${') and obj.endswith('}'):  # full value is env var
            var = obj[2:-1]
            return os.getenv(var, obj)
        return Template(obj).safe_substitute(os.environ)
    else:
        return obj

def _assert_valid_config_types(obj, path="config"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            _assert_valid_config_types(v, f"{path}['{k}']")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _assert_valid_config_types(v, f"{path}[{i}]")
    elif not isinstance(obj, (str, int, float, bool, type(None))):
        raise TypeError(f"Invalid type in config at {path}: {type(obj)}")

def get_config() -> Dict[str, Any]:
    CONFIG_PATH = os.getenv("SUSI_CONFIG", "config.yaml")
    with open(CONFIG_PATH, 'r') as f:
        raw_config = yaml.safe_load(f)
        config: Dict[str, Any] = cast(Dict[str, Any], resolve_env_vars(raw_config))
    _assert_valid_config_types(config)
    return config

def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    LOG_FILE = config[LOGGING_KEY][LOG_FILE_KEY]
    # If the log file path is not absolute, use the default relative to project root
    if not os.path.isabs(LOG_FILE):
        LOG_FILE = os.path.join("04_implementation", "logs", LOG_FILE)
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    LOG_LEVEL = getattr(logging, config[LOGGING_KEY][LOG_LEVEL_KEY], logging.INFO)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2*1024*1024, backupCount=5)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.setLevel(LOG_LEVEL)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    console_handler.setLevel(LOG_LEVEL)
    logging.basicConfig(level=LOG_LEVEL, handlers=[file_handler, console_handler])
    logger = logging.getLogger("susi.main")
    return logger