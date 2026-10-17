"""Interactive-stage probe uses ephemeral QA identities, never production accounts."""

import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from services.tests.test_api import ApiTests

ApiTests.setUpClass()
probe = ApiTests()
probe.setUp()
rows = []
try:
    cases = [
        ("A enterprise business list", "/api/v1/business_records", probe.token(), 200),
        (
            "A requesting B details",
            "/api/v1/business_records/QA/enterprise/b",
            probe.token(),
            404,
        ),
        (
            "A attempting B filter",
            "/api/v1/business_records?enterpriseId=B",
            probe.token(),
            200,
        ),
        (
            "Public map basic projection",
            "/api/v1/spatial_objects",
            probe.token("QA-PUBLIC"),
            200,
        ),
        (
            "Expired token",
            "/api/v1/session",
            probe.token(iat=probe.now - 600, exp=probe.now - 300),
            401,
        ),
    ]
    for name, path, token, expected in cases:
        status, data, _ = probe.request(path, token)
        if status != expected:
            raise RuntimeError("Probe failed: " + name)
        rows.append(
            {
                "scenario": name,
                "httpStatus": status,
                "expectedStatus": expected,
                "total": data.get("total"),
                "ids": [
                    item.get("id", item.get("businessId"))
                    for item in data.get("items", [])
                ],
                "error": data.get("error"),
            }
        )
    probe.policy["principals"][0]["enabled"] = False
    probe.write("policy.json", probe.policy)
    status, data, _ = probe.request("/api/v1/session")
    if status != 403:
        raise RuntimeError("Revocation probe failed")
    rows.append(
        {
            "scenario": "Server policy revocation",
            "httpStatus": status,
            "expectedStatus": 403,
            "error": data.get("error"),
        }
    )
    print(
        json.dumps(
            {
                "version": "0.1.0",
                "data": "SYNTHETIC QA ONLY",
                "usesRealLoopbackHTTP": True,
                "productionIdentityConnected": False,
                "checks": rows,
                "passed": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
finally:
    probe.tearDown()
