from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Flask!"

@app.route('/about')
def about():
    return "This is the about page"

@app.route('/more')
def about():
    return "This is the more page"

if __name__ == '__main__':
    app.run(debug=True)
