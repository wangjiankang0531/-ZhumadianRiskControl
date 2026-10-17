"""Actual loopback HTTP tests with ephemeral keys and explicitly synthetic A/B data."""

import copy, http.client, json, tempfile, threading, time, unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from services.api import Service, Server
from services.data import fingerprint
from services.common import loads


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        now = int(time.time())
        self.now = now
        self.base = {
            "iss": "https://qa.identity.invalid",
            "aud": "xnby-api",
            "sub": "QA-A",
            "iat": now,
            "exp": now + 300,
            "tenant": "QA",
            "scope": "spatial:read business:read",
            "client_id": "qa-client",
            "jti": "test-only",
        }

        def feature(i, owner):
            result = {
                "id": i,
                "name": "TEST " + i,
                "type": "point",
                "positions": [[10, 20, 30]],
                "label": {"text": "PRIVATE LABEL"},
                "style": {"iconImage": "PRIVATE ICON"},
            }
            if owner:
                result["business"] = {
                    "sourceSystem": "QA",
                    "objectType": "enterprise",
                    "businessId": i,
                    "enterpriseId": owner,
                }
            return result

        self.layers = {
            "schema": "hongtu.landscape.layers.v1",
            "scene": "zhumadian",
            "coordinates": {
                "srs": "EPSG:32650",
                "unit": "metre",
                "axes": "east,north,up",
                "origin": [225319.5, 3648440.1, 30.9],
            },
            "layers": [
                {
                    "id": "PRIVATE-LAYER",
                    "name": "PRIVATE LAYER NAME",
                    "features": [
                        feature("a", "A"),
                        feature("b", "B"),
                        feature("public", None),
                        feature("unknown", None),
                    ],
                }
            ],
        }
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
        self.records = {
            "schema": "xnby.business.records.v1",
            "scene": "zhumadian",
            "exportedAt": stamp,
            "ttlHours": 24,
            "records": [
                {
                    "sourceSystem": "QA",
                    "objectType": "enterprise",
                    "businessId": i,
                    "enterpriseId": owner,
                    "name": "TEST " + i,
                    "updatedAt": stamp,
                    "attributes": [
                        {"label": "Private detail", "value": "SECRET-" + owner}
                    ],
                }
                for i, owner in [("a", "A"), ("b", "B")]
            ],
        }
        self.policy = {
            "schema": "xnby.api.policy.v1",
            "tenant": "QA",
            "version": "qa-1",
            "principals": [
                {
                    "subject": subject,
                    "enabled": True,
                    "permissions": ["spatial:read", "business:read"],
                    "enterprises": companies,
                    "publicSpatial": public,
                    "allEnterprises": all_e,
                }
                for subject, companies, public, all_e in [
                    ("QA-A", ["A"], True, False),
                    ("QA-B", ["B"], False, False),
                    ("QA-PUBLIC", [], True, False),
                    ("QA-ADMIN", [], False, True),
                ]
            ],
        }
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.key.public_key()))
        jwk.update(kid="qa-key", alg="RS256", use="sig")
        self.write("jwks.json", {"keys": [jwk]})
        self.write("layers.json", self.layers)
        self.write("business.json", self.records)
        self.write("policy.json", self.policy)
        self.config = {
            "schema": "xnby.api.config.v1",
            "jwt": {
                "issuer": self.base["iss"],
                "audience": "xnby-api",
                "jwksFile": "jwks.json",
                "tenantClaim": "tenant",
                "tenant": "QA",
            },
            "policyFile": "policy.json",
            "data": {
                "layers": "layers.json",
                "business": "business.json",
                "publicSpatialIds": ["public"],
            },
            "auditFile": "audit.jsonl",
        }
        self.write("config.json", self.config)
        self.service = Service(self.root / "config.json")
        self.server = Server(("127.0.0.1", 0), self.service)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def write(self, name, value):
        p = self.root / name
        temporary = p.with_suffix(".new")
        temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        temporary.replace(p)

    def token(self, subject="QA-A", headers=None, **changes):
        payload = self.base | {"sub": subject} | changes
        return jwt.encode(
            payload,
            self.key,
            algorithm="RS256",
            headers={"kid": "qa-key", "typ": "at+jwt"} | (headers or {}),
        )

    def request(self, path, token=True, method="GET", headers=None, body=None):
        h = (
            {}
            if token is None
            else {
                "Authorization": "Bearer " + (self.token() if token is True else token)
            }
        )
        h.update(headers or {})
        c = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            c.request(method, path, body=body, headers=h)
            r = c.getresponse()
            raw = r.read()
            return r.status, {} if not raw else json.loads(raw), dict(r.getheaders())
        finally:
            c.close()

    def test_health_and_headers(self):
        status, d, h = self.request("/api/v1/health", None)
        self.assertEqual(status, 200)
        self.assertEqual(d["version"], "0.3.0")
        self.assertEqual(h["Cache-Control"], "no-store")
        self.assertEqual(h["Vary"], "Authorization")
        self.assertNotIn(str(self.root), json.dumps(d))

    def test_session_uses_server_policy(self):
        status, d, _ = self.request(
            "/api/v1/session", self.token(enterprises=["B"], roles=["admin"])
        )
        self.assertEqual(status, 200)
        self.assertEqual(d["enterprises"], ["A"])
        self.assertFalse(d["allEnterprises"])

    def test_company_a_spatial(self):
        status, d, _ = self.request("/api/v1/spatial_objects")
        self.assertEqual(status, 200)
        self.assertEqual(d["total"], 2)
        self.assertEqual({i["id"] for i in d["items"]}, {"a", "public"})
        self.assertNotIn("PRIVATE", json.dumps(d))
        self.assertNotIn("b", [i["id"] for i in d["items"]])

    def test_company_b_spatial(self):
        status, d, _ = self.request("/api/v1/spatial_objects", self.token("QA-B"))
        self.assertEqual(status, 200)
        self.assertEqual([i["id"] for i in d["items"]], ["b"])

    def test_public_projection_redacts_reference(self):
        self.service.store.public = frozenset(["public", "b"])
        status, d, _ = self.request("/api/v1/spatial_objects", self.token("QA-PUBLIC"))
        self.assertEqual(status, 200)
        self.assertEqual(d["total"], 2)
        for i in d["items"]:
            self.assertEqual(i["access"], "public_basic")
            self.assertNotIn("business", i)
            self.assertNotIn("enterpriseId", i)
        self.assertNotIn("SECRET-B", json.dumps(d))
        self.assertNotIn("PRIVATE", json.dumps(d))

    def test_public_cannot_read_business(self):
        status, d, _ = self.request("/api/v1/business_records", self.token("QA-PUBLIC"))
        self.assertEqual(status, 200)
        self.assertEqual(d["total"], 0)
        self.assertEqual(
            self.request(
                "/api/v1/business_records/QA/enterprise/b", self.token("QA-PUBLIC")
            )[0],
            404,
        )

    def test_business_scope_and_direct_lookup(self):
        status, d, _ = self.request("/api/v1/business_records")
        self.assertEqual(status, 200)
        self.assertEqual(d["total"], 1)
        self.assertEqual(d["items"][0]["businessId"], "a")
        self.assertEqual(d["source"], "file_snapshot")
        self.assertEqual(d["items"][0]["state"], "ready")
        self.assertEqual(
            self.request("/api/v1/business_records/QA/enterprise/a")[0], 200
        )
        for record in ("b", "nonexistent"):
            status, d, _ = self.request(
                "/api/v1/business_records/QA/enterprise/" + record
            )
            self.assertEqual(status, 404)
            self.assertEqual(d["error"], "NOT_FOUND")

    def test_query_cannot_expand_scope(self):
        for route in ("spatial_objects", "business_records"):
            status, d, _ = self.request("/api/v1/" + route + "?enterpriseId=B")
            self.assertEqual(status, 200)
            self.assertEqual(d["total"], 0)

    def test_search_cannot_reveal_company_b(self):
        for route in ("spatial_objects", "business_records"):
            status, d, _ = self.request("/api/v1/" + route + "?search=TEST%20b")
            self.assertEqual(status, 200)
            self.assertEqual(d["total"], 0)

    def test_admin_explicit_server_grant(self):
        status, d, _ = self.request("/api/v1/business_records", self.token("QA-ADMIN"))
        self.assertEqual(status, 200)
        self.assertEqual(d["total"], 2)

    def test_pagination_counts_after_authorization(self):
        status, d, _ = self.request("/api/v1/spatial_objects?limit=1&offset=1")
        self.assertEqual(status, 200)
        self.assertEqual(d["total"], 2)
        self.assertEqual(len(d["items"]), 1)
        self.assertEqual(d["items"][0]["id"], "public")

    def test_scope_intersection(self):
        token = self.token(scope="spatial:read")
        status, d, _ = self.request("/api/v1/spatial_objects", token)
        self.assertEqual(status, 200)
        self.assertNotIn("business", d["items"][0])
        self.assertEqual(self.request("/api/v1/business_records", token)[0], 403)
        self.assertEqual(
            self.request("/api/v1/spatial_objects", self.token(scope="unrelated"))[0],
            403,
        )

    def test_policy_revocation_next_request(self):
        self.assertEqual(self.request("/api/v1/session")[0], 200)
        self.policy["principals"][0]["enabled"] = False
        self.write("policy.json", self.policy)
        self.assertEqual(self.request("/api/v1/session")[0], 403)

    def test_policy_company_change_next_request(self):
        self.policy["version"] = "qa-2"
        self.policy["principals"][0]["enterprises"] = ["B"]
        self.write("policy.json", self.policy)
        status, d, _ = self.request("/api/v1/business_records")
        self.assertEqual(status, 200)
        self.assertEqual([r["businessId"] for r in d["items"]], ["b"])

    def test_unknown_subject_denied(self):
        self.assertEqual(
            self.request("/api/v1/session", self.token("QA-UNKNOWN"))[0], 403
        )

    def test_policy_validity(self):
        for from_, until in [
            (self.now + 60, self.now + 120),
            (self.now - 120, self.now - 60),
        ]:
            self.policy["principals"][0].update(validFrom=from_, validUntil=until)
            self.write("policy.json", self.policy)
            self.assertEqual(self.request("/api/v1/session")[0], 403)

    def test_bad_policy_fails_closed(self):
        self.policy["principals"][0]["enterprises"] = [{"malformed": True}]
        self.write("policy.json", self.policy)
        status, d, _ = self.request("/api/v1/session")
        self.assertEqual(status, 503)
        self.assertEqual(d["error"], "POLICY_UNAVAILABLE")

    def test_missing_token(self):
        self.assertEqual(self.request("/api/v1/spatial_objects", None)[0], 401)

    def test_query_token_rejected(self):
        self.assertEqual(
            self.request("/api/v1/session?access_token=" + self.token(), None)[0], 401
        )

    def test_invalid_signature(self):
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        token = jwt.encode(
            self.base,
            other,
            algorithm="RS256",
            headers={"kid": "qa-key", "typ": "at+jwt"},
        )
        self.assertEqual(self.request("/api/v1/session", token)[0], 401)

    def test_hmac_algorithm_rejected(self):
        token = jwt.encode(
            self.base,
            "synthetic-key-for-algorithm-test-only-0000",
            algorithm="HS256",
            headers={"kid": "qa-key", "typ": "at+jwt"},
        )
        self.assertEqual(self.request("/api/v1/session", token)[0], 401)

    def test_id_token_rejected(self):
        self.assertEqual(
            self.request("/api/v1/session", self.token(headers={"typ": "JWT"}))[0], 401
        )

    def test_header_urls_rejected(self):
        self.assertEqual(
            self.request(
                "/api/v1/session",
                self.token(headers={"jku": "https://attacker.invalid/keys"}),
            )[0],
            401,
        )

    def test_unknown_key_rejected(self):
        self.assertEqual(
            self.request("/api/v1/session", self.token(headers={"kid": "missing"}))[0],
            401,
        )

    def test_expired_token(self):
        self.assertEqual(
            self.request(
                "/api/v1/session", self.token(iat=self.now - 600, exp=self.now - 300)
            )[0],
            401,
        )

    def test_future_token(self):
        self.assertEqual(
            self.request(
                "/api/v1/session", self.token(iat=self.now + 300, exp=self.now + 600)
            )[0],
            401,
        )

    def test_lifetime_limit(self):
        self.assertEqual(
            self.request("/api/v1/session", self.token(exp=self.now + 7200))[0], 401
        )

    def test_bad_identity_claims(self):
        for changes in (
            {"iss": "https://other.invalid"},
            {"aud": "other"},
            {"tenant": "OTHER"},
            {"exp": str(self.now + 300)},
            {"nonce": "id-token-profile"},
            {"sub": ""},
            {"client_id": None},
            {"jti": None},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(
                    self.request("/api/v1/session", self.token(**changes))[0], 401
                )

    def test_duplicate_authorization(self):
        c = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        c.putrequest("GET", "/api/v1/session")
        c.putheader("Authorization", "Bearer " + self.token())
        c.putheader("Authorization", "Bearer " + self.token())
        c.endheaders()
        r = c.getresponse()
        self.assertEqual(r.status, 401)
        r.read()
        c.close()

    def test_raw_source_routes_absent(self):
        for path in (
            "/layers/default.json",
            "/business/default.json",
            "/spatial/default.json",
            "/../business.json",
            "/api/v1/../business.json",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)

    def test_bad_query(self):
        for query in (
            "limit=201",
            "limit=0",
            "offset=10001",
            "limit=1&limit=2",
            "file=business.json",
            "topic=invalid",
            "category=invalid",
            "search=%ZZ",
            "search=%FF",
            "enterpriseId=",
        ):
            with self.subTest(query=query):
                self.assertEqual(
                    self.request("/api/v1/spatial_objects?" + query)[0], 400
                )

    def test_read_only_and_head(self):
        for method in ("POST", "DELETE", "PUT", "PATCH", "OPTIONS"):
            self.assertEqual(self.request("/api/v1/session", method=method)[0], 405)
        status, d, h = self.request("/api/v1/session", method="HEAD")
        self.assertEqual(status, 200)
        self.assertEqual(d, {})
        self.assertGreater(int(h["Content-Length"]), 0)
        self.assertEqual(self.request("/api/v1/session", body="payload")[0], 400)

    def test_missing_business_source_explicit(self):
        del self.service.store.paths["business"]
        status, d, _ = self.request("/api/v1/business_records")
        self.assertEqual(status, 503)
        self.assertEqual(d["error"], "BUSINESS_SOURCE_NOT_CONFIGURED")

    def test_record_without_owner_never_inherits_layer_owner(self):
        del self.records["records"][0]["enterpriseId"]
        self.write("business.json", self.records)
        status, d, _ = self.request("/api/v1/spatial_objects")
        self.assertEqual(status, 200)
        self.assertEqual([r["id"] for r in d["items"]], ["public"])

    def test_enterprise_conflict_fails_closed(self):
        self.records["records"][0]["enterpriseId"] = "B"
        self.write("business.json", self.records)
        self.assertEqual(self.request("/api/v1/business_records")[0], 503)
        self.assertEqual(self.request("/api/v1/spatial_objects")[0], 503)

    def test_catalog_and_topic_query(self):
        d = {
            "schema": "xnby.spatial.catalog.v1",
            "scene": "zhumadian",
            "exportedAt": self.records["exportedAt"],
            "layerFingerprint": fingerprint(self.layers),
            "objects": [
                {"spatialId": "a", "category": "energy-meter", "themes": ["energy"]}
            ],
        }
        self.write("spatial.json", d)
        self.service.store.paths["spatial"] = self.root / "spatial.json"
        status, result, _ = self.request(
            "/api/v1/spatial_objects?topic=energy&category=energy-meter"
        )
        self.assertEqual(status, 200)
        self.assertEqual([r["id"] for r in result["items"]], ["a"])
        d["layerFingerprint"] = "0" * 64
        self.write("spatial.json", d)
        self.assertEqual(self.request("/api/v1/spatial_objects")[0], 503)

    def test_snapshot_stale_and_future(self):
        for age, state in [(90000, "stale"), (-600, "future")]:
            stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.now - age))
            self.records["exportedAt"] = stamp
            self.records["records"][0]["updatedAt"] = stamp
            self.write("business.json", self.records)
            status, d, _ = self.request("/api/v1/business_records")
            self.assertEqual(status, 200)
            self.assertEqual(d["items"][0]["state"], state)

    def test_duplicate_json_and_records(self):
        (self.root / "business.json").write_text(
            '{"schema":1,"schema":2}', encoding="utf-8"
        )
        self.assertEqual(self.request("/api/v1/business_records")[0], 503)
        self.records["records"].append(self.records["records"][0])
        self.write("business.json", self.records)
        self.assertEqual(self.request("/api/v1/business_records")[0], 503)

    def test_file_limits(self):
        with (self.root / "business.json").open("wb") as stream:
            stream.write(b" " * (8 * 1024 * 1024 + 1))
        self.assertEqual(self.request("/api/v1/business_records")[0], 503)

    def test_audit_no_token_or_business_values(self):
        token = self.token()
        self.request("/api/v1/business_records?search=SECRET-A", token)
        self.request("/api/v1/session", "malformed-token")
        raw = (self.root / "audit.jsonl").read_text("utf-8")
        self.assertNotIn(token, raw)
        self.assertNotIn("SECRET-A", raw)
        self.assertNotIn("malformed-token", raw)
        self.assertNotIn("search=", raw)
        self.assertIn("QA-A", raw)
        records = [json.loads(line) for line in raw.splitlines()]
        self.assertEqual(records[1]["status"], 401)
        self.assertNotIn("subject", records[1])

    def test_audit_failure_blocks_response(self):
        self.service.audit_file = self.root / "directory"
        self.service.audit_file.mkdir()
        status, d, _ = self.request("/api/v1/business_records")
        self.assertEqual(status, 503)
        self.assertEqual(d["error"], "AUDIT_UNAVAILABLE")
        self.assertNotIn("items", d)

    def test_missing_key_configuration_fails_closed(self):
        (self.root / "jwks.json").unlink()
        status, d, _ = self.request("/api/v1/session")
        self.assertEqual(status, 503)
        self.assertEqual(d["error"], "AUTH_CONFIGURATION_UNAVAILABLE")

    def test_fingerprint_matches_javascript_numbers_and_unicode_sort(self):
        document = json.loads(
            (Path(__file__).parent / "fingerprint_golden.json").read_text("utf-8")
        )
        self.assertEqual(
            fingerprint(document),
            "60bea1778686f10f935004fd202aacde62f8326d96b94329b607dc32d19687c9",
        )

    def test_json_duplicate_claims_rejected_before_signature(self):
        import base64

        encode = lambda raw: base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
        header = encode(b'{"alg":"RS256","kid":"qa-key","typ":"at+jwt"}')
        payload = encode((json.dumps(self.base)[:-1] + ',"sub":"QA-B"}').encode())
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        signature = encode(
            self.key.sign(
                (header + "." + payload).encode("ascii"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        )
        self.assertEqual(
            self.request("/api/v1/session", header + "." + payload + "." + signature)[
                0
            ],
            401,
        )

    def test_point_line_region_native_types(self):
        f = self.layers["layers"][0]["features"][0]
        for geometry, positions in [
            ("line", [[0, 0, 0], [1, 1, 0]]),
            ("region", [[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
        ]:
            f.update(type=geometry, positions=positions)
            self.write("layers.json", self.layers)
            status, d, _ = self.request("/api/v1/spatial_objects")
            self.assertEqual(status, 200)
            self.assertEqual(d["items"][0]["type"], geometry)
        f["type"] = "polygon"
        self.write("layers.json", self.layers)
        self.assertEqual(self.request("/api/v1/spatial_objects")[0], 503)

    def test_legacy_profile_requires_explicit_access_claim(self):
        verifier = self.service.jwt
        verifier.format = "legacy_access"
        verifier.access_claim = {"name": "token_use", "value": "access"}
        self.assertEqual(
            self.request(
                "/api/v1/session",
                self.token(headers={"typ": "JWT"}, token_use="access"),
            )[0],
            200,
        )
        self.assertEqual(
            self.request(
                "/api/v1/session", self.token(headers={"typ": "JWT"}, token_use="id")
            )[0],
            401,
        )

    def test_browser_metadata_and_dataset_revision(self):
        status, spatial, _ = self.request("/api/v1/spatial_objects")
        self.assertEqual(status, 200)
        status, business, _ = self.request("/api/v1/business_records")
        self.assertEqual(status, 200)
        self.assertEqual(spatial["datasetVersion"], business["datasetVersion"])
        self.assertEqual(spatial["policyVersion"], "qa-1")
        status, session, _ = self.request("/api/v1/session")
        self.assertEqual(status, 200)
        self.assertEqual(session["expiresAt"], self.base["exp"])
        self.records["records"][0]["attributes"][0]["value"] = "TEST CHANGED"
        self.write("business.json", self.records)
        changed = self.request("/api/v1/business_records")[1]
        self.assertNotEqual(changed["datasetVersion"], business["datasetVersion"])

    def test_authorized_style_and_label_preserved_public_projection_safe(self):
        feature = self.layers["layers"][0]["features"][0]
        feature["style"] = {
            "icon": "warning",
            "color": "#FF0000",
            "pattern": "dash",
            "widthPx": 8,
            "opacity": 0.5,
        }
        feature["label"] = {
            "visible": True,
            "text": "PRIVATE A LABEL",
            "fontPx": 16,
            "color": "#FFFFFF",
            "opacity": 0.8,
            "offset": [10, -20],
        }
        self.write("layers.json", self.layers)
        item = self.request("/api/v1/spatial_objects")[1]["items"][0]
        self.assertEqual(item["style"]["icon"], "warning")
        self.assertEqual(item["label"]["text"], "PRIVATE A LABEL")
        self.service.store.public = frozenset(["a"])
        result = self.request("/api/v1/spatial_objects", self.token("QA-PUBLIC"))[1]
        self.assertEqual(result["items"][0]["label"]["text"], "TEST a")
        self.assertNotIn("PRIVATE A LABEL", json.dumps(result))

    def test_invalid_authorized_style_rejected(self):
        self.layers["layers"][0]["features"][0]["style"] = {"opacity": 2}
        self.write("layers.json", self.layers)
        self.assertEqual(self.request("/api/v1/spatial_objects")[0], 503)

    def test_effective_authorization_revision_without_operator_version_change(self):
        first = self.request("/api/v1/session")[1]
        self.policy["principals"][0]["enterprises"] = ["B"]
        self.write("policy.json", self.policy)
        second = self.request("/api/v1/session")[1]
        self.assertEqual(first["policyVersion"], second["policyVersion"])
        self.assertNotEqual(
            first["authorizationVersion"], second["authorizationVersion"]
        )

    def test_native_group_visibility_and_name_preserved_when_fully_authorized(self):
        layer = self.layers["layers"][0]
        layer["features"] = [layer["features"][0]]
        layer["name"] = "A created group"
        layer["visible"] = False
        self.write("layers.json", self.layers)
        status, body, _ = self.request("/api/v1/spatial_objects", self.token())
        self.assertEqual(status, 200)
        item = body["items"][0]
        self.assertEqual(item["layer"]["name"], "A created group")
        self.assertFalse(item["layer"]["visible"])
        self.assertEqual(item["drawOrder"], 0)

    def test_mixed_layer_keeps_group_without_leaking_hidden_name_or_ordinals(self):
        status, body, _ = self.request("/api/v1/spatial_objects", self.token())
        self.assertEqual(status, 200)
        self.assertEqual([f["id"] for f in body["items"]], ["a", "public"])
        self.assertEqual([f["drawOrder"] for f in body["items"]], [0, 1])
        self.assertEqual(body["items"][0]["layer"], body["items"][1]["layer"])
        self.assertEqual(body["items"][0]["layer"]["name"], "授权图层 1")
        self.assertNotIn("PRIVATE", json.dumps(body))

    def test_fingerprint_invariants(self):
        original = fingerprint(self.layers)
        d = copy.deepcopy(self.layers)
        d["layers"].reverse()
        d["layers"][0]["features"].reverse()
        d["layers"][0]["features"][0]["name"] = "Renamed"
        self.assertEqual(original, fingerprint(d))
        d["layers"][0]["features"][0]["positions"][0][0] += 1
        self.assertNotEqual(original, fingerprint(d))


if __name__ == "__main__":
    unittest.main()
