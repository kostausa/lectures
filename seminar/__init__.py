import hashlib
import smtplib
from email.mime.text import MIMEText

from flask import Flask, jsonify, request, session, redirect, make_response
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)

import seminar.config
import seminar.views

if __name__ == "__main__":
    app.run()


