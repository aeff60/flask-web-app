from flask import Flask, request, render_template

app = Flask(__name__)

# @app.route('/')
# def home():
#     return "Hello, Flask!"

@app.route('/')
def home():
    return render_template('index.html', title="Home Page", heading="Welcome to My Website", content="This is the home page content.")


@app.route('/about')
def about():
    return "This is the about page"

def about():
    return "This is the more page"

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    return f"Hello, {name}!"

if __name__ == '__main__':
    app.run(debug=True)
