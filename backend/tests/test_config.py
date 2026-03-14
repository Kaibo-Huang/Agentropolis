"""
Tests for src/config.py — Settings loading and database_url computation.
"""

import pytest
from unittest.mock import patch

from src.config import Settings


class TestDatabaseUrlConversion:
    """Settings.database_url converts a raw NEON_DB string to asyncpg format."""

    def _make_settings(self, neon_db: str) -> Settings:
        with patch.dict("os.environ", {"NEON_DB": neon_db}, clear=False):
            return Settings(NEON_DB=neon_db)

    def test_postgresql_scheme_replaced(self):
        s = self._make_settings("postgresql://user:pass@host/db")
        assert s.database_url.startswith("postgresql+asyncpg://")

    def test_postgres_shorthand_scheme_replaced(self):
        s = self._make_settings("postgres://user:pass@host/db")
        assert s.database_url.startswith("postgresql+asyncpg://")

    def test_sslmode_stripped(self):
        s = self._make_settings("postgresql://user:pass@host/db?sslmode=require")
        assert "sslmode" not in s.database_url

    def test_channel_binding_stripped(self):
        s = self._make_settings(
            "postgresql://user:pass@host/db?channel_binding=require"
        )
        assert "channel_binding" not in s.database_url

    def test_ssl_query_param_stripped(self):
        s = self._make_settings("postgresql://user:pass@host/db?ssl=true")
        assert "ssl=" not in s.database_url

    def test_non_ssl_query_params_preserved(self):
        s = self._make_settings(
            "postgresql://user:pass@host/db?application_name=agentropolis"
        )
        assert "application_name=agentropolis" in s.database_url

    def test_empty_neon_db_returns_empty_string(self):
        s = Settings(NEON_DB="")
        assert s.database_url == ""

    def test_combined_ssl_params_all_stripped(self):
        s = self._make_settings(
            "postgresql://user:pass@host/db?sslmode=require&channel_binding=require"
        )
        url = s.database_url
        assert "sslmode" not in url
        assert "channel_binding" not in url

    def test_credentials_preserved(self):
        s = self._make_settings("postgresql://alice:secret@myhost.neon.tech/mydb")
        assert "alice:secret@myhost.neon.tech/mydb" in s.database_url
