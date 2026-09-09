from dataclasses import asdict
from typing import TypedDict
from uuid import UUID

import httpx
import minify_html
import quart
from httpx import HTTPStatusError
from quart import request

import db
from db import IPAddress


async def authenticate_user() -> db.Session | None:
    token = request.cookies.get("token")
    if token is None:
        return None

    try:
        uuid = UUID(token)
    except ValueError:
        return None

    return await db.get_session_by_token(uuid)


async def render_template(template: str, **kwargs) -> str:
    session = await authenticate_user()
    session_dict = asdict(session) if session else {}

    raw = await quart.render_template(template, session=session_dict, **kwargs)
    minified = minify_html.minify(raw, minify_css=True)
    return minified


class LocationInfo(TypedDict):
    country: str
    stateprov: str
    stateprovCode: str
    city: str
    latitude: str
    longitude: str
    continent: str
    timezone: str
    asn: int
    asnOrganization: str


async def get_ip_geo(ip: IPAddress) -> LocationInfo | None:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://geoip:8080/{ip}")
        try:
            response.raise_for_status()
        except HTTPStatusError as _:
            return None
        data = response.json()
        return data
