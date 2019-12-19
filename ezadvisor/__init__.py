from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import create_engine

#this program defines what symbols the EZAdvisor package is resolving

#create an app object
app = Flask(__name__)

ENV = 'prod'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password123@localhost:5433/ezadvisor'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://kznakoeaqlmggn:4673053b035ad924eed4e8b8bdc0a4ebe2b58c5f3950328e6b6f8e62f1e2498d@ec2-174-129-234-111.compute-1.amazonaws.com:5432/d9iog9eqi4gkmn'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '99cc3d4722f75100d23302806c98e61'


#create the database object
db = SQLAlchemy(app)

#create the login sub system
login = LoginManager(app)

# If a user who is not logged in tries to view a protected page, 
# Flask-Login will automatically redirect the user to the login form
login.login_view = 'login'

from ezadvisor import routes, data