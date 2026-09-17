import os
from flask import Flask, render_template, request

app = Flask(__name__)

# INTENTIONAL FLAW (for Gitleaks demo) - remove before final commit,
# see SECURITY.md for the remediation writeup.
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    if request.method == 'POST':
        name = request.form.get('name', 'friend')
        message = f'Hello, {name}! Welcome to the DevSecOps demo.'
    return render_template('index.html', message=message)

@app.route('/healthz')
def healthz():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)