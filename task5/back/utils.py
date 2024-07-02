import random
import json
import re
import bcrypt
from typing import Self
import string
import secrets
from datetime import datetime
from abc import ABC, abstractmethod
import mysql.connector

from dataclasses import dataclass

@dataclass
class UpdateVariant:
    id: int

@dataclass
class CreateVariant:
    pass

FormVariants = UpdateVariant | CreateVariant


class ORM(ABC):
    @abstractmethod
    def __init__(self, obj, cursor, cnx):
        pass

    @abstractmethod
    def insert_db(self):
        pass

    @abstractmethod
    def get_id(self):
        pass

class ToDict(ABC):
    """Trait for all to_dict'able objects"""
    @abstractmethod
    def to_dict(self):
        pass

class FromDict(ABC):
    @abstractmethod
    def from_dict(d):
        pass

class Validatable(ABC):
    """Trait for all validatable objects"""
    @abstractmethod
    def validate(self):
        pass



class UserORM(ORM):
    def __init__(self, user, cursor, cnx):
        self.user = user
        self.cursor = cursor
        self.cnx = cnx

    def __str__(self):
        return self.user.__str__()

    def insert_db(self):
        query = f"""
                    INSERT INTO user (username, password)
                    VALUES (%s, %s)
                """

        self.cursor.execute(
            query,
            (
                self.user.username,
                self.user.hashify(self.user.password)
            )
        )
        self.cnx.commit()

    def get_id(self):
        query = f"""
            SELECT id FROM user WHERE username = %s
        """
        self.cursor.execute(
            query,
            (self.user.username,)
        )

        return self.cursor.fetchone()[0]


class FormORM(ORM):
    def __init__(self, form, cursor, cnx):
        self.form = form
        self.cursor = cursor
        self.cnx = cnx

    def insert_db(self, user_id):
        query = f"""
            INSERT INTO application (user_id,
                                     name,
                                     phone,
                                     email,
                                     birthday,
                                     sex,
                                     fav_lang,
                                     bio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        form = self.form
        self.cursor.execute(
            query,
            (
                user_id,
                form.name,
                form.number,
                form.email,
                form.birthday,
                form.sex,
                form.fav_lang,
                form.bio
            )
        )
        self.cnx.commit()

    def update_db(self, application_id):
        query = """
            UPDATE application
            SET name = %s,
                phone = %s,
                email = %s,
                birthday = %s,
                sex = %s,
                fav_lang = %s,
                bio = %s
            WHERE
                id = %s
        """
        form = self.form
        self.cursor.execute(
            query,
            (
                form.name,
                form.number,
                form.email,
                form.birthday,
                form.sex,
                form.fav_lang,
                form.bio,
                application_id
            )
        )
        self.cnx.commit()

    def get_by_id(self, rec_id):
        query = """
            SELECT * from application
            WHERE id = %s
        """

        self.cursor.execute(query, (rec_id,))

        res = self.cursor.fetchone()
        print(res)
        return Form.from_unwrappable(res[1:2] + res[3:] + (True, ))

    def get_id(self, user_id):
        query = f"""
            SELECT id FROM application WHERE user_id = %s
        """
        self.cursor.execute(
            query,
            (self.user.username,)
        )
        return cursor.fetchall()


class User(ToDict):
    """User module"""
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def __str__(self) -> str:
        return f"Username: {self.username}, Password: {self.password}"

    def to_dict(self):
        return dict(username = self.username, password = self.password)

    @staticmethod
    def hashify(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"),
                             bcrypt.gensalt())

    @staticmethod
    def check_in_db(user, cursor, cnx) -> bool:
        query = "SELECT password FROM user WHERE username = %s"
        cursor.execute(query, (user.username, ))
        result = cursor.fetchone()
        return User.verify(user.password, result[0].encode("utf-8"))

    @staticmethod
    def verify(plain_password: str, hashed_password: int) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"),
                              hashed_password)

    @staticmethod
    def generate_user(
            username_length = 10,
            password_length = 15
    ):
        def generate_string(length: int) -> str:
            chars = string.ascii_letters + string.digits
            return "".join(secrets.choice(chars) for _ in range(length))

        username = generate_string(username_length)
        password = generate_string(password_length)

        return User(username, password)

class Form(ToDict, FromDict, Validatable):
    """Class which allow easily manipulate form"""
    def __init__(
            self,
            name,
            number,
            email,
            birthday,
            sex,
            fav_lang,
            bio,
            agreement
    ):
        self.name = name
        self.number = number
        self.email = email
        self.birthday = birthday
        self.sex = sex
        self.fav_lang = fav_lang
        self.bio = bio
        self.agreement = agreement

    def to_dict(self):
        return {
            'name': self.name,
            'number': self.number,
            'email': self.email,
            'birthday': self.birthday,
            'sex': self.sex,
            'fav_lang': self.fav_lang,
            'bio': self.bio,
            'agreement': self.agreement
        }

    @classmethod
    def from_dict(self, d):
        return Form(**d)

    @classmethod
    def from_unwrappable(self, u):
        return Form(*u)

    def validate(data) -> dict:
        """Validate"""
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

        if not data.get("birthday"):
            errors["birthday"] = "Birthday is required"
        else:
            try:
                birthday = datetime.strptime(data["birthday"], "%Y-%m-%d")
                if birthday > datetime.now():
                    errors["birthday"] = "Birthday cannot be in the future"
            except ValueError:
                errors["birthday"] = "Invalid birthday format, must be YYYY-MM-DD"
        return errors
