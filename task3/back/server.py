from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import datetime
import re
import mysql.connector

# Replace these with your MySQL database credentials
MYSQL_CONFIG = {
    "user": "my_user",
    "password": "123",
    "host": "db",
    # "host": "0.0.0.0",
    "port": "3306",
    "database": "my_db",
}


def validate(data: dict) -> dict:
    errors = {}

    # Validate name
    if not data.get("name") or not re.match(
        "^[A-ZА-Я][a-zа-я]+(\\s[A-ZА-Я][a-zа-я]+){1,2}$", data["name"]
    ):
        errors["name"] = "Invalid name"

    # Validate number
    if not data.get("number") or not re.match(
        "^\\+[1-9]{1}[0-9]{3,14}$", data["number"]
    ):
        errors["number"] = "Invalid number"

    # Validate email
    if not data.get("email") or not re.match("[^@]+@[^@]+\.[^@]+", data["email"]):
        errors["email"] = "Invalid email"

    # Validate sex
    if not data.get("sex") or data["sex"].lower() not in ["on", "off"]:
        errors["sex"] = "Invalid sex: on or off required"

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
        data = json.loads(post_data)

        cnx = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = cnx.cursor()

        errors = validate(data)
        if errors:
            self.send_response(400)  # Bad Request
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "errors": errors}).encode())
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
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success"}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_cors_headers()

        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write("Hey!".encode())


# Set up the server
serv = HTTPServer(("0.0.0.0", 3307), HttpProcessor)
serv.serve_forever()
