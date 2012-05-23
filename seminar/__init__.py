import hashlib
import smtplib
from email.mime.text import MIMEText

from flask import Flask, jsonify, request, session, redirect, make_response
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'dldntEhekfmsdnfl'

app.config.update(
  DEBUG=True,
  YEAR=2012,
  SECRET="gkskslaskfk",
  SQLALCHEMY_DATABASE_URI='mysql://web:tiffha@localhost/kosta',
  ADMINPASS="gkskslaskfk"
)
db = SQLAlchemy(app)

import seminar.views

if __name__ == "__main__":
    app.run()


