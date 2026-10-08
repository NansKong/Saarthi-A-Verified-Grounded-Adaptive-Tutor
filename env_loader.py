"""Load local Pod C configuration without storing secrets in source code."""

from dotenv import load_dotenv

# The local .env is the project's source of truth. This also replaces stale
# keys exported earlier in the same PowerShell session.
load_dotenv(override=True)
