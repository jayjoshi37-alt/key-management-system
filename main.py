from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from utils.key_generator import generate_api_key
from flask import jsonify
import requests
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

# MySQL Config
app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")

app.config['MYSQL_PORT'] = int(
    os.getenv("MYSQL_PORT")
)

app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")

app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")

app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")

mysql = MySQL(app)

# LOGIN ROUTE
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        query = """
        SELECT * FROM admin
        WHERE email=%s AND password=%s
        """

        cur.execute(query, (email, password))

        admin = cur.fetchone()

        cur.close()

        if admin:

            session['admin_logged_in'] = True

            return redirect('/dashboard')

        else:
            return "Invalid Email or Password"

    return render_template('login.html')


# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'admin_logged_in' in session:

        cur = mysql.connection.cursor()

        query = """

        SELECT

            projects.*,

            COUNT(DISTINCT usage_logs.mac_address)
            AS total_users

        FROM projects

        LEFT JOIN usage_logs

        ON projects.id = usage_logs.project_id

        GROUP BY projects.id

        """

        cur.execute(query)

        projects = cur.fetchall()
        print(projects)
        cur.close()

        return render_template(
            'dashboard.html',
            projects=projects
        )

    return redirect('/')


@app.route('/add-project', methods=['GET', 'POST'])
def add_project():

    if 'admin_logged_in' not in session:
        return redirect('/')

    if request.method == 'POST':

        project_name = request.form['project_name']

        api_key = generate_api_key()

        cur = mysql.connection.cursor()

        query = """
        INSERT INTO projects(project_name, api_key)
        VALUES(%s, %s)
        """

        cur.execute(query, (project_name, api_key))

        mysql.connection.commit()

        cur.close()

        return redirect('/dashboard')

    return render_template('add_project.html')


@app.route('/block-project/<int:id>')
def block_project(id):

    if 'admin_logged_in' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()

    query = """
    UPDATE projects
    SET status='Blocked'
    WHERE id=%s
    """

    cur.execute(query, (id,))

    mysql.connection.commit()

    cur.close()

    return redirect('/dashboard')


@app.route('/unblock-project/<int:id>')
def unblock_project(id):

    if 'admin_logged_in' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()

    query = """
    UPDATE projects
    SET status='Active'
    WHERE id=%s
    """

    cur.execute(query, (id,))

    mysql.connection.commit()

    cur.close()

    return redirect('/dashboard')


@app.route('/delete-project/<int:id>')
def delete_project(id):

    if 'admin_logged_in' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()

    query = """
    DELETE FROM projects
    WHERE id=%s
    """

    cur.execute(query, (id,))

    mysql.connection.commit()

    cur.close()

    return redirect('/dashboard')


@app.route('/verify-key', methods=['POST'])
def verify_key():

    data = request.get_json()

    api_key = data.get('api_key')
    mac_address = data.get('mac_address')
    device_info = data.get('device_info')

    # USER IP

    ip_address = request.remote_addr

    # LOCATION FETCH

    try:

        response = requests.get(
            f"http://ip-api.com/json/{ip_address}"
        )

        location_data = response.json()

        location = (
            f"{location_data.get('city')}, "
            f"{location_data.get('country')}"
        )

    except:

        location = "Unknown"

    cur = mysql.connection.cursor()

    # CHECK KEY

    query = """
    SELECT * FROM projects
    WHERE api_key=%s
    """

    cur.execute(query, (api_key,))

    project = cur.fetchone()

    # INVALID KEY

    if not project:

        cur.close()

        return jsonify({
            "status": "error",
            "message": "Invalid API Key"
        })

    # BLOCKED KEY

    if project[3] == 'Blocked':

        cur.close()

        return jsonify({
            "status": "error",
            "message": "API Key Blocked"
        })

    # UPDATE LAST USED

    update_query = """
    UPDATE projects
    SET last_used=NOW()
    WHERE id=%s
    """

    cur.execute(update_query, (project[0],))

    # INSERT LOG

    insert_log = """
    INSERT INTO usage_logs
    (
        project_id,
        ip_address,
        mac_address,
        location,
        device_info
    )

    VALUES(%s,%s,%s,%s,%s)
    """

    cur.execute(insert_log, (

        project[0],
        ip_address,
        mac_address,
        location,
        device_info

    ))

    mysql.connection.commit()

    cur.close()

    return jsonify({

        "status": "success",
        "message": "API Key Verified",
        "project_name": project[1]

    })


# LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)