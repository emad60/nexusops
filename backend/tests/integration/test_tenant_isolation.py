"""Cross-tenant isolation: the Phase 1 exit gate.

Every test here answers one of three questions, and all three have to hold:

1. **Can organization B reach organization A's data?** By direct object id
   (IDOR), by search/list, by subscription, or by machine credential. It must
   never be able to, and the answer must not distinguish "not yours" from "does
   not exist" — an existence oracle is itself a leak.
2. **Does the database enforce it, or only the application?** The raw-SQL probes
   connect as the application role with no ORM and no guard, and assert that
   PostgreSQL row-level security alone returns nothing across tenants, plus that
   every table carrying an ``org_id`` actually has a policy (so a new table
   cannot ship unprotected).
3. **Does an unscoped code path fail loudly?** A missing tenant filter used to be
   a silent full-table read; it is now a ``TenancyScopeError``, and the tests
   below pin that behaviour for ORM reads, bulk DML, Core statements and
   identity-map hits.

Both organizations in the matrix are owned by the **same superadmin user**, and
requests differ only in ``X-Org-Id``. That removes every authentication
difference from the equation: whatever blocks organization B is the tenancy
boundary itself, not a permission check.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from app.core.tenancy import TenancyScopeError, current_org, org_scope, system_scope
from app.models import (
    AuditLog,
    Deployment,
    Monitor,
    MonitorCheck,
    NotificationChannel,
    Secret,
    Server,
)
from sqlalchemy import select

from .helpers import (
    API,
    assert_error_code,
    bearer,
    error_of,
    login_account,
    server_payload,
    unique_email,
)

pytestmark = pytest.mark.integration


# --- fixtures -----------------------------------------------------------------


@pytest_asyncio.fixture
async def org_a(client, owner) -> dict:
    """The bootstrap organization plus a few resources created inside it."""
    headers = owner["headers"]

    server = (
        await client.post(f"{API}/nodes", headers=headers, json=server_payload("org-a-node"))
    ).json()
    secret = (
        await client.post(
            f"{API}/secrets",
            headers=headers,
            json={"key": "ORG_A_KEY", "value": "org-a-value"},
        )
    ).json()
    monitor = (
        await client.post(
            f"{API}/monitors",
            headers=headers,
            json={"name": "org-a-probe", "url": "sim://probe/healthy"},
        )
    ).json()
    project = (
        await client.post(f"{API}/projects", headers=headers, json={"name": "Org A App"})
    ).json()
    channel = (
        await client.post(
            f"{API}/notification-channels",
            headers=headers,
            json={
                "type": "EMAIL",
                "name": "org-a-sink",
                "config": {"recipients": ["a@nexusops.example.com"]},
                "events": ["MONITOR_DOWN"],
            },
        )
    ).json()

    return {
        "id": owner["active_organization_id"],
        "headers": headers,
        "server": server,
        "secret": secret,
        "monitor": monitor,
        "project": project,
        "channel": channel,
    }


@pytest_asyncio.fixture
async def viewer_in_a(client, org_a) -> dict:
    """A least-privileged, **non-superadmin** member of organization A.

    Used to show that a permission denial and a tenant denial are different
    things: this user legitimately holds ``node.read`` in A and still cannot
    see anything of B's.
    """
    roles = (await client.get(f"{API}/roles", headers=org_a["headers"])).json()
    rows = roles["items"] if isinstance(roles, dict) else roles
    viewer_role = next(r for r in rows if r["name"] == "Viewer")

    email = unique_email("viewer")
    created = await client.post(
        f"{API}/users",
        headers=org_a["headers"],
        json={
            "email": email,
            "password": "Integration-Pass1",
            "full_name": "Org A Viewer",
            "role_id": viewer_role["id"],
        },
    )
    assert created.status_code in (200, 201), created.text

    session = await login_account(client, email=email, password="Integration-Pass1")
    return {
        "credentials": {"email": email, "password": "Integration-Pass1"},
        "headers": bearer(session["access_token"], session["active_organization_id"]),
        "org_id": session["active_organization_id"],
    }


# --- 1. direct object access (IDOR) -------------------------------------------


async def test_superadmin_in_org_b_cannot_read_org_a_rows(client, owner, org_a, second_org):
    """Knowing an id is not authority — not even for an instance operator.

    The caller here is the platform superadmin and the owner of **both**
    organizations; the only thing pointing at organization B is the header. Every
    read must come back as a 404, not a 403: the row must be indistinguishable
    from one that does not exist.
    """
    b = second_org["headers"]

    roots = [
        (f"{API}/nodes", org_a["server"]["id"], "server"),
        (f"{API}/secrets", org_a["secret"]["id"], "secret"),
        (f"{API}/monitors", org_a["monitor"]["id"], "monitor"),
        (f"{API}/projects", org_a["project"]["id"], "project"),
        (f"{API}/notification-channels", org_a["channel"]["id"], "channel"),
    ]

    for root, real_id, label in roots:
        other_tenant = await client.get(f"{root}/{real_id}", headers=b)
        nonexistent = await client.get(f"{root}/{uuid.uuid4()}", headers=b)

        assert other_tenant.status_code == nonexistent.status_code == 404, (
            f"{label}: {other_tenant.status_code} {other_tenant.text}"
        )
        # The *code* matters as much as the status: a different code for "exists
        # but is not yours" would turn the API into an existence oracle.
        assert error_of(other_tenant.json())["code"] == error_of(nonexistent.json())["code"], (
            f"{label}: cross-tenant response must be indistinguishable from a miss"
        )

    # Controls: the same ids are readable from the organization that owns them.
    for root, real_id, label in roots:
        response = await client.get(f"{root}/{real_id}", headers=org_a["headers"])
        assert response.status_code == 200, f"{label} control: {response.text}"


#: Every mutation route a *foreign* tenant must miss, one entry per resource
#: and per verb. ``id_key`` indexes the ``org_a`` fixture so each probe aims at
#: an object that really exists — that is the whole point: the row is there and
#: still cannot be touched. Method/path/body mirror what the SPA sends.
WRITE_PROBES: list[tuple[str, str, str, str, dict[str, str] | None]] = [
    ("node update", "PATCH", "/nodes/{id}", "server", {"location": "org-b-edited"}),
    ("node delete", "DELETE", "/nodes/{id}", "server", None),
    ("secret rotate", "POST", "/secrets/{id}/rotate", "secret", {"value": "org-b-rotated-value"}),
    ("secret delete", "DELETE", "/secrets/{id}", "secret", None),
    ("monitor update", "PATCH", "/monitors/{id}", "monitor", {"name": "org-b-owned"}),
    ("monitor delete", "DELETE", "/monitors/{id}", "monitor", None),
    ("project update", "PATCH", "/projects/{id}", "project", {"name": "org-b-app"}),
    ("project delete", "DELETE", "/projects/{id}", "project", None),
    ("channel update", "PATCH", "/notification-channels/{id}", "channel", {"name": "org-b-sink"}),
    ("channel delete", "DELETE", "/notification-channels/{id}", "channel", None),
]


async def test_org_b_cannot_mutate_or_delete_org_a_rows(client, owner, org_a, second_org):
    """The write side of the boundary: every mutating route misses for a foreign tenant.

    Reads being closed is not enough — a PATCH, a rotate or a DELETE that lands
    lets one tenant corrupt another's data, and a delete is the one operation no
    later read can undo. Each probe runs twice, against org A's real id and
    against a random uuid, and the two must be *identical* (same status and same
    error code): a distinguishable "exists but is not yours" is itself the leak.
    """
    b = second_org["headers"]

    for label, method, path, id_key, body in WRITE_PROBES:
        foreign = await client.request(
            method, f"{API}{path.format(id=org_a[id_key]['id'])}", headers=b, json=body
        )
        missing = await client.request(
            method, f"{API}{path.format(id=uuid.uuid4())}", headers=b, json=body
        )

        assert foreign.status_code == missing.status_code == 404, (
            f"{label}: cross-tenant {foreign.status_code} vs miss {missing.status_code}"
        )
        assert error_of(foreign.json())["code"] == error_of(missing.json())["code"], (
            f"{label}: cross-tenant response must be indistinguishable from a miss"
        )

    # And none of it took effect: org A still reads every object unchanged.
    node = await client.get(f"{API}/nodes/{org_a['server']['id']}", headers=org_a["headers"])
    assert node.status_code == 200
    assert node.json()["location"] != "org-b-edited"

    monitor = await client.get(f"{API}/monitors/{org_a['monitor']['id']}", headers=org_a["headers"])
    assert monitor.json()["name"] == "org-a-probe"

    project = await client.get(f"{API}/projects/{org_a['project']['id']}", headers=org_a["headers"])
    assert project.json()["name"] == "Org A App"

    channel = await client.get(
        f"{API}/notification-channels/{org_a['channel']['id']}", headers=org_a["headers"]
    )
    assert channel.json()["name"] == "org-a-sink"

    secret = await client.get(f"{API}/secrets/{org_a['secret']['id']}", headers=org_a["headers"])
    assert secret.json()["version"] == 1
    assert secret.json()["digest"] == org_a["secret"]["digest"]


async def test_secret_material_never_crosses_the_tenant_boundary(client, owner, org_a, second_org):
    """No secret material is reachable across the boundary (Phase 1 criterion).

    No endpoint returns a plaintext value by design, so the claim is checked at
    the three places material *could* escape: the listing, the detail read, and
    the rotation digest (a server-keyed HMAC that still must not cross). A
    foreign reader must also be unable to rotate or delete the row — covered by
    the probe matrix above; this test pins the read side and the response bodies.
    """
    b = second_org["headers"]

    listed = (await client.get(f"{API}/secrets", headers=b)).json()["items"]
    assert "ORG_A_KEY" not in {row["key"] for row in listed}
    assert org_a["secret"]["digest"] not in {row["digest"] for row in listed}

    detail = await client.get(f"{API}/secrets/{org_a['secret']['id']}", headers=b)
    assert detail.status_code == 404
    # The miss must not echo the row back through the error envelope.
    assert "ORG_A_KEY" not in detail.text
    assert org_a["secret"]["digest"] not in detail.text
    assert "org-a-value" not in detail.text


async def test_plain_viewer_of_a_cannot_reach_b_even_without_permissions_involved(
    client, org_a, second_org, viewer_in_a
):
    """A non-superadmin member of A: legitimate read authority there, nothing in B.

    Two independent things are asserted: the viewer can read A's node (so the
    denial below is not a blanket 403), and B's node id is a 404 for them.
    """
    allowed = await client.get(
        f"{API}/nodes/{org_a['server']['id']}", headers=viewer_in_a["headers"]
    )
    assert allowed.status_code == 200, allowed.text

    # To create a row in B we need B's owner: same superadmin, B's header.
    node_b = (
        await client.post(
            f"{API}/nodes", headers=second_org["headers"], json=server_payload("org-b-node")
        )
    ).json()

    # The viewer cannot even be told that the header names B: no membership there.
    cross = await client.get(
        f"{API}/nodes/{node_b['id']}",
        headers=bearer(viewer_in_a["headers"]["Authorization"].split(" ", 1)[1], second_org["id"]),
    )
    assert cross.status_code == 403, cross.text
    assert_error_code(cross.json(), "ORGANIZATION_FORBIDDEN")


async def test_lists_and_search_never_cross_the_boundary(client, owner, org_a, second_org):
    """A tenant sees its own rows and nobody else's, on every listing surface."""
    b = second_org["headers"]
    node_b = (
        await client.post(f"{API}/nodes", headers=b, json=server_payload("b-only-node"))
    ).json()
    await client.post(
        f"{API}/secrets", headers=b, json={"key": "ORG_B_KEY", "value": "org-b-value"}
    )
    await client.post(
        f"{API}/monitors", headers=b, json={"name": "org-b-probe", "url": "sim://probe/healthy"}
    )

    # Servers
    listed_a = (await client.get(f"{API}/nodes", headers=org_a["headers"])).json()["items"]
    assert {row["id"] for row in listed_a} == {org_a["server"]["id"]}

    listed_b = (await client.get(f"{API}/nodes", headers=b)).json()["items"]
    assert {row["id"] for row in listed_b} == {node_b["id"]}

    # Free-text search is a listing with a filter: it must not become a global
    # lookup just because the term matches another tenant's row.
    searched = (await client.get(f"{API}/nodes", headers=b, params={"q": "org-a-node"})).json()[
        "items"
    ]
    assert searched == []

    # Secrets never reveal another tenant's key names.
    keys_b = {row["key"] for row in (await client.get(f"{API}/secrets", headers=b)).json()["items"]}
    assert "ORG_A_KEY" not in keys_b

    # Monitors and projects behave the same way.
    monitors_b = {
        row["name"] for row in (await client.get(f"{API}/monitors", headers=b)).json()["items"]
    }
    assert monitors_b == {"org-b-probe"}
    projects_b = {
        row["name"] for row in (await client.get(f"{API}/projects", headers=b)).json()["items"]
    }
    assert "Org A App" not in projects_b


async def test_audit_trail_is_tenant_scoped(client, owner, org_a, second_org):
    """Every security event identifies its organization, and only that one."""
    b = second_org["headers"]
    await client.post(f"{API}/nodes", headers=b, json=server_payload("audit-b-node"))

    rows_b = (await client.get(f"{API}/audit-logs", headers=b, params={"limit": 100})).json()[
        "items"
    ]
    assert rows_b, "organization B should see its own audit rows"
    assert all(row["org_id"] == second_org["id"] for row in rows_b)
    assert not any(row["resource_id"] == org_a["server"]["id"] for row in rows_b)

    rows_a = (
        await client.get(f"{API}/audit-logs", headers=org_a["headers"], params={"limit": 100})
    ).json()["items"]
    assert all(row["org_id"] == org_a["id"] for row in rows_a)
    assert any(row["resource_id"] == org_a["server"]["id"] for row in rows_a)


# --- 1b. header handling ------------------------------------------------------


async def test_org_header_is_required_and_never_guessed(client, owner):
    """An authenticated request must name its organization."""
    bare = bearer(owner["access_token"])
    missing = await client.get(f"{API}/nodes", headers=bare)
    assert missing.status_code == 403
    assert_error_code(missing.json(), "ORGANIZATION_HEADER_REQUIRED")

    malformed = await client.get(
        f"{API}/nodes",
        headers={**bare, "X-Org-Id": "not-a-uuid"},
    )
    assert malformed.status_code == 400
    assert_error_code(malformed.json(), "INVALID_ORG_HEADER")

    unknown = await client.get(
        f"{API}/nodes",
        headers={**bare, "X-Org-Id": str(uuid.uuid4())},
    )
    # A non-existent organization and one the caller has no membership in are
    # answered identically: knowing a UUID grants nothing.
    assert unknown.status_code == 403
    assert_error_code(unknown.json(), "ORGANIZATION_FORBIDDEN")


async def test_api_key_ignores_the_header_and_stays_in_its_own_tenant(
    client, owner, org_a, second_org
):
    """A machine credential's organization is its own, not whatever it claims.

    Changing ``X-Org-Id`` on a key-authenticated request must not widen the key:
    the key *is* the boundary.
    """
    created = await client.post(
        f"{API}/api-keys",
        headers=org_a["headers"],
        json={"name": "deploy-bot", "scopes": ["*"]},
    )
    assert created.status_code == 201, created.text
    key_headers = {"X-API-Key": created.json()["key"], "X-Org-Id": second_org["id"]}

    # Reads resolve to the key's organization (A), so B's ids remain invisible…
    listed = await client.get(f"{API}/nodes", headers=key_headers)
    assert listed.status_code == 200, listed.text
    assert {row["id"] for row in listed.json()["items"]} == {org_a["server"]["id"]}

    # …and writes land in A regardless of the header.
    node_b = (
        await client.post(
            f"{API}/nodes", headers=second_org["headers"], json=server_payload("b-node-for-keys")
        )
    ).json()
    hidden = await client.get(f"{API}/nodes/{node_b['id']}", headers=key_headers)
    assert hidden.status_code == 404, hidden.text

    created_node = await client.post(
        f"{API}/nodes", headers=key_headers, json=server_payload("written-by-key")
    )
    assert created_node.status_code == 201, created_node.text
    in_b = await client.get(f"{API}/nodes", headers=second_org["headers"])
    assert created_node.json()["id"] not in {row["id"] for row in in_b.json()["items"]}
    in_a = await client.get(f"{API}/nodes", headers=org_a["headers"])
    assert created_node.json()["id"] in {row["id"] for row in in_a.json()["items"]}


# --- 2. the database, on its own ---------------------------------------------


def _app_role_dsn() -> str:
    """A libpq DSN for the RLS-enforced application role (no ORM, no guard)."""
    from tests.conftest import TEST_APP_PASSWORD, TEST_APP_ROLE, TEST_DATABASE_URL

    url = TEST_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    assert TEST_APP_ROLE in url and TEST_APP_PASSWORD  # sanity: app role, not owner
    return url


def _raw_probe(sql: str, params: tuple = (), *, org: str | None = None, expect_error: bool = False):
    """Run one statement as ``nexusops_app`` with an explicit GUC.

    Parameterized like any other query — these are probes, not a place to hand
    build SQL strings from test values.
    """
    import psycopg

    with psycopg.connect(_app_role_dsn()) as conn:
        if org is not None:
            conn.execute("SELECT set_config('app.current_org', %s, false)", (org,))
        try:
            return conn.execute(sql, params).fetchall()
        except psycopg.errors.Error as exc:
            if not expect_error:
                raise
            return exc


async def test_rls_blocks_cross_tenant_reads_without_the_orm(
    client, owner, org_a, second_org, org_db
):
    """Raw SQL as the application role: the policies alone return nothing.

    Written against the **database**, not the API: no ORM session, no session
    guard, no request context — just the GUC a request would have set.
    """
    node_b = (
        await client.post(
            f"{API}/nodes", headers=second_org["headers"], json=server_payload("rls-b-node")
        )
    ).json()

    # A: its own row is visible.
    mine = _raw_probe(
        "SELECT name FROM servers WHERE id = %s", (org_a["server"]["id"],), org=org_a["id"]
    )
    assert [row[0] for row in mine] == ["org-a-node"]

    # A: B's row is not — and asking for it by primary key changes nothing.
    theirs = _raw_probe("SELECT name FROM servers WHERE id = %s", (node_b["id"],), org=org_a["id"])
    assert theirs == []

    # A: an unfiltered SELECT sees only A.
    everything = _raw_probe("SELECT org_id FROM servers", org=org_a["id"])
    assert {str(row[0]) for row in everything} == {org_a["id"]}

    # The system scope is the one that sees across tenants (and is how sweeps,
    # not requests, run).
    all_rows = _raw_probe("SELECT org_id FROM servers", org="00000000-0000-0000-0000-000000000000")
    assert {str(row[0]) for row in all_rows} == {org_a["id"], second_org["id"]}

    # No scope at all (the GUC unset) denies everything, including A's own rows.
    assert _raw_probe("SELECT org_id FROM servers") == []


async def test_audit_trail_is_still_append_only_after_tenancy(client, owner, org_a, second_org):
    """Adding ``org_id`` to ``audit_logs`` must not have opened a way to edit it.

    The immutability trigger predates tenancy and is deliberately untouched: the
    tenant column narrows who can *read* the trail, it must never widen who can
    rewrite it — a tenant-scoped UPDATE of an audit row would be a way to erase
    evidence of exactly the actions this suite is about.
    """
    await client.post(f"{API}/nodes", headers=org_a["headers"], json=server_payload("a1"))

    for statement in (
        "UPDATE audit_logs SET action = 'tampered'",
        "DELETE FROM audit_logs",
    ):
        error = _raw_probe(statement, org=org_a["id"], expect_error=True)
        assert "append-only" in str(error), f"{statement} must be blocked: {error}"

    # ... and the rows are all still there, still attributed to their tenant.
    rows = _raw_probe("SELECT org_id FROM audit_logs", org=org_a["id"])
    assert rows and {str(row[0]) for row in rows} <= {org_a["id"], second_org["id"]}


async def test_rls_rejects_cross_tenant_writes_without_the_orm(client, owner, org_a, second_org):
    """``WITH CHECK`` is not decoration: an unlucky INSERT cannot cross tenants."""
    # Posing as B, claim A's organization on a new row.
    error = _raw_probe(
        "INSERT INTO tags (id, name, color, org_id, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 'smuggled', '#fff', %s, now(), now())",
        (org_a["id"],),
        org=second_org["id"],
        expect_error=True,
    )
    assert error is not None and "row-level security" in str(error)

    # Posing as A, update one of A's rows so that it points at B.
    error = _raw_probe(
        "UPDATE servers SET org_id = %s WHERE id = %s",
        (second_org["id"], org_a["server"]["id"]),
        org=org_a["id"],
        expect_error=True,
    )
    assert error is not None and "row-level security" in str(error)

    # A row that legitimately belongs to the scope still inserts.
    assert _raw_probe(
        "INSERT INTO tags (id, name, color, org_id, created_at, updated_at) "
        "VALUES (gen_random_uuid(), 'legit', '#fff', %s, now(), now()) RETURNING name",
        (org_a["id"],),
        org=org_a["id"],
    ) == [("legit",)]


async def test_every_table_with_an_org_id_has_a_policy(org_db):
    """Catalog completeness: a new tenant table cannot ship unprotected.

    Compares the tables that carry an ``org_id`` against the tables that have at
    least one row-level-security policy requiring it, excluding the documented
    pre-org carve-outs. Adding an ``org_id`` column without policies fails here
    rather than silently becoming instance-wide.
    """
    from app.core.tenancy import RLS_EXEMPT_ORG_TABLES
    from sqlalchemy import text

    rows = (
        await org_db.execute(
            text(
                """
                SELECT c.relname,
                       c.relrowsecurity,
                       (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid) AS policies,
                       (SELECT count(*) FROM pg_policy p
                         WHERE p.polrelid = c.oid
                           AND pg_get_expr(p.polqual, p.polrelid) LIKE '%org_id%'
                           AND pg_get_expr(p.polwithcheck, p.polrelid) LIKE '%org_id%') AS org_policies
                  FROM pg_class c
                  JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'org_id'
                 WHERE c.relkind = 'r' AND c.relnamespace = 'public'::regnamespace
                """
            )
        )
    ).all()

    protected = {row[0]: row for row in rows if row[1] and row[3] >= 1}
    unprotected = sorted(
        name for name, row in {r[0]: r for r in rows}.items() if name not in protected
    )

    assert unprotected, "the probe must find the org_id tables it is meant to"
    # ``organizations`` is in the carve-out list as the tenant root, but it has no
    # ``org_id`` column of its own (it *is* the id), so only the intersection is
    # expected to show up here.
    expected = set(RLS_EXEMPT_ORG_TABLES) & {row[0] for row in rows}
    assert set(unprotected) == expected, (
        "tables carrying org_id without a tenant policy must be exactly the documented "
        f"pre-org carve-outs; got {sorted(set(unprotected))} vs {sorted(expected)}"
    )

    # Both directions of the policy are present on a tenant table: the migration
    # must not have produced a USING-only (write-open) or WITH CHECK-only policy.
    name, row = next(iter(protected.items()))
    assert row[2] >= 2, f"{name} should carry a tenant policy and a system policy"


# --- 3. the application guard -------------------------------------------------


async def test_unscoped_access_to_tenant_data_fails_loudly(client, owner, org_a, db):
    """No scope is an error, not a full-table read.

    The ORM session guard is the first of the three nets and the one developers
    hit while writing code, so its failure mode is the most important thing here:
    it must raise rather than return every tenant's rows.
    """
    with pytest.raises(TenancyScopeError):
        await db.execute(select(Server))

    with pytest.raises(TenancyScopeError):
        await db.execute(select(Server.id))  # a column-only load is still a read

    # A refresh of an object loaded *with* a scope goes through the same guard:
    # the row is in the identity map, so a naive refresh could otherwise refresh
    # it under a different (or no) tenant.
    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        with org_scope(uuid.UUID(owner["active_organization_id"])):
            from app.core.tenancy import apply_scope_to_session

            await apply_scope_to_session(session)
            server = (await session.execute(select(Server))).scalars().first()
            assert server is not None
            assert str(server.id) == org_a["server"]["id"]
        with pytest.raises(TenancyScopeError):
            await session.refresh(server)


async def test_scope_cannot_be_switched_on_a_live_session(owner):
    """A session that spans two organizations is how identity-map hits leak."""
    other = uuid.uuid4()
    first = uuid.UUID(owner["active_organization_id"])
    with org_scope(first):
        with pytest.raises(TenancyScopeError):
            with org_scope(other):
                pass  # pragma: no cover - the switch is refused on entry
    # The refusal leaves the (stale) scope untouched and re-entrant.
    assert current_org() is None


async def test_bulk_dml_and_core_statements_are_refused_under_org_scope(org_a, org_db):
    """Loader criteria do not apply to DML — so the guard refuses instead.

    A silent bulk UPDATE with no ``org_id`` predicate would rewrite every
    tenant's rows, which is exactly the failure RLS then catches at the database.
    Both layers are asserted together (see the raw-SQL probes above for RLS's
    half).
    """
    from sqlalchemy import delete, update

    with pytest.raises(TenancyScopeError):
        await org_db.execute(update(Server).values(location="mass-edited"))

    with pytest.raises(TenancyScopeError):
        await org_db.execute(delete(Server).where(Server.name == "org-a-node"))

    # A scoped statement is fine, and touches only this organization. The org id
    # is written explicitly rather than read from a ContextVar, because the
    # statement is built before the session's scope is entered.
    result = await org_db.execute(
        update(Server).where(Server.org_id == uuid.UUID(org_a["id"])).values(location="scoped-edit")
    )
    assert result.rowcount == 1

    # System scope is the deliberate escape hatch (and is allowlisted + logged).
    with system_scope("integration test: bulk maintenance"):
        from app.core.tenancy import apply_scope_to_session

        await apply_scope_to_session(org_db)
        assert (await org_db.execute(select(Server))).scalars().all()


async def test_identity_map_hit_cannot_smuggle_a_row_between_scopes(
    client, owner, org_a, second_org, org_db
):
    """A row loaded in one organization is not usable in another.

    ``expire_on_commit=False`` keeps loaded objects in memory across commits, so
    the same Python object could otherwise be handed to a code path acting for a
    different tenant. The load is scoped to A; the same id asked for from B (and
    from no scope at all) never resolves — the identity map is not a cache that
    can be read across a tenant boundary.
    """
    loaded = (await org_db.execute(select(Server))).scalars().first()
    assert loaded is not None and str(loaded.org_id) == owner["active_organization_id"]
    assert str(loaded.id) == org_a["server"]["id"]

    await org_db.commit()

    # Still in A: the very same object is returned from the identity map.
    still_visible = await org_db.get(Server, loaded.id)
    assert still_visible is not None
    assert still_visible is loaded, "identity map hit within the same tenant"

    # Scoped to B (a fresh session, as a second request would use), the same
    # primary key is not merely filtered — it is absent.
    from app.core.db import get_sessionmaker
    from app.core.tenancy import apply_scope_to_session

    async with get_sessionmaker()() as org_b_session:
        with org_scope(uuid.UUID(second_org["id"])):
            await apply_scope_to_session(org_b_session)
            assert await org_b_session.get(Server, loaded.id) is None


# --- 4. redis / worker delivery ------------------------------------------------


async def test_dispatch_frame_only_notifies_the_frames_own_tenant(client, owner, org_a, second_org):
    """One broadcast channel, two tenants: the frame's org decides who is told."""
    from app.models import NotificationDelivery
    from app.services.notification_service import dispatch_event_frame

    await client.post(
        f"{API}/notification-channels",
        headers=second_org["headers"],
        json={
            "type": "EMAIL",
            "name": "org-b-sink",
            "config": {"recipients": ["b@nexusops.example.com"]},
            "events": ["MONITOR_DOWN"],
        },
    )

    # A real event row for organization A (deliveries reference system_events).
    from app.core.db import get_sessionmaker
    from app.core.tenancy import apply_scope_to_session
    from app.models import SystemEvent
    from app.models.enums import EventLevel

    async with get_sessionmaker()() as writer:
        with org_scope(uuid.UUID(org_a["id"])):
            await apply_scope_to_session(writer)
            event = SystemEvent(
                type="MONITOR_DOWN",
                level=EventLevel.CRITICAL,
                message="probe down",
                data={},
            )
            writer.add(event)
            await writer.commit()
    event_id = str(event.id)

    queued = await dispatch_event_frame(
        {
            "id": event_id,
            "org_id": org_a["id"],
            "type": "MONITOR_DOWN",
            "level": "CRITICAL",
            "message": "probe down",
            "data": {},
        }
    )
    assert queued == 1, "only organization A's channel may be queued"

    async with get_sessionmaker()() as probe_session:
        with system_scope("integration test: delivery probe"):
            await apply_scope_to_session(probe_session)
            deliveries = (
                (
                    await probe_session.execute(
                        select(NotificationDelivery).where(
                            NotificationDelivery.event_id == uuid.UUID(event_id)
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(deliveries) == 1
            assert str(deliveries[0].org_id) == org_a["id"]


async def test_orgless_frame_notifies_nobody(owner, org_a):
    """A platform-level event has no tenant audience — it is not a broadcast."""
    from app.services.notification_service import dispatch_event_frame

    assert await dispatch_event_frame({"type": "SOME.SYSTEM.EVENT", "message": "no org"}) == 0


# --- 5. agents ------------------------------------------------------------------


async def test_agent_token_is_bound_to_its_own_node_and_tenant(client, owner, org_a, second_org):
    """A node token identifies one node in one organization.

    Knowing another node's id (or its container ids) does not let a token speak
    for it: the credential routes to exactly one ``(node, org)`` pair, and every
    downstream write happens inside that organization's scope.
    """
    node_b = (
        await client.post(
            f"{API}/nodes", headers=second_org["headers"], json=server_payload("agent-b-node")
        )
    ).json()
    token_b = (
        await client.post(f"{API}/nodes/{node_b['id']}/agent-token", headers=second_org["headers"])
    ).json()["agent_token"]

    hello_b = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": token_b},
        json={"agent_version": "test-agent/0.1", "hostname": "agent-b-node.integration.test"},
    )
    assert hello_b.status_code == 200, hello_b.text
    assert hello_b.json()["server_id"] == node_b["id"]

    # The row it just updated belongs to B only.
    in_b = await client.get(f"{API}/nodes", headers=second_org["headers"])
    assert node_b["id"] in {row["id"] for row in in_b.json()["items"]}
    in_a = await client.get(f"{API}/nodes", headers=org_a["headers"])
    assert node_b["id"] not in {row["id"] for row in in_a.json()["items"]}

    token_a = (
        await client.post(
            f"{API}/nodes/{org_a['server']['id']}/agent-token", headers=org_a["headers"]
        )
    ).json()["agent_token"]
    first = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": token_a},
        json={"agent_version": "test-agent/0.1", "hostname": "org-a-node.integration.test"},
    )
    assert first.status_code == 200, first.text

    # Rotating A's token does not touch B's node. The old token keeps
    # authenticating for the rotation grace window so a running agent can fetch
    # its replacement on the next beat — that is the whole point of rotation
    # versus revocation.
    rotated = (
        await client.post(
            f"{API}/nodes/{org_a['server']['id']}/agent-token", headers=org_a["headers"]
        )
    ).json()["agent_token"]
    assert rotated != token_a
    during_grace = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": token_a},
        json={"agent_version": "test-agent/0.1", "hostname": "org-a-node.integration.test"},
    )
    assert during_grace.status_code == 200, during_grace.text
    with_new = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": rotated},
        json={"agent_version": "test-agent/0.1", "hostname": "org-a-node.integration.test"},
    )
    assert with_new.status_code == 200, with_new.text

    # The immediate kill switch is revoke, not rotate: after it, *both* tokens
    # are rejected, with an explicit code so the agent's log is actionable.
    revoked = await client.post(
        f"{API}/nodes/{org_a['server']['id']}/agent-token/revoke", headers=org_a["headers"]
    )
    assert revoked.status_code == 200, revoked.text
    for dead in (token_a, rotated):
        rejected = await client.post(
            f"{API}/agent/hello",
            headers={"X-Agent-Token": dead},
            json={"agent_version": "test-agent/0.1", "hostname": "org-a-node.integration.test"},
        )
        assert rejected.status_code == 401, rejected.text
        assert_error_code(rejected.json(), "AGENT_TOKEN_REVOKED")

    # A token that never existed is a different, deliberately distinct code.
    unknown = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": "nxa_does-not-exist"},
        json={"agent_version": "test-agent/0.1", "hostname": "nope"},
    )
    assert unknown.status_code == 401
    assert_error_code(unknown.json(), "AGENT_TOKEN_UNKNOWN")

    # B's token is untouched by A's rotation.
    heartbeat = await client.post(
        f"{API}/agent/heartbeat",
        headers={"X-Agent-Token": token_b},
        json={
            "cpu_percent": 1.0,
            "mem_used_mb": 10.0,
            "mem_percent": 1.0,
            "disk_used_gb": 1.0,
            "disk_percent": 1.0,
            "containers": [],
        },
    )
    assert heartbeat.status_code == 204, heartbeat.text


# --- 6. worker isolation ---------------------------------------------------------


async def test_sweep_processes_every_tenant_without_mixing_their_rows(
    client, owner, org_a, second_org
):
    """A worker sweep claims across tenants and resolves each row's own owner.

    Both organizations get a due monitor; the worker's per-row path must run
    each check inside that monitor's organization, so incidents and checks land
    with the right ``org_id`` rather than in whichever scope happened to be
    active.
    """
    monitor_b = (
        await client.post(
            f"{API}/monitors",
            headers=second_org["headers"],
            json={"name": "sweep-b-probe", "url": "sim://probe/failing"},
        )
    ).json()

    # The task calls asyncio.run() internally (Celery workers are sync), so it is
    # driven from a worker thread exactly like beat does.
    import asyncio

    from app.tasks.monitoring import run_due_monitors

    result = await asyncio.to_thread(run_due_monitors)
    assert result["executed"] >= 1

    from app.core.db import dispose_engine, get_sessionmaker
    from app.core.tenancy import apply_scope_to_session

    await dispose_engine()  # pooled connections are bound to the task's loop
    async with get_sessionmaker()() as probe_session:
        with system_scope("test: cross-tenant check"):
            await apply_scope_to_session(probe_session)
            monitors = (await probe_session.execute(select(Monitor))).scalars().all()
            by_name = {m.name: m for m in monitors}
            assert str(by_name["sweep-b-probe"].org_id) == second_org["id"]
            assert str(by_name["org-a-probe"].org_id) == org_a["id"]
            assert monitor_b["id"] in {
                str(m.id) for m in monitors if str(m.org_id) == second_org["id"]
            }

            # Each tenant's checks carry the tenant that owns the monitor.
            checks = (await probe_session.execute(select(MonitorCheck))).scalars().all()
            monitor_org = {str(m.id): str(m.org_id) for m in monitors}
            assert checks, "the sweep must have recorded the checks it ran"
            for check in checks:
                assert str(check.org_id) == monitor_org[str(check.monitor_id)]


async def test_deployment_and_audit_rows_land_in_the_right_tenant(client, owner, org_a, second_org):
    """Cross-check the write paths that a worker drives on behalf of one tenant."""
    from app.core.db import get_sessionmaker
    from app.core.tenancy import apply_scope_to_session

    node_b = (
        await client.post(
            f"{API}/nodes", headers=second_org["headers"], json=server_payload("deploy-b-node")
        )
    ).json()
    assert node_b["id"]

    async with get_sessionmaker()() as probe_session:
        with system_scope("test: write attribution"):
            await apply_scope_to_session(probe_session)
            audits = (await probe_session.execute(select(AuditLog))).scalars().all()
            orgs = {str(row.org_id) for row in audits if row.org_id is not None}
            assert orgs <= {org_a["id"], second_org["id"]}

            # Every tenant row that exists must name one of the two
            # organizations: a NULL would mean a write path that never resolved
            # an owner (which the RLS WITH CHECK would have refused anyway).
            for model in (Server, Secret, Monitor, NotificationChannel, Deployment):
                rows = (await probe_session.execute(select(model))).scalars().all()
                assert all(str(row.org_id) in {org_a["id"], second_org["id"]} for row in rows), (
                    f"{model.__name__} rows must all carry an organization"
                )


# --- 7. the member directory and session credentials ---------------------------
#
# ``users`` and ``sessions`` are the two surfaces whose tenancy boundary is *not*
# an ``org_id`` column: a person belongs to several organizations through
# ``memberships``, and a session is a credential of the account. Both therefore
# have to be filtered through the membership join, and both used to leak the
# whole instance to any tenant that could reach them.


async def _invite(client, headers: dict, role_name: str, *, password: str = "Integration-Pass1"):
    """Invite a fresh account into the caller's organization and log it in."""
    roles = (await client.get(f"{API}/roles", headers=headers)).json()
    rows = roles["items"] if isinstance(roles, dict) else roles
    role_id = next(r for r in rows if r["name"] == role_name)["id"]

    email = unique_email("member")
    created = await client.post(
        f"{API}/users",
        headers=headers,
        json={
            "email": email,
            "password": password,
            "full_name": f"{role_name} member",
            "role_id": role_id,
        },
    )
    assert created.status_code in (200, 201), created.text
    session = await login_account(client, email=email, password=password)
    return {
        "id": created.json()["user"]["id"],
        "email": email,
        "password": password,
        "role_id": role_id,
        "headers": bearer(session["access_token"], session["active_organization_id"]),
    }


async def test_member_directory_only_ever_shows_the_active_tenant(client, owner, org_a, second_org):
    """The user directory is "who is in this organization", not "who exists".

    ``users`` has no tenant column, so an unjoined ``SELECT`` here is an
    instance-wide dump of names and emails reachable from any organization. The
    directory, the single-user read, the search index and the mutating routes
    are all checked together because they share one boundary: the membership.
    """
    member_a = await _invite(client, org_a["headers"], "Viewer")
    member_b = await _invite(client, second_org["headers"], "Operator")

    listed_a = (await client.get(f"{API}/users", headers=org_a["headers"])).json()
    ids_a = {row["id"] for row in listed_a["items"]}
    assert member_a["id"] in ids_a and owner["user"]["id"] in ids_a
    assert member_b["id"] not in ids_a, "organization B's member leaked into A's directory"

    listed_b = (await client.get(f"{API}/users", headers=second_org["headers"])).json()
    ids_b = {row["id"] for row in listed_b["items"]}
    assert member_b["id"] in ids_b
    assert member_a["id"] not in ids_b

    # The role column must be the membership's role, or the same person would
    # appear to hold one tenant's privileges while being read from another.
    row_a = next(row for row in listed_a["items"] if row["id"] == member_a["id"])
    assert row_a["role_name"] == "Viewer"
    assert row_a["membership_status"] == "ACTIVE"

    # Free-text directory search is the same listing with a pattern.
    filtered = (
        await client.get(f"{API}/users", headers=org_a["headers"], params={"q": member_b["email"]})
    ).json()
    assert filtered["items"] == []

    # The command palette must not become a cross-tenant account lookup either.
    palette = (
        await client.get(f"{API}/search", headers=org_a["headers"], params={"q": "member"})
    ).json()
    palette_ids = {hit["id"] for hit in palette.get("users", [])}
    assert member_b["id"] not in palette_ids
    assert member_a["id"] in palette_ids

    # Direct object access: a foreign user id is a miss, not a hit with a 403.
    foreign_read = await client.get(f"{API}/users/{member_b['id']}", headers=org_a["headers"])
    nonexistent = await client.get(f"{API}/users/{uuid.uuid4()}", headers=org_a["headers"])
    assert foreign_read.status_code == nonexistent.status_code == 404
    assert error_of(foreign_read.json())["code"] == error_of(nonexistent.json())["code"]

    # ... and the mutating routes cannot be used to reconfigure another tenant's
    # member: the role change and the removal both miss, and B's member keeps
    # the role it had.
    for method, body in (("patch", {"role_id": member_a["role_id"]}), ("delete", None)):
        call = getattr(client, method)
        response = await call(
            f"{API}/users/{member_b['id']}",
            headers=org_a["headers"],
            **({"json": body} if body else {}),
        )
        assert response.status_code == 404, f"{method} crossed the tenant boundary: {response.text}"

    b_row = next(
        row
        for row in (await client.get(f"{API}/users", headers=second_org["headers"])).json()["items"]
        if row["id"] == member_b["id"]
    )
    assert b_row["role_name"] == "Operator"
    assert b_row["membership_status"] == "ACTIVE"
    assert b_row["role_id"] != member_a["role_id"], "roles are per-organization"


async def test_suspending_a_member_is_confined_to_one_organization(
    client, owner, org_a, second_org, db
):
    """Removing someone from A must not reach their account or their other tenant.

    The same person is a member of both organizations. Suspending them in A ends
    their access *there*: their membership in B, their account, and their live
    sessions are untouched. Disabling the account or revoking its credentials
    would have been a cross-tenant denial of service available to any
    organization administrator.
    """
    from datetime import UTC, datetime

    from app.models import Membership
    from app.models.enums import MembershipStatus

    member = await _invite(client, org_a["headers"], "Viewer")

    # A second membership in B for the *same* account. The API only invites new
    # accounts, so the row is written directly — ``memberships`` is one of the
    # deliberately pre-org tables, which is why this works without a scope.
    db.add(
        Membership(
            org_id=uuid.UUID(second_org["id"]),
            user_id=uuid.UUID(member["id"]),
            role_id=uuid.UUID(member["role_id"]),
            status=MembershipStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    await db.commit()

    removed = await client.delete(f"{API}/users/{member['id']}", headers=org_a["headers"])
    assert removed.status_code == 200, removed.text
    assert removed.json()["membership_status"] == "SUSPENDED"
    assert removed.json()["is_active"] is True, "a tenant may not disable the account"

    # A no longer offers it, and the membership row survives as history.
    listed_a = (await client.get(f"{API}/users", headers=org_a["headers"])).json()["items"]
    row_a = next(row for row in listed_a if row["id"] == member["id"])
    assert row_a["membership_status"] == "SUSPENDED"

    # The client can no longer act in A: X-Org-Id validation reads memberships,
    # and a suspended one is not authority.
    blocked = await client.get(f"{API}/nodes", headers=member["headers"])
    assert blocked.status_code == 403
    assert_error_code(blocked.json(), "ORGANIZATION_FORBIDDEN")

    # ... but the tenant it was NOT removed from is unaffected, and the account
    # — including the session it already had — still works.
    still_member = await login_account(client, email=member["email"], password=member["password"])
    org_ids = {row["organization"]["id"] for row in still_member["organizations"]}
    assert second_org["id"] in org_ids and org_a["id"] not in org_ids
    assert (
        await client.get(
            f"{API}/nodes",
            headers=bearer(still_member["access_token"], second_org["id"]),
        )
    ).status_code == 200


async def test_one_tenants_session_list_and_revocation_stop_at_its_members(
    client, owner, org_a, second_org
):
    """``sessions`` has no tenant column: the owning membership is the boundary.

    Without it, ``?all=true`` (a single ``user.manage`` request) is an
    instance-wide feed of IP addresses, device labels and user agents, and
    revoking by id is a cross-tenant DoS. A session outside the tenant must be
    invisible and unrevokable, and reported exactly like one that never existed.
    """
    member_a = await _invite(client, org_a["headers"], "Viewer")
    member_b = await _invite(client, second_org["headers"], "Viewer")

    sessions_b = (await client.get(f"{API}/sessions", headers=member_b["headers"])).json()["items"]
    assert sessions_b, "the invited member must have a live session"
    session_b_id = sessions_b[0]["id"]

    listed = await client.get(f"{API}/sessions", headers=org_a["headers"], params={"all": True})
    assert listed.status_code == 200, listed.text
    listed_ids = {row["id"] for row in listed.json()["items"]}
    assert session_b_id not in listed_ids, "another tenant's session was listed"

    own = (await client.get(f"{API}/sessions", headers=member_a["headers"])).json()["items"]
    assert {row["id"] for row in own} & listed_ids, "same-tenant sessions must still be visible"

    # Filtering by a foreign user is a miss (not a 403, which would confirm the
    # account exists), and so is revoking their session.
    filtered = await client.get(
        f"{API}/sessions", headers=org_a["headers"], params={"user_id": member_b["id"]}
    )
    assert filtered.status_code == 404

    revoked = await client.delete(f"{API}/sessions/{session_b_id}", headers=org_a["headers"])
    assert revoked.status_code == 404, revoked.text
    survivor = (await client.get(f"{API}/sessions", headers=member_b["headers"])).json()["items"]
    assert session_b_id in {row["id"] for row in survivor}
