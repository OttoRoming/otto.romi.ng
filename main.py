import os
import pickle
import subprocess
from pathlib import Path
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    abort,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.exceptions import HTTPException

STORE_FILENAME = "store.pickle"


# https://stackoverflow.com/questions/41505448/is-python-uuid-uuid4-strong-enough-for-password-reset-links
def uuid4():
    """Generate a cryptographically secure random UUID."""
    return UUID(bytes=os.urandom(16), version=4)


class SessionStore:
    def __init__(self) -> None:
        self.sessions: dict[UUID, int] = {}

    def dump(self) -> None:
        with open(STORE_FILENAME, "wb") as f:
            pickle.dump(self, f)

    def new_session(self, level: int) -> UUID:
        session = uuid4()
        self.sessions[session] = level

        self.dump()
        return session

    def remove_session(self, session: UUID | None = None) -> None:
        if session is None:
            session_str = request.cookies.get("session")
            if session_str is None:
                return None

            session = UUID(session_str)

        del self.sessions[session]

    def get_access_level(self, session: UUID | None = None) -> int | None:
        if session is None:
            session_str = request.cookies.get("session")
            if session_str is None:
                return None

            session = UUID(session_str)

        return self.sessions.get(session)


app = Flask(__name__)
store: SessionStore

try:
    with open(STORE_FILENAME, "rb") as f:
        store = pickle.load(f)
except FileNotFoundError:
    store = SessionStore()

load_dotenv()

password_access_levels: dict[str | None, int] = {
    os.getenv("PASSWORD1"): 1,
    os.getenv("PASSWORD2"): 2,
}


def generate_context(other: dict[str, Any] = {}) -> dict[str, Any]:
    access_level = store.get_access_level()
    logged_in = access_level is not None

    return {
        "logged_in": logged_in,
        "access_level": access_level,
        **other,
    }


@app.errorhandler(HTTPException)
def error(error: HTTPException) -> str:

    context = generate_context({"code": error.code, "name": error.name})
    return render_template("error.html", **context)


@app.get("/")
def index() -> str:
    context = generate_context()

    return render_template("index.html", **context)


@app.get("/login/", defaults={"path": ""})
@app.get("/login/<path:path>")
def login(path: str) -> str:
    context = generate_context()
    return render_template("login.html", **context)


@app.post("/login/", defaults={"path": ""})
@app.post("/login/<path:path>")
def login_post(path: str) -> Response:
    password = request.form.get("password")
    if password is None:
        abort(400)

    access_level = password_access_levels.get(password)
    if access_level is None:
        abort(401)

    session = store.new_session(access_level)

    response = make_response(redirect(url_for("public", path=path)))
    response.set_cookie("session", str(session))
    return response


@app.get("/signout")
def signout() -> Response:
    response = make_response(redirect(url_for("index")))
    response.delete_cookie("session")

    return response


@app.get("/public/", defaults={"path": ""})
@app.get("/public/<path:path>")
def public(path: str = "") -> Response | str:
    login_response = make_response(redirect(url_for("login", path=path)))

    session = request.cookies.get("session")
    if session is None:
        return login_response

    access_level = store.get_access_level(UUID(session))
    if access_level is None:
        return login_response

    # https://en.wikipedia.org/wiki/Directory_traversal_attack
    if ".." in path:
        abort(400)

    entries = []
    home = os.getenv("HOME")
    # realpath = f"{home}/shared/public/{path}"

    p = Path(f"{home}/shared/public")
    realpath = p / path
    display_path = Path(path)
    parent_path = display_path.parent

    if os.path.isdir(realpath):
        for entry in os.scandir(realpath):
            if entry.name == ".confidential" and access_level < 2:
                abort(451)
                # response = make_response()
                # response.status_code = 402
                # return response

            type = ""
            if entry.is_symlink():
                type = "symlink"
            elif entry.is_file():
                type = "file"
            elif entry.is_dir():
                type = "dir"

            entries.append({"type": type, "name": entry.name})

        entries.sort(key=lambda e: e["name"])
        context = generate_context(
            {
                "display_path": str(display_path),
                "parent_path": str(parent_path),
                "entries": entries,
            }
        )
        return render_template("public/dir.html", **context)
    elif os.path.isfile(realpath):
        return send_file(realpath)
    else:
        abort(404)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=61000)
