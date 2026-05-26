import os
import subprocess

from flask import Flask, abort, render_template

app = Flask(__name__)


@app.get("/")
def index() -> str:
    quote = subprocess.run(["fortune", "-l"], capture_output=True, text=True).stdout

    return render_template("index.html", quote=quote)


@app.get("/books/<book>")
def book(book: str) -> str:
    for name in os.listdir("books"):
        if name == book:
            break
    else:
        return abort(404)

    quote = subprocess.run(["fortune", "-l"], capture_output=True, text=True).stdout

    text = ""
    with open(f"books/{book}") as f:
        text = f.read()

    return render_template("book.html", quote=quote, text=text)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
