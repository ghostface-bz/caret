"""Deliberately vulnerable sample app — used to verify the scanner pipeline.
DO NOT deploy. Every issue here is intentional so gitleaks/semgrep/trivy have something
to find: a hard-coded secret, a SQL injection, and a command injection.
"""
import os
import sqlite3
import subprocess

import flask

app = flask.Flask(__name__)

# gitleaks: hard-coded credential (CWE-798)
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DB_PASSWORD = "SuperSecret123!"


@app.route("/user")
def get_user():
    # semgrep: SQL injection via string formatting (CWE-89 / A03 Injection)
    uid = flask.request.args.get("id")
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = '%s'" % uid)
    return str(cur.fetchall())


@app.route("/ping")
def ping():
    # semgrep: command injection via shell=True (CWE-78)
    host = flask.request.args.get("host")
    out = subprocess.check_output("ping -c1 " + host, shell=True)
    return out


if __name__ == "__main__":
    # semgrep: debug=True in production (CWE-489)
    app.run(host="0.0.0.0", debug=True)
