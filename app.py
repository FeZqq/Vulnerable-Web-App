import json
import os
import sqlite3
import subprocess
import platform
import re
import html
from flask import Flask, request, render_template, redirect, url_for, session,render_template_string
import base64
import requests


app = Flask(__name__)
app.secret_key = "secret_key"

COMMENTS_FILE = "comments.json"

def get_user_by_credentials(username, password):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id ,username ,password , email, credit_card FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def load_comments():
    if not os.path.exists(COMMENTS_FILE):
        return {"level1": [], "level2": []}
    with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_comments(comments):
    with open(COMMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

def get_products():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, name, category FROM products")
    products = c.fetchall()
    conn.close()
    return [
        {"id": p[0], "name": p[1], "category": p[2], "price": 10 + p[0]*3}
        for p in products
    ]

@app.route('/')
def ssti():
    title = request.args.get('title')

    if not title:
        return redirect('/?title=Welcome to the Vulnerable Web App')

    with open("templates/layout.html") as f:
        layout = f.read()

    vulnerable_page = layout.replace('{% block content %}{% endblock %}', f"""
        <h2 class="text-center">{title}</h2>
        <p class="text-center text-muted">This page is vulnerable to SSTI.</p>
    """)

    return render_template_string(vulnerable_page)

    return render_template_string(vulnerable_page)
@app.route('/clear_comments', methods=['POST'])
def clear_comments():
    comments = load_comments()         
    comments["level1"] = []           
    comments["level2"] = []           
    save_comments(comments)           
    return redirect(request.referrer or url_for('index'))  


@app.route('/XSS/level/1', methods=['GET', 'POST'])
def XSS_level1():
    comments = load_comments()
    if request.method == 'POST':
        comment = request.form.get('comment', '')
        comments['level1'].append(comment)
        save_comments(comments)
        return redirect(url_for('XSS_level1'))
    return render_template('XSS_level1.html', comments=comments['level1'])

@app.route('/XSS/level/2', methods=['GET', 'POST'])
def XSS_level2():
    comments = load_comments()
    if request.method == 'POST':
        raw = request.form.get('comment', '')
        decoded = html.unescape(raw)

        blocked = ['<', '>', '"', "'"]
        if any(char in raw for char in blocked):
            comment = "🚫 Blocked by WAF"
        else:
            comment = decoded
        comments['level2'].append(comment)
        save_comments(comments)
        return redirect(url_for('XSS_level2'))
    return render_template('XSS_level2.html', comments=comments['level2'])

@app.route('/SQLi/level/1', methods=['GET', 'POST'])
def sqli_level1():
    results = []
    query = request.args.get('q', '')
    if query:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            sql = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
            cursor.execute(sql)
            results = cursor.fetchall()
        except Exception as e:
            results = []
        conn.close()
    return render_template('SQLi_level1.html', results=results)

@app.route('/SQLi/level/2', methods=['GET', 'POST'])
def sqli_level2():
    result = None
    query = request.args.get('id', '')
    if query:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            sql = f"SELECT * FROM products WHERE id = {query}"
            cursor.execute(sql)
            row = cursor.fetchone()
            if row:
                result = "Product exists!"
            else:
                result = "No product found."
        except Exception as e:
            result = "Error in query."
        conn.close()
    return render_template('SQLi_level2.html', result=result)

@app.route('/OSCMD/level/1', methods=['GET', 'POST'])
def oscmd_level1():
    output = None
    ip = ''
    if request.method == 'POST':
        ip = request.form.get('ip', '')
        try:
            if platform.system().lower().startswith('win'):
                    ping_cmd = f"ping -n 2 {ip}"
            else:
                    ping_cmd = f"ping -c 2 {ip}"
            output = subprocess.getoutput(ping_cmd)
        except Exception as e:
            output = f"Error: {e}"
    return render_template('oscmd_level1.html', output=output, ip=ip)

@app.route('/OSCMD/level/2', methods=['GET', 'POST'])
def oscmd_level2():
    output = None
    ip = ''
    if request.method == 'POST':
        ip = request.form.get('ip', '')
        if re.match(r'^[0-9]', ip) and ' ' not in ip and len(ip) <= 30:
            try:
                if platform.system().lower().startswith('win'):
                    ping_cmd = f"ping -n 2 {ip}"
                else:
                    ping_cmd = f"ping -c 2 {ip}"
                output = subprocess.getoutput(ping_cmd)
            except Exception as e:
                output = f"Error: {e}"
        else:
            output = "Invalid IP address format!"
    return render_template('oscmd_level2.html', output=output, ip=ip)


@app.route('/IDOR/login_1', methods=['GET', 'POST'])
def login1():
    error = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user_by_credentials(username, password)
        if user:
            return redirect(url_for('idor_level1') + f'?id={user[0]}')
        else:
            error = "Invalid credentials"
    return render_template('login.html', error=error)

@app.route('/IDOR/login_2', methods=['GET', 'POST'])
def login2():
    error = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user_by_credentials(username, password)
        if user:
            encoded_id = base64.b64encode(str(user[0]).encode()).decode()
            return redirect(url_for('idor_level2') + f'?id={encoded_id}')
        else:
            error = "Invalid credentials"
    return render_template('login.html', error=error)

@app.route('/IDOR/level/1', methods=['GET', 'POST'])
def idor_level1():
    id = request.args.get('id', '')
    try:
        user = get_user_by_id(id)
        if user:
            return render_template(
                'idor.html',
                id=user[0],
                username=user[1],
                password=user[2],
                email=user[3],
                credit_card=user[4]
            )
        else:
            return "User not found", 404
    except Exception as e:
        return f"Invalid ID: {str(e)}", 400
    
@app.route('/IDOR/level/2', methods=['GET'])
def idor_level2():
    encoded_id = request.args.get('id', '')
    try:
        decoded_id = base64.b64decode(encoded_id).decode()
        user = get_user_by_id(decoded_id)
        if user:
            return render_template(
                'idor.html',
                id=user[0],
                username=user[1],
                password=user[2],
                email=user[3],
                credit_card=user[4]
            )
        else:
            return "User not found", 404
    except Exception as e:
        return f"Invalid ID: {str(e)}", 400
@app.route('/Businesslogic', methods=['GET', 'POST'])
def businesslogic():
    if 'cart' not in session:
        session['cart'] = []
    products = get_products()
    cart = session['cart']

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            product_id = int(request.form.get('product_id'))
            name = request.form.get('name')
            price = float(request.form.get('price'))
            quantity = int(request.form.get('quantity'))
            session['cart'].append({
                "product_id": product_id,
                "name": name,
                "price": price,
                "quantity": quantity
            })
            session.modified = True
            return redirect(url_for('businesslogic'))
        elif action == 'checkout':
            session['cart'] = []
            session.modified = True
            return render_template('businesslogic.html', products=products, cart=[], total=0, message="Order completed! Cart is now empty.")

    total = sum(float(item['price']) * int(item['quantity']) for item in cart)
    return render_template('businesslogic.html', products=products, cart=cart, total=total, message=None)

@app.route('/aggrements', methods=['GET', 'POST'])
def aggrements():
    return render_template('aggrements.html')

@app.route('/SSRF', methods=['GET', 'POST'])
def ssrf():
    if request.method == 'POST':
        target_url = request.form.get('url')
        if not target_url:
            return "No URL provided.", 400
        try:
            resp = requests.get(target_url, timeout=5)
            return resp.text   
        except Exception as e:
            return f"Error: {e}", 500

    return render_template('ssrf.html')


if __name__ == '__main__':
    app.run(debug=True,host="127.0.0.1",port=5000)