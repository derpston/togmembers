# stdlib
import os

# This app
import utils
import settings_loader
from utils import page

# Third party
from flask import Flask, request, session, redirect, flash, render_template
from wtforms import Form, BooleanField, TextField, PasswordField, validators
import jinja2

app = Flask(settings_loader.APPNAME, template_folder = "../templates/", static_folder = "../static")

if __name__ == "__main__":
   # Bit of a hack to get this extra path into the settings_loader module
   # and work around the way flask imports it, which is a complete reload.
   # This has to happen here because settings_loader can't detect when
   # we're run as __main__, which is a good indicator of a dev environment.
   os.environ['EXTRA_CONFIG_PATHS'] = "conf/dev.yaml"

# Load all the configs.
app.config.from_pyfile("settings_loader.py")

# Push a reference to the config into the utils module.
utils.config = app.config

@app.route("/")
def index():
   if 'uid' in session:
      return redirect("/members/")
   else:
      return redirect("/login/")

class LoginForm(Form):
   username = TextField('Username', [validators.Length(min = 1, max = 64)])
   password = PasswordField('Password', [validators.Length(min = 0, max = 64)])

@app.route("/login/", methods = ["GET"])
def login_form():
   context = {}
   return render_template('login.html', **context)

@app.route("/login/", methods = ["POST"])
def login_submit():
   form = LoginForm(request.form)
   if form.validate() and utils.validate_user(form.username.data, form.password.data):
      # Log the user in.
      session['uid'] = form.username.data
      return render_template('login_redirect.html')
   else:
      flash("Incorrect username and/or password.")
      return redirect("/login/")

@app.route("/logout/", methods = ["GET"])
def logout():
   session.clear()
   return redirect("/")
   
if __name__ == "__main__":
   app.run()

