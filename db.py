import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from uuid import UUID

import asyncpg as pg

type IPAddress = IPv4Address | IPv6Address


ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

conn: pg.Connection


@dataclass
class Password:
    id: UUID
    password: str
    access_level: int
    created_at: datetime


@dataclass
class Session:
    token: UUID
    access_level: int
    is_admin: bool
    created_at: datetime


async def init() -> None:
    global conn
    conn = await pg.connect(
        user="otto",
        password="shushing_face",
        database="roming",
        host="db",
    )


@asynccontextmanager
async def transaction() -> AsyncIterator[None]:
    async with conn.transaction():
        yield


async def login(password: str, user_agent: str | None, client_ip: str) -> UUID | None:
    if password == ADMIN_PASSWORD:
        session_row = await conn.fetchrow(
            """
            INSERT INTO sessions (access_level, is_admin)
            VALUES (100, true)
            RETURNING token
       """
        )
        assert session_row is not None
        return session_row["token"]

    password_row = await conn.fetchrow(
        """
        SELECT *
        FROM passwords
        WHERE password = $1;
     """,
        password,
    )
    if password_row is None:
        return None
    password_id: UUID = password_row["id"]
    access_level: int = password_row["access_level"]

    await conn.execute(
        """
        INSERT INTO logins (password_id, user_agent, client_ip)
        VALUES ($1, $2, $3::inet);
   """,
        password_id,
        user_agent,
        client_ip,
    )

    if access_level:
        session_row = await conn.fetchrow(
            """
            INSERT INTO sessions (access_level)
            VALUES ($1)
            RETURNING token
       """,
            access_level,
        )
        assert session_row is not None

        session_token: UUID = session_row["token"]
        return session_token

    return None


async def get_session_by_token(token: UUID) -> Session | None:
    session = await conn.fetchrow(
        """
        SELECT *
        FROM sessions
        WHERE token = $1;
    """,
        token,
    )

    return Session(**dict(session)) if session else None


async def get_passwords() -> list[Password]:
    rows = await conn.fetch(
        """
        SELECT *
        FROM passwords;
    """
    )

    return [Password(**dict(row)) for row in rows]


async def add_password(password: str, access_level: int) -> Password:
    row = await conn.fetchrow(
        """
        INSERT INTO passwords (password, access_level)
        VALUES ($1, $2)
        RETURNING *;
    """,
        password,
        access_level,
    )
    assert row is not None

    return Password(**dict(row))


@dataclass
class LoginPassword:
    id: UUID
    password: Password
    user_agent: str
    client_ip: IPAddress
    created_at: datetime


async def get_logins() -> list[LoginPassword]:
    rows = await conn.fetch(
        """
        SELECT
            json_build_object(
                'id', l.id,
                'user_agent', l.user_agent,
                'client_ip', l.client_ip,
                'created_at', l.created_at
            ) AS login,
            json_build_object(
                'id', p.id,
                'password', p.password,
                'access_level', p.access_level,
                'created_at', p.created_at
            ) AS password
        FROM logins AS l
        LEFT JOIN passwords AS p
        ON l.password_id = p.id;
    """
    )

    print([row for row in rows][0])
    return []
