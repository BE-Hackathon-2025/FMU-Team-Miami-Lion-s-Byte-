# from flask import Flask
# app = Flask(__name__)
# @app.route('/')
# def home():
#     return "Sup, Berry!"

from app import app as application


if __name__ == '__main__':
    application.run(debug=True)