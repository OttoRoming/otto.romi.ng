import os
import pickle
import subprocess
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

STORE_FILENAME = "store.pickle"


# https://stackoverflow.com/questions/41505448/is-python-uuid-uuid4-strong-enough-for-password-reset-links
def uuid4():
    """Generate a cryptographically secure random UUID."""
    return UUID(bytes=os.urandom(16), version=4)


class SessionStore:
    def __init__(self) -> None:
        self.sessions: set[UUID] = set()

    def dump(self) -> None:
        with open(STORE_FILENAME, "wb") as f:
            pickle.dump(self, f)

    def new_session(self) -> UUID:
        session = uuid4()
        self.sessions.add(session)

        self.dump()
        return session

    def is_session_valid(self, session: UUID) -> bool:
        return session in self.sessions


app = Flask(__name__)
store: SessionStore

try:
    with open(STORE_FILENAME, "rb") as f:
        store = pickle.load(f)
except FileNotFoundError:
    store = SessionStore()

load_dotenv()
PASSWORD = os.getenv("PASSWORD")


def generate_context(other: dict[str, Any] = {}) -> dict[str, Any]:
    fortune = subprocess.run(["fortune"], capture_output=True, text=True).stdout

    return {"fortune": fortune, **other}


@app.get("/")
def index() -> str:
    context = generate_context()

    return render_template("index.html", **context)


@app.get("/login")
def login() -> str:
    context = generate_context()
    return render_template("login.html", **context)


@app.post("/login")
def login_post() -> Response:
    password = request.form.get("password")

    print(password, PASSWORD)
    if password != PASSWORD:
        abort(401)

    session = store.new_session()

    response = make_response(redirect(url_for("public")))
    response.set_cookie("session", str(session))
    return response


@app.get("/public/", defaults={"path": ""})
@app.get("/public/<path:path>")
def public(path: str = "") -> Response | str:
    session = request.cookies.get("session")
    if session is None or not store.is_session_valid(UUID(session)):
        return make_response(redirect(url_for("login")))

    # https://en.wikipedia.org/wiki/Directory_traversal_attack
    if ".." in path:
        abort(400)

    entries = []
    home = os.getenv("HOME")
    realpath = f"{home}/shared/public/{path}"

    if os.path.isdir(realpath):
        for entry in os.scandir(realpath):
            if entry.name == ".busig":
                response = make_response()
                response.status_code = 402
                return response

            type = ""
            if entry.is_symlink():
                type = "symlink"
            elif entry.is_file():
                type = "file"
            elif entry.is_dir():
                type = "dir"

            entries.append({"type": type, "name": entry.name})

        context = generate_context({"path": path, "entries": entries})
        return render_template("public.html", **context)
    elif os.path.isfile(realpath):
        return send_file(realpath)
    else:
        abort(404)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=61000)
