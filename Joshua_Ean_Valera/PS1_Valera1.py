from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    greeting = ""
    if request.method == 'POST':
        name = request.form['name']
        greeting = f"Hello World! {name}, welcome to CCCS 106 - Applications Development and Emerging Technologies."
    return render_template('index.html', greeting=greeting)

if __name__ == '__main__':
    app.run(debug=True)
