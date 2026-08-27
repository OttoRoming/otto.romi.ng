import os
import pickle
import subprocess
from pathlib import Path
from typing import Any, Literal
from uuid import UUID
import pwd
from datetime import datetime
import asyncio

from quart import (
    Quart,
    abort,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
    Response as QuartResponse
)
from werkzeug.exceptions import HTTPException
from werkzeug import Response as WerkResponse
import db

type Response = QuartResponse | WerkResponse



STORE_FILENAME = "store.pickle"

PREVIEW_EXT: dict[str, Literal["image", "video", "document"]] = {
    # Image formats
    ".jpg": "image",
    ".jpeg": "image",
    ".jpe": "image",
    ".jif": "image",
    ".jfif": "image",
    ".png": "image",
    ".gif": "image",
    ".svg": "image",
    ".svgz": "image",
    ".webp": "image",
    ".avif": "image",
    ".avifs": "image",
    ".apng": "image",
    ".ico": "image",
    ".cur": "image",
    ".bmp": "image",
    ".dib": "image",
    # Video formats
    ".mp4": "video",
    ".m4v": "video",
    ".webm": "video",
    # Document formats
    ".pdf": "document",
}


# https://stackoverflow.com/questions/41505448/is-python-uuid-uuid4-strong-enough-for-password-reset-links
def uuid4():
    """Generate a cryptographically secure random UUID."""
    return UUID(bytes=os.urandom(16), version=4)

# class SessionStore:
#     def __init__(self) -> None:
#         self.sessions: dict[UUID, int] = {}
#
#     def dump(self) -> None:
#         with open(STORE_FILENAME, "wb") as f:
#             pickle.dump(self, f)
#
#     def new_session(self, level: int) -> UUID:
#         session = uuid4()
#         self.sessions[session] = level
#
#         self.dump()
#         return session
#
#     def remove_session(self, session: UUID | None = None) -> None:
#         if session is None:
#             session_str = request.cookies.get("session")
#             if session_str is None:
#                 return None
#
#             session = UUID(session_str)
#
#         del self.sessions[session]
#
#     def get_access_level(self, session: UUID | None = None) -> int | None:
#         if session is None:
#             session_str = request.cookies.get("session")
#             if session_str is None:
#                 return None
#
#             session = UUID(session_str)
#
#         return self.sessions.get(session)


app = Quart(__name__)

# try:
#     with open(STORE_FILENAME, "rb") as f:
#         store = pickle.load(f)
# except FileNotFoundError:
#     store = SessionStore()

async def generate_context(other: dict[str, Any] = {}) -> dict[str, Any]:
    token = request.cookies.get("token")
    access_level: int | None = None

    if token is not None:
        access_level = await db.get_session_access_level(UUID(token))

    return {
        "access_level": access_level,
        **other,
    }


@app.errorhandler(HTTPException)
async def error(error: HTTPException) -> str:

    context = await generate_context({"code": error.code, "name": error.name})
    return await render_template("error.html", **context)


@app.get("/")
async def index() -> str:
    context = await generate_context()
    return await render_template("index.html", **context)


@app.get("/login/", defaults={"path": ""})
@app.get("/login/<path:path>")
async def login(path: str) -> str:
    context = await generate_context()
    return await render_template("login.html", **context)


@app.post("/login/", defaults={"path": ""})
@app.post("/login/<path:path>")
async def login_post(path: str) -> Response:
    form = await request.form
    password = form.get("password")
    if password is None:
        abort(400)

    user_agent = request.headers.get("User-Agent")

    client_ip = request.remote_addr
    if client_ip is None:
        abort(400)

    response = await make_response(redirect(url_for("public", path=path)))
    token = await db.login(password, user_agent, client_ip)
    
    response.set_cookie("token", str(token))
    return response


@app.get("/signout")
async def signout() -> Response:
    response = await make_response(redirect(url_for("index")))
    response.delete_cookie("session")

    return response


@app.get("/preview/<path:path>")
async def preview(path: str) -> Response | str:
    return await make_response(redirect(url_for("public", path=path)))

    # login_response = make_response(redirect(url_for("login", path=path)))

    # access_level = store.get_access_level()
    # if access_level is None:
    #     return login_response

    # # https://en.wikipedia.org/wiki/Directory_traversal_attack
    # if ".." in path:
    #     abort(400)

    # type = PREVIEW_EXT.get(os.path.splitext(path)[1])
    # if type is None:

    # filename = Path(path).name

    # return render_template(
    #     "preview.html",
    #     **generate_context({"type": type, "path": path, "filename": filename}),
    # )


@app.get("/public/", defaults={"path": ""})
@app.get("/public/<path:path>")
async def public(path: str = "") -> Response | str:
    login_response = await make_response(redirect(url_for("login", path=path)))

    access_level = store.get_access_level()
    if access_level is None:
        return login_response

    # https://en.wikipedia.org/wiki/Directory_traversal_attack
    if ".." in path:
        abort(400)

    mode = request.args.get("mode")
    if mode is None:
        mode = "icons"

    entries = []
    home = os.getenv("HOME")

    p = Path(f"{home}/shared/public")
    realpath = p / path
    display_path = Path(path)
    parent_path = display_path.parent
    print(realpath)

    if os.path.isdir(realpath):
        for entry in os.scandir(realpath):
            if entry.name == ".confidential" and access_level < 2:
                abort(451)

            extension = os.path.splitext(entry.path)[1]
            preview_availible = extension.lower() in PREVIEW_EXT

            type = ""
            if entry.is_symlink():
                type = "symlink"
            elif entry.is_file():
                type = "file"
            elif entry.is_dir():
                type = "dir"

            stat = entry.stat()
            owner_info = pwd.getpwuid(stat.st_uid)
            dt = datetime.fromtimestamp(stat.st_mtime)

            entries.append(
                {
                    "name": entry.name,
                    "mode": oct(stat.st_mode),
                    "owner": owner_info.pw_name,
                    "type": type,
                    "modified_day": dt.strftime("%d"),
                    "modified_month": dt.strftime("%b"),
                    "modified_year": dt.strftime("%Y"),
                    "preview_available": preview_availible,
                }
            )

        context = await generate_context(
            {
                "display_path": str(display_path),
                "parent_path": str(parent_path),
                "entries": entries,
                "mode": mode
            }
        )
        return await render_template("public/dir.html", **context)
    elif os.path.isfile(realpath):

        return await send_file(realpath)
    else:
        abort(404)


@app.before_serving
async def init():
    await db.init()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
