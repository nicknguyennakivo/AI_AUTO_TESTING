from dataclasses import dataclass
import os
from dotenv import load_dotenv
import logging



basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, "../.env"))


@dataclass
class Config:
    VERSION: str = "0.0.1"
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    PORT: int = int(os.getenv("PORT", "7878"))
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    APP_NAME: str = os.getenv("APP_NAME", "QA_TESTS")
    LOGGER_TYPE: str = os.getenv("LOGGER_TYPE", "console")
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
