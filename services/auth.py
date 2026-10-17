"""Pinned RSA access-token verification and independently managed enterprise policy."""

import base64, json, re, time
from dataclasses import dataclass
from pathlib import Path
import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from .common import ApiError, fields, read_json, loads, text, integer, boolean, strings

PERMISSIONS = {"spatial:read", "business:read", "focus:read", "focus:track", "focus:feedback"}


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str
    permissions: frozenset
    enterprises: frozenset
    all_enterprises: bool
    public_spatial: bool
    policy_version: str

    def require(self, permission):
        if permission not in self.permissions:
            raise ApiError(403, "FORBIDDEN")

    def enterprise(self, enterprise):
        return bool(enterprise) and (
            self.all_enterprises or enterprise in self.enterprises
        )


class JwtVerifier:
    def __init__(self, config, base):
        fields(
            config,
            [
                "issuer",
                "audience",
                "jwksFile",
                "tenantClaim",
                "tenant",
                "format",
                "accessTokenClaim",
                "maxLifetimeSeconds",
            ],
            ["issuer", "audience", "jwksFile", "tenantClaim", "tenant"],
        )
        self.issuer = text(config["issuer"], 1024)
        self.audience = text(config["audience"], 256, True)
        if not self.issuer.startswith("https://"):
            raise ValueError("issuer must be pinned HTTPS identifier")
        self.tenant_claim = text(config["tenantClaim"], 128, True)
        self.tenant = text(config["tenant"], 128, True)
        self.keys_path = (base / text(config["jwksFile"], 4096)).resolve()
        self.format = config.get("format", "rfc9068")
        self.access_claim = config.get("accessTokenClaim")
        if self.format not in ("rfc9068", "legacy_access"):
            raise ValueError("unsupported token format")
        if self.format == "legacy_access":
            fields(self.access_claim, ["name", "value"], ["name", "value"])
            text(self.access_claim["name"], 128, True)
            text(self.access_claim["value"], 128, True)
        self.lifetime = integer(config.get("maxLifetimeSeconds", 3600), 60, 86400)
        self.public_keys()

    def public_keys(self):
        document = read_json(self.keys_path, 256 * 1024)
        fields(document, ["keys"], ["keys"])
        if (
            not isinstance(document["keys"], list)
            or not 1 <= len(document["keys"]) <= 32
        ):
            raise ValueError("invalid key set")
        result = {}
        for key in document["keys"]:
            fields(
                key,
                [
                    "kty",
                    "kid",
                    "alg",
                    "use",
                    "n",
                    "e",
                    "x5c",
                    "x5t",
                    "x5t#S256",
                    "key_ops",
                ],
                ["kty", "kid", "alg", "n", "e"],
            )
            kid = text(key["kid"], 128, True)
            if (
                kid in result
                or key["kty"] != "RSA"
                or key["alg"] != "RS256"
                or key.get("use", "sig") != "sig"
            ):
                raise ValueError("invalid public key")
            if "key_ops" in key and key["key_ops"] != ["verify"]:
                raise ValueError("invalid key operations")
            public = jwt.PyJWK.from_dict(key, algorithm="RS256").key
            if not isinstance(public, RSAPublicKey) or public.key_size < 2048:
                raise ValueError("weak or unsupported key")
            result[kid] = public
        return result

    def verify(self, token):
        try:
            if not isinstance(token, str) or len(token) > 16384:
                raise ValueError("invalid token size")
            parts = token.split(".")
            if len(parts) != 3 or any(
                not re.fullmatch(r"[A-Za-z0-9_-]+", part) for part in parts
            ):
                raise ValueError("invalid compact token")
            decode = lambda part: loads(
                base64.urlsafe_b64decode(part + "=" * ((-len(part)) % 4))
            )
            header = decode(parts[0])
            payload = decode(parts[1])
            fields(header, ["alg", "kid", "typ"], ["alg", "kid", "typ"])
            if (
                header["alg"] != "RS256"
                or not isinstance(payload, dict)
                or "nonce" in payload
            ):
                raise ValueError("invalid token profile")
            if self.format == "rfc9068":
                if header["typ"] not in ("at+jwt", "application/at+jwt"):
                    raise ValueError("access-token type required")
                text(payload.get("client_id"), 256, True)
                text(payload.get("jti"), 256, True)
            else:
                if (
                    header["typ"] != "JWT"
                    or payload.get(self.access_claim["name"])
                    != self.access_claim["value"]
                ):
                    raise ValueError("legacy access discriminator missing")
            for claim in ("iat", "exp"):
                if type(payload.get(claim)) is not int:
                    raise ValueError("numeric dates required")
            if "nbf" in payload and type(payload["nbf"]) is not int:
                raise ValueError("invalid not-before")
            if not 0 < payload["exp"] - payload["iat"] <= self.lifetime:
                raise ValueError("token lifetime invalid")
            key = self.public_keys().get(text(header["kid"], 128, True))
            if key is None:
                raise ValueError("unknown key")
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.audience,
                options={
                    "require": ["iss", "aud", "sub", "exp", "iat"],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                    "verify_iss": True,
                    "verify_aud": True,
                    "verify_sub": True,
                },
                leeway=0,
            )
            text(claims["sub"], 256, True)
            if claims.get(self.tenant_claim) != self.tenant:
                raise ValueError("wrong tenant")
            scope = claims.get("scope", "")
            if (
                not isinstance(scope, str)
                or len(scope) > 2048
                or re.search(r"[\x00-\x1f\x7f]", scope)
            ):
                raise ValueError("invalid scope")
            claims["_permissions"] = frozenset(scope.split()) & PERMISSIONS
            return claims
        except (ValueError, TypeError, KeyError, RecursionError, jwt.PyJWTError):
            raise ApiError(401, "UNAUTHENTICATED") from None
        except OSError:
            raise ApiError(503, "AUTH_CONFIGURATION_UNAVAILABLE") from None


class Policy:
    def __init__(self, path, tenant):
        self.path, self.tenant = Path(path), tenant
        self.document()

    def document(self):
        document = read_json(self.path, 1024 * 1024)
        fields(
            document,
            ["schema", "tenant", "version", "principals"],
            ["schema", "tenant", "version", "principals"],
        )
        if (
            document["schema"] != "xnby.api.policy.v1"
            or document["tenant"] != self.tenant
        ):
            raise ValueError("invalid policy scope")
        text(document["version"], 128, True)
        if (
            not isinstance(document["principals"], list)
            or len(document["principals"]) > 10000
        ):
            raise ValueError("invalid principals")
        principals = {}
        for item in document["principals"]:
            fields(
                item,
                [
                    "subject",
                    "enabled",
                    "permissions",
                    "enterprises",
                    "allEnterprises",
                    "publicSpatial",
                    "validFrom",
                    "validUntil",
                ],
                ["subject", "enabled", "permissions", "enterprises"],
            )
            subject = text(item["subject"], 256, True)
            if subject in principals:
                raise ValueError("duplicate subject")
            boolean(item["enabled"])
            permissions = strings(item["permissions"], len(PERMISSIONS))
            if not permissions <= PERMISSIONS:
                raise ValueError("unknown permission")
            strings(item["enterprises"], 1000)
            boolean(item.get("allEnterprises", False))
            boolean(item.get("publicSpatial", False))
            for key in ("validFrom", "validUntil"):
                if key in item:
                    integer(item[key], 0, 2**53 - 1)
            if (
                "validFrom" in item
                and "validUntil" in item
                and item["validFrom"] >= item["validUntil"]
            ):
                raise ValueError("invalid policy interval")
            principals[subject] = item
        return document["version"], principals

    def principal(self, claims):
        try:
            version, items = self.document()
        except (OSError, ValueError, TypeError):
            raise ApiError(503, "POLICY_UNAVAILABLE") from None
        item = items.get(claims["sub"])
        now = time.time()
        if (
            not item
            or not item["enabled"]
            or now < item.get("validFrom", 0)
            or now >= item.get("validUntil", float("inf"))
        ):
            raise ApiError(403, "FORBIDDEN")
        return Principal(
            claims["sub"],
            self.tenant,
            frozenset(item["permissions"]) & claims["_permissions"],
            frozenset(item["enterprises"]),
            item.get("allEnterprises", False),
            item.get("publicSpatial", False),
            version,
        )
