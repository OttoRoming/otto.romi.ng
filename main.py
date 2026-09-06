import os
import pwd
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from quart import (
    Quart,
    abort,
    make_response,
    redirect,
    request,
    send_file,
    url_for,
)
from quart import Response as QuartResponse
from werkzeug import Response as WerkResponse
from werkzeug.exceptions import HTTPException

import db
from pages import authenticate_user, render_template

type Response = QuartResponse | WerkResponse

app = Quart(__name__)


async def login_response() -> Response:
    response = await make_response(redirect(url_for("login", path=request.url)))
    return response


@app.errorhandler(HTTPException)
async def error(error: HTTPException) -> str:
    return await render_template("error.html")


@app.get("/")
async def index() -> str:
    return await render_template("index.html")


@app.get("/robots.txt")
async def robots() -> Response:
    response = await make_response()
    response.content_type = "text/plain"
    response.data = "User-agent: *\nAllow: /".encode("utf-8")
    return response


@app.get("/login/")
async def login() -> str:
    return await render_template("login.html")


@app.post("/login/")
async def login_post() -> Response:
    form = await request.form
    password = form.get("password")
    if password is None:
        abort(400)

    user_agent = request.headers.get("User-Agent")

    client_ip = request.remote_addr
    if client_ip is None:
        abort(400)

    redirect_url = request.args.get("path")
    if redirect_url is None:
        redirect_url = url_for("index")

    response = await make_response(redirect(redirect_url))
    token = await db.login(password, user_agent, client_ip)

    response.set_cookie("token", str(token))
    return response


@app.get("/signout")
async def signout() -> Response:
    response = await make_response(redirect(url_for("index")))
    response.delete_cookie("token")

    return response


@app.get("/public/", defaults={"path": ""})
@app.get("/public/<path:path>")
async def public(path: str = "") -> Response | str:
    session = await authenticate_user()
    if session is None:
        return await login_response()

    # https://en.wikipedia.org/wiki/Directory_traversal_attack
    if ".." in path:
        abort(400)

    mode = request.args.get("mode")
    if mode not in ["icons", "details"]:
        mode = "icons"

    entries = []

    p = Path("/public")
    realpath = p / path
    display_path = Path(path)
    parent_path = display_path.parent

    if os.path.isdir(realpath):
        for entry in os.scandir(realpath):
            if entry.name == ".confidential" and session.access_level < 2:
                abort(451)

            # extension = os.path.splitext(entry.path)[1]
            # preview_availible = extension.lower() in PREVIEW_EXT

            type = ""
            if entry.is_symlink():
                type = "symlink"
            elif entry.is_file():
                type = "file"
            elif entry.is_dir():
                type = "dir"

            stat = entry.stat()

            try:
                owner = pwd.getpwuid(stat.st_uid).pw_name
            except KeyError:  # If the userid is not on the system
                owner = str(stat.st_uid)

            dt = datetime.fromtimestamp(stat.st_mtime)

            entries.append(
                {
                    "name": entry.name,
                    "mode": oct(stat.st_mode),
                    "owner": owner,
                    "type": type,
                    "modified_day": dt.strftime("%d"),
                    "modified_month": dt.strftime("%b"),
                    "modified_year": dt.strftime("%Y"),
                    # "preview_available": preview_availible,
                }
            )

        entries.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))

        return await render_template(
            "public/dir.html",
            display_path=str(display_path),
            parent_path=str(parent_path),
            entries=entries,
            mode=mode,
        )
    elif os.path.isfile(realpath):
        return await send_file(realpath)
    else:
        abort(404)


@app.get("/admin/")
async def admin() -> Response | str:
    session = await authenticate_user()
    if session is None:
        return await login_response()
    if not session.is_admin:
        abort(403)

    passwords = await db.get_passwords()
    await db.get_logins()
    return await render_template("admin.html", passwords=[asdict(p) for p in passwords])


@app.post("/admin/password")
async def admin_password() -> Response:
    session = await authenticate_user()
    if session is None:
        return await login_response()

    form = await request.form
    password = form.get("password")
    if password is None:
        abort(400)
    access_level = form.get("access_level")
    if access_level is None:
        abort(400)

    await db.add_password(password, int(access_level))
    return await make_response(redirect(url_for("admin")))


@app.before_serving
async def init():
    await db.init()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
