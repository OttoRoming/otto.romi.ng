from contextlib import asynccontextmanager
import asyncpg as pg
from collections.abc import AsyncIterator
from ipaddress import IPv4Address, IPv6Address
from uuid import UUID

type IPAddress = IPv4Address | IPv6Address


conn: pg.Connection

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
    password_row = await conn.fetchrow("""
        SELECT (id, access_level)
        FROM passwords
        WHERE password = $1;
     """, password)
    password_id: UUID | None = password_row["id"] if password_row else None
    access_level: int | None = password_row["access_level"] if password_row else None

    await conn.execute("""
        INSERT INTO logins (password_id, user_agent, client_ip)
        VALUES ($1, $2, $3::inet);
   """, password_id, user_agent, client_ip)

    if access_level:
        session_row = await conn.fetchrow("""
            INSERT INTO sessions (access_level)
            VALUES ($1)
            RETURNING token
       """, access_level)

        session_token: UUID = session_row["token"]
        return session_token
    
    return None

async def get_session_access_level(token: UUID) -> int | None:
    session = await conn.fetchrow("""
        SELECT (access_level)
        FROM sessions
        WHERE token = $1;
    """, token)
    access_level = session["access_level"] if session else None

    return access_level

