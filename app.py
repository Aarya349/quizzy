from flask import Flask
from dotenv import load_dotenv
import os

#app initialize
app = Flask(__name__)

#load environment variable
load_dotenv()

#app configure
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

import routes
import crud_routes
import models

if __name__ == '__main__':
    app.run(debug=True)