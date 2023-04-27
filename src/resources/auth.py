import datetime
from functools import wraps

import jwt
from flask import request, jsonify
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash

from src import db, app
from src.database.models import User
from src.schemas.users import UserSchema


class AuthRegister(Resource):
    user_schema = UserSchema()
    token = ''

        # curl - X 'POST' \ 'http://127.0.0.1:5000/register' \ - H 'accept: */*' \ - H
        # 'Content-Type: application/json' \ - d '{"username": "admin", "email": "admin@gmail.com",
        # "password": "admin"}'

    def post(self):
        try:
            user = self.user_schema.load(request.json, session=db.session)
        except ValidationError as e:
            return {"message": str(e)}
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"message": "Such user exists"}, 409
        return self.user_schema.dump(user), 201


def token_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        auth = request.authorization
        if not auth:
            return "", 401, {"WWW-Authenticate": "Basic realm='Authentication required'"}
        user = User.find_user_by_username(auth.get('username', ''))
        if not user or not check_password_hash(user.password, auth.get('password', '')):
            return "", 401, {"WWW-Authenticate": "Basic realm='Authentication required'"}
        AuthRegister.token = jwt.encode(
            {
                "user_id": user.uuid,
                "exp": datetime.datetime.now() + datetime.timedelta(minutes=1)
            }, app.config['SECRET_KEY']
        )
        return func(self, *args, **kwargs)
    return wrapper


class AuthLogin(Resource):
    @token_required
    def get(self):
        return jsonify(
            {
                # "token": token.decode('utf-8')    #перестало работать из за обновления pyjwt
                "token": AuthRegister.token
            }
        )
