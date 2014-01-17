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

app = Flask(settings_loader.APPNAME, template_folder = "../templates/")

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
   context = {"message": "feck yis", "debug": app.debug}
   #return template.render(context)
   return render_template('index.html', **context)

class LoginForm(Form):
   username = TextField('Username', [validators.Length(min = 1, max = 64)])
   password = PasswordField('Password', [validators.Length(min = 0, max = 64)])

@app.route("/login/", methods = ["POST"])
def login():
   form = LoginForm(request.form)
   if form.validate():
      print form.username.data
      print form.password.data
      if utils.validate_user(form.username.data, form.password.data):
         session['uid'] = form.username.data
   #else:
      #flash("waf")
   return redirect("/")

@app.route("/logout/", methods = ["GET"])
def logout():
   session.clear()
   return redirect("/")
 
if __name__ == "__main__":
   app.run()

