import os
from ravendb import DocumentStore
from dotenv import load_dotenv

load_dotenv()


RAVENDB_URL = os.getenv("RAVENDB_URL", "localhost:8888")
RAVENDB_DB = os.getenv("RAVENDB_DB")

store = DocumentStore([RAVENDB_URL], RAVENDB_DB)
store.initialize()


def get_store():
    return store.open_session()
