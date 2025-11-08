# from flask import Flask
# app = Flask(__name__)
# @app.route('/')
# def home():
#     return "Sup, Berry!"

from flask import Flask, render_template

app = Flask(__name__)                       

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return "The About Page!"

if __name__ == '__main__':
    app.run(debug=True)