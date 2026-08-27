from pathlib import Path


def schema_sql_path() -> Path:
    """Prefer the packaged schema, then the repository copy."""
    packaged = Path(__file__).resolve().parent / "schema.sql"
    if packaged.exists():
        return packaged
    return Path(__file__).resolve().parents[2] / "supabase" / "schema.sql"
