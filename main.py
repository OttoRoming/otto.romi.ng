import os
import subprocess

from flask import Flask, abort, render_template

app = Flask(__name__)


@app.get("/")
def index() -> str:
    quote = subprocess.run(["fortune", "-l"], capture_output=True, text=True).stdout

    return render_template("index.html", quote=quote)


@app.get("/public/", defaults={"path": ""})
@app.get("/public/<path:path>")
def public(path: str = "") -> str:
    abort(501, "This page is under construction. 🚨🚨🚨🚨🚨")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=1502)
