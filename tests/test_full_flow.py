from __future__ import annotations

from datetime import date, timedelta

import pytest


@pytest.mark.asyncio
async def test_full_crm_flow(client):
    register_payload = {
        "email": "owner@example.com",
        "password": "StrongPass123",
        "name": "Alice Owner",
        "organization_name": "Acme Inc",
    }
    register_resp = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 200
    tokens = register_resp.json()

    auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    orgs_resp = await client.get("/api/v1/organizations/me", headers=auth_headers)
    assert orgs_resp.status_code == 200
    organizations = orgs_resp.json()
    assert organizations
    organization_id = organizations[0]["organization"]["id"]

    headers = {**auth_headers, "X-Organization-Id": str(organization_id)}

    contact_resp = await client.post(
        "/api/v1/contacts",
        json={"name": "John Doe", "email": "john@example.com", "phone": "+123"},
        headers=headers,
    )
    assert contact_resp.status_code == 201
    contact_id = contact_resp.json()["id"]

    deal_resp = await client.post(
        "/api/v1/deals",
        json={
            "contact_id": contact_id,
            "title": "Website redesign",
            "amount": 10000,
            "currency": "EUR",
        },
        headers=headers,
    )
    assert deal_resp.status_code == 201
    deal_id = deal_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/deals/{deal_id}",
        json={"stage": "proposal"},
        headers=headers,
    )
    assert patch_resp.status_code == 200

    patch_resp = await client.patch(
        f"/api/v1/deals/{deal_id}",
        json={"status": "won"},
        headers=headers,
    )
    assert patch_resp.status_code == 200

    due = (date.today() + timedelta(days=2)).isoformat()
    task_resp = await client.post(
        "/api/v1/tasks",
        json={
            "deal_id": deal_id,
            "title": "Call client",
            "description": "Discuss proposal",
            "due_date": due,
        },
        headers=headers,
    )
    assert task_resp.status_code == 201

    tasks_resp = await client.get("/api/v1/tasks", headers=headers)
    assert tasks_resp.status_code == 200
    assert len(tasks_resp.json()) == 1

    summary_resp = await client.get("/api/v1/analytics/deals/summary", headers=headers)
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["count_by_status"]["won"] == 1

    funnel_resp = await client.get("/api/v1/analytics/deals/funnel", headers=headers)
    assert funnel_resp.status_code == 200
    assert funnel_resp.json()["stages"]
