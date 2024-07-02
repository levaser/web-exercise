import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie, Morsel
import json
from datetime import datetime, timedelta
import re
import mysql.connector
from jinja2 import Environment, FileSystemLoader, select_autoescape
from urllib.parse import parse_qs
from utils import *
import os
import secrets
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass

class FormCRUD:
    """CRUD"""
    @staticmethod
    def form_page_post(handler, cursor, cnx, env):
        """Method for posting"""
        FormCRUD.form_create_or_update(handler, cursor, cnx, env, CreateVariant)

    @staticmethod
    def form_page_update(handler, cursor, cnx, env, Id):
        """Method for updating"""
        FormCRUD.form_create_or_update(handler, cursor, cnx, env, UpdateVariant(Id))

    @staticmethod
    def form_page_get(handler, cursor, cnx, env):
        FormCRUD.form_page_get_aux(handler, cursor, cnx, env, None)

    @staticmethod
    def form_page_get_exact(handler, cursor, cnx, env, Id):
        FormCRUD.form_page_get_aux(handler, cursor, cnx, env, Id)

    @staticmethod
    def login_page_get(handler, env):
        """get login page form"""
        handler.send_response(200)
        handler.send_cors_headers()

        cookie_raw = handler.headers.get("Cookie")
        cookie = SimpleCookie()
        if cookie_raw is not None:
            cookie.load(cookie_raw)

        rec = get_cookie(cookie)
        user = rec.get("user")
        template = env.get_template("login.html")
        output = None
        if bool(user):
            # Already
            output = template.render(logined=True, user=user, login_errors = {})
        else:
            # Not Yet
            output = template.render(logined=False, user={}, login_errors = {})


        handler.send_header("Content-Type", "text/html")
        handler.end_headers()
        handler.wfile.write(output.encode("utf-8"))

    @staticmethod
    def login_page_post(handler, cursor, cnx, env):
        """LOGIN"""
        cookie = SimpleCookie()
        template = env.get_template("login.html")
        content_length = int(handler.headers["Content-Length"])
        post_data = handler.rfile.read(content_length)
        print(post_data)
        data = parse_qs(post_data.decode("utf-8"))
        data = {key: value[0] for key, value in data.items() if value}

        login_errors = {}
        print(data)
        if "username" in data and "password" in data:
            user = User(data["username"], data["password"])
            if User.check_in_db(user, cursor, cnx):
                expires = datetime.utcnow() + timedelta(days=360) # expires in 30 days
                cookie["session"] = str(uuid.uuid4())
                cookie["session"]["path"] = "/"
                cookie["session"]["expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")

                cookie["user"] = json.dumps(user.to_dict())
                cookie["user"]["path"] = "/"

                handler.send_response(200)
                handler.send_cors_headers()
                handler.send_header("Content-Type", "text/html")
                handler.send_header("Set-Cookie", cookie["session"].output(header=""))
                handler.send_header("Set-Cookie", cookie["user"].output(header=""))
                handler.end_headers()
                output = template.render(logined=True, user=user, login_errors={})
                handler.wfile.write(output.encode("utf-8"))
                return
            else:
                login_errors = {"auth_err": "wrong password or username"}
        else:
            login_errors = {"auth_err": "wrong password or username"}

        output = template.render(logined=False, user = {}, login_errors=login_errors)

        cookie["login_errors"] = json.dumps(login_errors)
        cookie["login_errors"]["path"] = "/login"

        handler.send_response(400)
        handler.send_header("Content-Type", "text/html")
        handler.send_header("Set-Cookie", cookie["login_errors"].output(header=""))
        handler.end_headers()

        handler.wfile.write(output.encode("utf-8"))

    @staticmethod
    def form_list_get(handler, cursor, cnx, env):
        """get list of pages"""
        handler.send_response(200)
        handler.send_cors_headers()


        template = env.get_template("list.html")
        cookie_raw = handler.headers.get("Cookie")
        cookie = SimpleCookie()
        if cookie_raw is not None:
            cookie.load(cookie_raw)

        rec = get_cookie(cookie)
        user_rec = rec.get("user")

        output = None

        if bool(user_rec):
            user = User(user_rec["username"], user_rec["password"])
            query = "SELECT * FROM application WHERE user_id = %s"
            cursor.execute(query, (UserORM(user, cursor, cnx).get_id(),))
            cards = cursor.fetchall()
            print(cards)
            output = template.render(logined = True, user = user, cards = cards)
        else:
            output = template.render(logined = False, user = {}, cards = [])

        handler.send_header("Content-Type", "text/html")
        handler.end_headers()
        handler.wfile.write(output.encode("utf-8"))

    @staticmethod
    def form_create_or_update(handler, cursor, cnx, env, variant: FormVariants):
        """This function change behaviour based on flag to creat or update form"""
        template = env.get_template("index.html")
        path = handler.path
        print(path)
        # Create user and add it to session
        # (If it's not already created)
        rawc = handler.headers.get("Cookie")
        cookie = SimpleCookie()
        if rawc is not None:
            cookie.load(rawc)


        output = template.render(errors={}, data={}, user={}, path=path)

        content_length = int(handler.headers["Content-Length"])
        post_data = handler.rfile.read(content_length)
        print(post_data)
        data = parse_qs(post_data.decode("utf-8"))
        data = {key: value[0] for key, value in data.items() if value}


        print(post_data, data)

        errors = Form.validate(data)

        # Cookies!
        secret_key = secrets.token_urlsafe(16)

        # Set the cookie with error information and secret key
        cookie_value = json.dumps({"errors": errors, "secret": secret_key})
        print(cookie_value)

        user = {}
        if "user" in cookie:
            user_d = json.loads(cookie["user"].value)
            user = User(user_d["username"],
                        user_d["password"])
        else:
            user = User.generate_user()


        if errors:
            output = template.render(errors=errors, data=data, user={}, path=path)
            handler.send_response(400)  # Bad Request
            handler.send_cors_headers()
            cookie["errors"] = cookie_value
            # handler.send_header("Set-Cookie", f"errors={cookie_value}; Path=/; HttpOnly")  # Expires in session
            handler.send_header("Set-Cookie", cookie.output(header=""))
            handler.send_header("Content-Type", "text/html")
            handler.end_headers()
            handler.wfile.write(output.encode("utf-8"))
            return


        form = Form.from_dict(data)

        if "user" not in cookie:
            user_orm = UserORM(user, cursor, cnx).insert_db()

        output = template.render(errors=errors, data=data, user=user, path=path)

        user_id = UserORM(user, cursor, cnx).get_id()
        print(user_id, user)

        match variant:
            case UpdateVariant(Id):
                FormORM(form, cursor, cnx).update_db(Id)
            case CreateVariant:
                FormORM(form, cursor, cnx).insert_db(user_id)

        expires = datetime.utcnow() + timedelta(days=360) # expires in 30 days

        cookie["session"] = str(uuid.uuid4())
        cookie["session"]["path"] = "/"
        cookie["session"]["expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")

        cookie["errors"] = json.dumps(errors)
        cookie["errors"]["path"] = "/"

        cookie["user"] = json.dumps(user.to_dict())
        cookie["user"]["path"] = "/"

        cookie["data"] = json.dumps(form.to_dict())
        cookie["data"]["path"] = "/"
        # Send a response back to the client
        handler.send_response(200)
        handler.send_cors_headers()
        # Set cookie
        print(cookie.output(header=""))
        handler.send_header("Content-Type", "text/html")
        handler.send_header("Set-Cookie", cookie["session"].output(header=""))
        handler.send_header("Set-Cookie", cookie["errors"].output(header=""))
        handler.send_header("Set-Cookie", cookie["user"].output(header=""))
        handler.send_header("Set-Cookie", cookie["data"].output(header=""))
        handler.end_headers()

        handler.wfile.write(output.encode("utf-8"))

    @staticmethod
    def form_page_get_aux(handler, cursor, cnx, env, Id):
        """get page of form"""
        handler.send_response(200)
        handler.send_cors_headers()
        cookie_raw = handler.headers.get("Cookie")
        cookie = SimpleCookie()
        if cookie_raw is not None:
            cookie.load(cookie_raw)

        user = {}; errors = {}; data = {}
        if "user" in cookie:
            user = cookie["user"].value
        if "errors" in cookie:
            errors = cookie["errors"].value

        if Id is not None:
            form = FormORM(None, cursor, cnx).get_by_id(Id)
            formy = form.to_dict()
            print(formy)
            cookie["data"] = json.dumps(formy, default = str)

        if "data" in cookie:
            data = json.loads(cookie["data"].value)

        handler.send_header("Content-Type", "text/html")
        if "data" in cookie:
            handler.send_header("Set-Cookie", cookie["data"].output(header=""))

        template = env.get_template("index.html")
        output = template.render(errors=errors, data=data, user=user)

        handler.end_headers()
        handler.wfile.write(output.encode("utf-8"))




def get_cookie(cookie):
    user = {}; errors = {}; secret_key = {}; data = {}
    login_data = {}; login_errors = {}
    if "user" in cookie:
        user = json.loads(cookie["user"].value)
    if "errors" in cookie:
        errors = json.loads(cookie["errors"].value)
    if "data" in cookie:
        data = json.loads(cookie["data"].value)
    if "login_data" in cookie:
        login_data = json.loads(cookie["login_data"].value)
    if "login_errors" in cookie:
        login_errors = json.loads(cookie["login_errors"].value)

    return {"user": user,
            "errors": errors,
            "secret_key": secret_key,
            "data": data,
            "login_data": login_data,
            "login_errors": login_errors}
