from dotenv import load_dotenv
import os

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

TEST_TOKEN = os.getenv("TEST_TOKEN")

KOAT_API_BASE = "https://apiv1.koat.ai"
KOAT_API_KEY = os.getenv("KOAT_API_KEY")

TAAPI_SECRET = os.getenv("TAAPI_SECRET")

DEXANI_URL = "https://app.dexani.io/api/wise"
# secret doesn't exist, but I'm sure we will need a key in the future?
DEXANI_HEADERS = {
    "Content-Type": "application/json",
    "Accept-Encoding": "application/json",
}

TAAPI_URL = "https://api.taapi.io"
TAAPI_HEADERS = {
    "Content-Type": "application/json",
    "Accept-Encoding": "application/json",
}

ONE_HOUR = 60 * 60
TWELVE_HOURS = ONE_HOUR * 12
ONE_DAY = ONE_HOUR * 24
