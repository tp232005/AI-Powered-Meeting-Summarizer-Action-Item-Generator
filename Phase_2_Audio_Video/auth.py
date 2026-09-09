"""Local authentication and organization membership for the Phase 2 prototype."""
import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime


class AuthManager:
    """Manage users with salted scrypt password hashes."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _init_db(self):
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    organization_type TEXT NOT NULL DEFAULT 'Student Team',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    organization_id INTEGER NOT NULL REFERENCES organizations(id),
                    role TEXT NOT NULL DEFAULT 'Member',
                    created_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _hash_password(password: str) -> str:
        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters.")
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
        return f"scrypt${salt.hex()}${digest.hex()}"

    @staticmethod
    def _verify_password(password: str, encoded: str) -> bool:
        try:
            algorithm, salt_hex, digest_hex = encoded.split("$", 2)
            if algorithm != "scrypt":
                return False
            actual = hashlib.scrypt(
                password.encode("utf-8"), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1
            )
            return hmac.compare_digest(actual.hex(), digest_hex)
        except (ValueError, TypeError):
            return False

    def register(self, name: str, email: str, password: str, organization: str, organization_type: str = "Student Team") -> dict:
        name, email, organization = name.strip(), email.strip().lower(), organization.strip()
        if not name or not email or not organization:
            raise ValueError("Name, email, and organization are required.")
        password_hash = self._hash_password(password)
        now = datetime.now().isoformat()
        with self._connect() as connection:
            existing = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                raise ValueError("An account with that email already exists.")
            org = connection.execute("SELECT id FROM organizations WHERE name = ?", (organization,)).fetchone()
            if org:
                organization_id = org["id"]
                role = "Member"
            else:
                organization_id = connection.execute(
                    "INSERT INTO organizations(name, organization_type, created_at) VALUES (?, ?, ?)",
                    (organization, organization_type, now),
                ).lastrowid
                role = "Admin"
            user_id = connection.execute(
                """INSERT INTO users(name, email, password_hash, organization_id, role, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (name, email, password_hash, organization_id, role, now),
            ).lastrowid
        return self.get_user(user_id)

    def authenticate(self, email: str, password: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip().lower(),)
            ).fetchone()
        if not row or not self._verify_password(password, row["password_hash"]):
            return None
        return self._public_user(row)

    def get_user(self, user_id: int) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        return self._public_user(row) if row else None

    @staticmethod
    def _public_user(row) -> dict:
        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "organization_id": row["organization_id"],
            "role": row["role"],
            "created_at": row["created_at"],
        }
