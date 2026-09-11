"""Idempotent demo seed: roles, admin user, simulated fleet, monitors, history.

Run via ``make seed`` (or ``uv run python scripts/seed.py``). Safe to run
repeatedly and across replicas: everything is guarded by a Postgres advisory
lock and exits early when an admin already exists.

Opt-in outside the ``test`` environment (``NEXUSOPS_ALLOW_SEED=1``): a seed
superadmin with a publicly-known password would be a standing full-platform
backdoor. Outside ``test`` the admin password is generated randomly, printed
ONCE on stdout, and no API key is created (a derivable seeded key would be
equally fatal). In ``test`` the deterministic dev credentials below are kept
so automated suites stay reproducible.
"""

from __future__ import annotations

import asyncio
import os
import secrets
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlalchemy as sa
from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.core.logging import configure_logging, get_logger
from app.core.permissions import PERMISSIONS, ROLE_MATRIX
from app.core.security import (
    digest_of,
    encrypt_str,
    generate_agent_token,
    hash_password,
    hash_token,
)
from app.models import (
    Alert,
    ApiKey,
    Application,
    Deployment,
    DeploymentEnvironment,
    DeploymentStep,
    DockerHost,
    Incident,
    IncidentEvent,
    LogEntry,
    Monitor,
    NotificationChannel,
    Permission,
    Project,
    Role,
    Server,
    Session,
    Tag,
    User,
)
from app.models.enums import (
    DeploymentStatus,
    IncidentSeverity,
    IncidentStatus,
    MonitorStatus,
    ServerStatus,
    StepStatus,
    UserStatus,
)

configure_logging()
logger = get_logger("seed")

ADMIN_EMAIL = "admin@nexusops.example.com"
DEV_ADMIN_PASSWORD = "nexusops-admin"  # noqa: S105 - test-only seed credential
DEV_VIEWER_PASSWORD = "nexusops-dev-123"  # noqa: S105 - test-only seed credential
SEED_API_KEY_RAW = "nxo_" + "seed-demo-key-do-not-use"


def _seed_credentials(settings) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    """(admin_password, viewer_password): deterministic in test, random otherwise."""
    if settings.is_testing:
        return DEV_ADMIN_PASSWORD, DEV_VIEWER_PASSWORD
    return secrets.token_urlsafe(16), secrets.token_urlsafe(16)


SERVERS = [
    ("web-prod-01", "10.0.4.11", "production", "us-east", ["frontend", "critical"], False),
    ("api-prod-02", "10.0.4.12", "production", "us-east", ["api", "critical"], False),
    ("db-prod-03", "10.0.4.13", "production", "us-east", ["database", "critical"], False),
    ("worker-staging-01", "10.1.2.21", "staging", "eu-west", ["worker"], False),
    ("edge-cache-02-flaky", "10.0.9.32", "production", "eu-west", ["cache", "flaky"], True),
]

CONTAINERS = {
    "web-prod-01": [("edge-proxy", "nginx:1.27-alpine"), ("static-site", "caddy:2.8")],
    "api-prod-02": [
        ("app-server", "ghcr.io/nexusops/demo-api:1.4.2"),
        ("job-runner", "python:3.13-slim"),
    ],
    "db-prod-03": [
        ("postgres-main", "postgres:17-alpine"),
        ("pgbouncer", "edoburu/pgbouncer:1.23"),
    ],
    "worker-staging-01": [("celery-worker", "ghcr.io/nexusops/demo-api:1.4.2")],
    "edge-cache-02-flaky": [("varnish", "varnish:7.5")],
}

MONITORS = [
    # name, url, interval, threshold, expect
    ("Public homepage", "sim://public/homepage", 30, 3, 200),
    ("API health endpoint", "sim://api/health", 15, 3, 200),
    ("Checkout flow probe", "sim://checkout/flaky", 20, 3, 200),
    ("Legacy status page", "sim://legacy/always-down", 60, 2, 200),
]


async def _lock(db) -> None:  # type: ignore[no-untyped-def]
    await db.execute(sa.text("SELECT pg_advisory_lock(hashtext('nexusops-seed'))"))


async def _unlock(db) -> None:  # type: ignore[no-untyped-def]
    await db.execute(sa.text("SELECT pg_advisory_unlock(hashtext('nexusops-seed'))"))


async def seed() -> int:
    settings = get_settings()
    maker = get_sessionmaker()
    async with maker() as db:
        await _lock(db)
        try:
            existing = (await db.execute(sa.select(sa.func.count()).select_from(User))).scalar_one()
            if existing:
                logger.info("seed_skipped", reason="users exist", users=existing)
                return 0

            now = datetime.now(UTC)
            await _seed_rbac(db)

            owner_role = (
                await db.execute(sa.select(Role).where(Role.name == "Owner"))
            ).scalar_one()
            operator_role = (
                await db.execute(sa.select(Role).where(Role.name == "Operator"))
            ).scalar_one()

            admin_password, viewer_password = _seed_credentials(settings)
            admin = User(
                email=ADMIN_EMAIL,
                full_name="Ops Admin",
                password_hash=hash_password(admin_password),
                is_superadmin=True,
                status=UserStatus.ACTIVE,
                role_id=owner_role.id,
                last_login_at=now - timedelta(hours=2),
            )
            viewer = User(
                email="dev@nexusops.example.com",
                full_name="Devin Developer",
                password_hash=hash_password(viewer_password),
                status=UserStatus.ACTIVE,
                role_id=operator_role.id,
            )
            db.add_all([admin, viewer])
            await db.flush()

            admin_session = Session(
                user_id=admin.id,
                ip_address="127.0.0.1",
                user_agent="seed-script",
                device_label="workstation",
                expires_at=now + timedelta(days=7),
                last_seen_at=now - timedelta(minutes=5),
            )
            db.add(admin_session)
            # A seeded API key with a value derivable from source is a standing
            # credential; only ever create it inside the throwaway test env.
            if settings.is_testing:
                db.add(
                    ApiKey(
                        user_id=admin.id,
                        name="seed CI key",
                        key_prefix=SEED_API_KEY_RAW[:12],
                        key_hash=hash_token(SEED_API_KEY_RAW),
                        scopes=["server.read", "deployment.read"],
                    )
                )

            servers = await _seed_fleet(db, now)
            await _seed_monitors(db, admin, now)
            project = await _seed_delivery(db, admin, servers, now)
            await _seed_history(db, admin, servers, project, now)

            await db.commit()
            logger.info(
                "seed_done",
                admin_email=ADMIN_EMAIL,
                simulated_servers=len(servers),
                simulation_mode=settings.simulation_mode,
            )
            if not settings.is_testing:
                # One-time disclosure: the generated credentials are printed
                # exactly once and never persisted in derivable form.
                print(
                    f"[nexusops] Seeded admin {ADMIN_EMAIL}\n"
                    f"[nexusops]   one-time password: {admin_password}\n"
                    f"[nexusops] Rotate this password immediately — it will not be shown again.",
                    file=sys.stderr,
                )
            return 0
        except Exception:
            await db.rollback()
            raise
        finally:
            await _unlock(db)


async def _seed_rbac(db) -> None:  # type: ignore[no-untyped-def]
    for spec in PERMISSIONS:
        db.add(Permission(codename=spec.codename, group=spec.group, description=spec.description))
    await db.flush()
    perms = {p.codename: p for p in (await db.execute(sa.select(Permission))).scalars()}
    for role_name, codenames in ROLE_MATRIX.items():
        role = Role(name=role_name, description=f"{role_name} (system)", is_system=True)
        if codenames != ["*"]:
            role.permissions = [perms[c] for c in codenames]
        db.add(role)
    await db.flush()


async def _seed_fleet(db, now: datetime) -> list[Server]:  # type: ignore[no-untyped-def]
    tag_cache: dict[str, Tag] = {}
    servers: list[Server] = []
    for idx, (name, ip, env, location, tag_names, _simulated) in enumerate(SERVERS):
        server_tags = []
        for tag_name in tag_names:
            if tag_name not in tag_cache:
                tag = Tag(
                    name=tag_name,
                    color=["#2563eb", "#059669", "#d97706", "#dc2626"][len(tag_cache) % 4],
                )
                db.add(tag)
                await db.flush()
                tag_cache[tag_name] = tag
            server_tags.append(tag_cache[tag_name])

        server = Server(
            name=name,
            hostname=f"{name}.nexusops.internal",
            ip_address=ip,
            os_name="Ubuntu",
            os_version="24.04 LTS",
            arch="x86_64",
            environment=env,
            location=location,
            description=f"Simulated {env} node managed by NexusOps demo fleet",
            status=ServerStatus.UNKNOWN,
            cpu_cores=[8, 16, 4, 8, 4][idx % 5],
            memory_total_mb=[16384, 32768, 8192, 16384, 8192][idx % 5],
            disk_total_gb=[200, 500, 1000, 250, 120][idx % 5],
            heartbeat_interval_seconds=30,
            last_heartbeat_at=None,
            simulated=True,
            extra={"provider": "simulation", "demo_fleet": True},
        )
        server.tags = server_tags
        db.add(server)
        servers.append(server)
    await db.flush()

    token_hashes = {}
    for server in servers:
        raw, _prefix, token_hash = generate_agent_token()
        token_hashes[server.name] = raw
        server.agent_token_hash = token_hash
        server.agent_enrolled_at = now
        host = DockerHost(
            server_id=server.id,
            name=f"agent-{server.name}",
            endpoint_url=f"agent://{server.name}",
            status="UNKNOWN",
        )
        db.add(host)
        await db.flush()
        for cname, image in CONTAINERS.get(server.name, []):
            from app.models import Container

            db.add(
                Container(
                    docker_host_id=host.id,
                    server_id=server.id,
                    container_id=f"sim{uuid4().hex[:16]}",
                    name=cname,
                    image_ref=image,
                    status="RUNNING",
                    health="HEALTHY",
                    observed_at=now,
                    started_at=now - timedelta(days=idx + 1),
                    restart_count=(server.name.count("-")),
                    cpu_percent=12.5,
                    mem_used_mb=180,
                    mem_limit_mb=1024,
                    simulated=True,
                )
            )
    await db.flush()
    return servers


async def _seed_monitors(db, admin: User, now: datetime) -> None:  # type: ignore[no-untyped-def]
    for name, url, interval, threshold, expected in MONITORS:
        db.add(
            Monitor(
                name=name,
                url=url,
                method="GET",
                interval_seconds=interval,
                timeout_seconds=10,
                expected_status=expected,
                enabled=True,
                status=MonitorStatus.PENDING,
                next_check_at=now,
                failure_threshold=threshold,
                success_threshold=2,
                created_by_id=admin.id,
            )
        )
    email_channel = NotificationChannel(
        name="Ops email (mailpit)",
        type="EMAIL",
        config_ciphertext=encrypt_str('{"recipients": ["ops@nexusops.example.com"]}'),
        display_target="ops@nexusops.example.com",
        events=[
            "MONITOR_DOWN",
            "MONITOR_RECOVERED",
            "DEPLOYMENT_FAILED",
            "SERVER_OFFLINE",
            "INCIDENT_OPENED",
        ],
        enabled=True,
        created_by_id=admin.id,
    )
    db.add(email_channel)
    await db.flush()


async def _seed_delivery(db, admin: User, servers: list[Server], now: datetime):  # type: ignore[no-untyped-def]
    from app.models import Secret

    project = Project(
        name="Demo Platform", repository_url="https://git.example.com/acme/platform.git"
    )
    db.add(project)
    await db.flush()
    app_row = Application(
        project_id=project.id,
        name="platform-api",
        slug="platform-api",
        build_config={"dockerfile": "Dockerfile", "registry": "ghcr.io/acme"},
    )
    db.add(app_row)
    await db.flush()
    env_row = DeploymentEnvironment(
        application_id=app_row.id,
        name="production",
        slug="production",
        server_id=servers[1].id,
        healthcheck_path="/healthz",
        auto_deploy=False,
        config={
            "DATABASE_URL": "${secret:PLATFORM_DB_URL}",
            "REDIS_HOST": "redis.internal",
        },
    )
    db.add(env_row)
    db.add(
        Secret(
            key="PLATFORM_DB_URL",
            ciphertext=encrypt_str("postgresql://demo:demo@db.internal/platform"),
            version=1,
            digest=digest_of("postgresql://demo:demo@db.internal/platform"),
            description="Platform API production database (seed)",
            created_by_id=admin.id,
            rotated_at=now,
        )
    )
    await db.flush()
    return project


async def _seed_history(
    db, admin: User, servers: list[Server], project: Project, now: datetime
) -> None:
    """Two finished deployments + one open incident so pages have substance."""
    app_row = (await db.execute(sa.select(Application))).scalars().first()
    env_row = (await db.execute(sa.select(DeploymentEnvironment))).scalars().first()
    assert app_row and env_row

    specs = [
        (
            14,
            "1.4.2",
            DeploymentStatus.SUCCESS,
            "a1b2c3d",
            "release 1.4.2",
            now - timedelta(days=2),
        ),
        (
            15,
            "1.5.0-broken",
            DeploymentStatus.FAILED,
            "e4f5a6b",
            "hotfix attempt",
            now - timedelta(days=1),
        ),
    ]
    step_names = [
        "PULL_REPO",
        "CHECKOUT",
        "BUILD_IMAGE",
        "STOP_OLD_CONTAINER",
        "START_NEW_CONTAINER",
        "HEALTH_CHECK",
        "FINALIZE",
    ]
    for number, version, status, commit, notes, created in specs:
        dep = Deployment(
            application_id=app_row.id,
            number=number,
            environment_id=env_row.id,
            version=version,
            git_commit=commit,
            notes=notes,
            status=status,
            trigger="MANUAL",
            triggered_by_id=admin.id,
            queued_at=created,
            started_at=created + timedelta(seconds=3),
            finished_at=created + timedelta(minutes=4),
            duration_ms=237_000,
            failure_reason=""
            if status == DeploymentStatus.SUCCESS
            else "HEALTH_CHECK failed after retries",
        )
        db.add(dep)
        await db.flush()
        failed_at = step_names.index("HEALTH_CHECK") if status == DeploymentStatus.FAILED else None
        for idx, step_name in enumerate(step_names):
            if failed_at is not None and idx > failed_at:
                step_status = StepStatus.SKIPPED
            elif failed_at is not None and idx == failed_at:
                step_status = StepStatus.FAILED
            else:
                step_status = StepStatus.SUCCESS
            db.add(
                DeploymentStep(
                    deployment_id=dep.id,
                    idx=idx,
                    name=step_name,
                    status=step_status,
                    output=f"[{step_name}] simulated output for {version}\nok",
                    error=None
                    if step_status != StepStatus.FAILED
                    else "healthcheck: connection refused",
                    started_at=dep.started_at + timedelta(seconds=idx * 30),
                    finished_at=dep.started_at + timedelta(seconds=idx * 30 + 25),
                )
            )
            db.add(
                LogEntry(
                    source="DEPLOYMENT",
                    deployment_id=dep.id,
                    stream="stdout",
                    level="INFO",
                    message=f"[{step_name}] completed for {version}",
                    ts=dep.started_at + timedelta(seconds=idx * 30),
                )
            )
        await db.flush()

    legacy_monitor = (
        await db.execute(sa.select(Monitor).where(Monitor.url == "sim://legacy/always-down"))
    ).scalar_one()
    opened = now - timedelta(hours=6)
    incident = Incident(
        monitor_id=legacy_monitor.id,
        title="Legacy status page is down",
        severity=IncidentSeverity.MAJOR,
        status=IncidentStatus.OPEN,
        failure_count=342,
        opened_at=opened,
        detected_at=opened,
    )
    db.add(incident)
    await db.flush()
    db.add_all(
        [
            IncidentEvent(
                incident_id=incident.id,
                kind="OPENED",
                message="Failure threshold reached (2 consecutive failures)",
                occurred_at=opened,
            ),
            IncidentEvent(
                incident_id=incident.id,
                kind="NOTIFIED",
                message="Notification sent via Ops email (mailpit)",
                occurred_at=opened + timedelta(seconds=4),
            ),
            IncidentEvent(
                incident_id=incident.id,
                kind="NOTE",
                message="Legacy host scheduled for decommission; acknowledged noise.",
                occurred_at=opened + timedelta(hours=1),
            ),
        ]
    )
    db.add(
        Alert(
            severity="CRITICAL",
            title="Legacy status page is DOWN",
            body="sim://legacy/always-down failing since last hour",
            event_type="MONITOR_DOWN",
            source="monitor",
            resource_type="monitor",
            resource_id=str(legacy_monitor.id),
        )
    )
    await db.flush()


if __name__ == "__main__":
    _settings = get_settings()
    _opted_in = os.environ.get("NEXUSOPS_ALLOW_SEED", "").strip().lower() in {"1", "true", "yes"}
    if _settings.is_production:
        print("[nexusops] refusing to seed a production environment", file=sys.stderr)
        raise SystemExit(2)
    if not _settings.is_testing and not _opted_in:
        # Seeding a shared environment must be an explicit decision: the seed
        # creates a superadmin, and doing so silently is how known default
        # credentials end up on network-reachable hosts.
        print(
            "[nexusops] refusing to seed a non-test environment without explicit opt-in.\n"
            "[nexusops] Re-run with NEXUSOPS_ALLOW_SEED=1 to create the demo superadmin\n"
            "[nexusops] (a random one-time password will be printed once).",
            file=sys.stderr,
        )
        raise SystemExit(2)
    raise SystemExit(asyncio.run(seed()))
