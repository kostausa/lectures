from seminar import app

app.secret_key = 'dldntEhekfmsdnfl'
app.config.update(
  DEBUG=True,
  YEAR=2012,
  SECRET="gkskslaskfk",
  SQLALCHEMY_DATABASE_URI='mysql://web:tiffha@localhost/kosta',
  ADMINPASS="gkskslaskfk",
  SMTPPASS="gkskslaskfk"
)