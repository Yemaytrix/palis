"""
entra_auth.py — Microsoft Entra ID token verification for the Palis MCP server.
================================================================================
Implements the MCP SDK TokenVerifier protocol by validating JWT access tokens
issued by Microsoft Entra ID against the published JWKS (signature + issuer +
audience + scope). Wiring this into FastMCP via AuthSettings makes the server an
OAuth 2.0 Resource Server: the SDK then automatically serves RFC 9728 protected-
resource metadata and returns 401 + WWW-Authenticate, which is exactly what the
Microsoft 365 Agents Toolkit's fetch expects.

Required env vars (set before starting the server in authenticated mode):
    ENTRA_TENANT_ID         your Ngozai tenant GUID (single-tenant)
    ENTRA_CLIENT_ID         the Application (client) ID of the Palis MCP Server app reg
    ENTRA_APP_ID_URI        the Application ID URI, e.g. api://<client-id>
    PALIS_REQUIRE_AUTH      "true" to enforce auth (default false = open dev mode)

Standard-library + PyJWT(+cryptography) + urllib only; no extra installs needed
(cryptography and pyjwt arrived with the mcp package).
"""

import json
import os
import time
import urllib.request

import jwt  # PyJWT (installed as a dependency of mcp)
from jwt import PyJWKClient

from mcp.server.auth.provider import AccessToken, TokenVerifier

TENANT_ID = os.environ.get("ENTRA_TENANT_ID", "")
CLIENT_ID = os.environ.get("ENTRA_CLIENT_ID", "")
APP_ID_URI = os.environ.get("ENTRA_APP_ID_URI", "")  # api://<client-id>

# Entra (v2.0) endpoints for a single tenant.
_AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
_JWKS_URI = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

# Accept either the bare client id or the api:// URI as a valid audience — Entra
# may stamp either depending on how the token was requested. We check both.
_VALID_AUDIENCES = [a for a in (CLIENT_ID, APP_ID_URI) if a]

# v2.0 issuer; we accept both v2.0 and v1.0 issuer forms to be safe.
_VALID_ISSUERS = [
    f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
    f"https://sts.windows.net/{TENANT_ID}/",
]

# Cache the JWKS client (it caches signing keys internally).
_jwk_client = PyJWKClient(_JWKS_URI) if TENANT_ID else None


class EntraTokenVerifier(TokenVerifier):
    """Validates Microsoft Entra ID JWT access tokens."""

    async def verify_token(self, token: str) -> AccessToken | None:
        if not (_jwk_client and _VALID_AUDIENCES):
            # Misconfigured — fail closed (no token accepted).
            print("[auth] ERROR: Entra env vars not set; rejecting token.")
            return None
        try:
            signing_key = _jwk_client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=_VALID_AUDIENCES,   # PyJWT accepts a list; matches any
                options={"verify_iss": False},  # we check issuer manually below
            )
        except Exception as e:  # signature/expiry/audience failures land here
            print(f"[auth] token rejected: {type(e).__name__}: {e}")
            return None

        # Manual issuer check (tolerant of v1.0/v2.0 forms).
        iss = claims.get("iss", "")
        if iss not in _VALID_ISSUERS:
            print(f"[auth] token rejected: unexpected issuer {iss!r}")
            return None

        # Scope check: Entra puts delegated scopes in "scp" (space-delimited).
        scopes = claims.get("scp", "").split()
        if "access_as_user" not in scopes:
            print(f"[auth] token rejected: missing access_as_user scope; got {scopes}")
            return None

        # Valid. Return the AccessToken the SDK expects.
        return AccessToken(
            token=token,
            client_id=claims.get("appid") or claims.get("azp") or "unknown",
            scopes=scopes,
            expires_at=claims.get("exp"),
        )
