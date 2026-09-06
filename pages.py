from dataclasses import asdict
from uuid import UUID

import minify_html
import quart
from quart import request

import db


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
