from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import datetime
import re
import mysql.connector
from jinja2 import Environment, FileSystemLoader, select_autoescape
from urllib.parse import parse_qs
import os
import secrets

env = Environment(loader=FileSystemLoader("./templates/"))
# Replace these with your MySQL database credentials
MYSQL_CONFIG = {
    "user": os.environ["user"],
    "password": os.environ["password"],
    "host": os.environ["host"],
    "port": os.environ["port"],
    "database": os.environ["database"],
}

def validate(data: dict) -> dict:
    errors = {}

    # Validate name
    if not data.get("name") or not re.match(
        "^[A-ZА-Я][a-zа-я]+(\\s[A-ZА-Я][a-zа-я]+){1,2}$", data["name"]
    ):
        errors["name"] = "Invalid name, name can consist of chars A-Z, А-Я"

    # Validate number
    if not data.get("number") or not re.match(
        "^\\+[1-9]{1}[0-9]{3,14}$", data["number"]
    ):
        errors["number"] = (
            "Invalid number, number must consist of digits 0-9 and + at start"
        )
    # Validate email
    if not data.get("email") or not re.match("[^@]+@[^@]+\.[^@]+", data["email"]):
        errors["email"] = "Invalid email, email must consist @ and ."

    # Validate sex
    if not data.get("sex") or data["sex"].lower() not in ["on", "off"]:
        errors["sex"] = "Invalid sex: Male or Female required"

    # Validate fav_lang
    if not data.get("fav_lang"):
        errors["fav_lang"] = "Favorite language is required"

    # Validate bio
    if not data.get("bio"):
        errors["bio"] = "Bio is required"

    return errors


class HttpProcessor(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers", "X-Requested-With, Content-type"
        )

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        print(post_data)
        data = parse_qs(post_data.decode("utf-8"))
        data = {key: value[0] for key, value in data.items() if value}

        print(post_data, data)
        cnx = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = cnx.cursor()

        errors = validate(data)
        # Cookies!
        secret_key = secrets.token_urlsafe(16)

        # Set the cookie with error information and secret key
        cookie_value = json.dumps({"errors": errors, "secret": secret_key})
        print(cookie_value)


        # Jinja
        template = env.get_template("index.html")
        output = template.render(errors=errors, data=data)

        if errors:
            self.send_response(400)  # Bad Request
            self.send_cors_headers()
            self.send_header("Set-Cookie", f"errors={cookie_value}; Path=/; HttpOnly")  # Expires in session
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(output.encode("utf-8"))
            return

        query = "INSERT INTO application (name, phone, email, birthday, sex, fav_lang, bio) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(
            query,
            (
                data["name"],
                data["number"],
                data["email"],
                data["birthday"],
                data["sex"],
                data["fav_lang"],
                data["bio"],
            ),
        )

        # Commit the changes and close the connection
        cnx.commit()
        cursor.close()
        cnx.close()

        # Send a response back to the client
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Set-Cookie", f"errors=; Path=/; Expires=Thu, 01 Jan 2025 00:00:00 GMT; HttpOnly")  # Expires in 1 year
        # Set new cookie with form data
        cookie_value = json.dumps(data)
        self.send_header("Set-Cookie", f"data={cookie_value}; Path=/; Max-Age=31536000; HttpOnly") # Save data for 1 yr
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(output.encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_cors_headers()
        cookie_data = self.headers.get("Cookie")
        errors = {}
        secret_key = None
        if cookie_data:
            try:
                # Extract error data and secret key from cookie
                cookie_dict = json.loads(cookie_data.split("=")[1])
                errors = cookie_dict["errors"]
                secret_key = cookie_dict["secret"]
            except json.JSONDecodeError:
                pass  # Invalid cookie format, ignore
        # Jinja
        template = env.get_template("index.html")
        output = template.render(errors={}, data={})

        # Send response
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(output.encode("utf-8"))


# Set up the server
serv = HTTPServer(("0.0.0.0", 3307), HttpProcessor)
serv.serve_forever()
