from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB as PG_JSONB

# Dialect-agnostic types
JSONB = JSON().with_variant(PG_JSONB(), "postgresql")

def ARRAY(item_type):
    """Return a type that is ARRAY in Postgres and Text/JSON in SQLite."""
    return JSON().with_variant(PG_ARRAY(item_type), "postgresql")
