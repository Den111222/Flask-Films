from flask import request
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.orm import selectinload

from src import db
from src.database.models import Film
from src.resources.auth import token_required
from src.schemas.films import FilmSchema
from src.services.film_service import FilmService


class FilmListApi(Resource):
    film_schema = FilmSchema()

    def get(self, uuid=None):
        if not uuid:
            films = FilmService.fetch_all_films(db.session).options(
                selectinload(Film.actors)
            ).all()
            return self.film_schema.dump(films, many=True), 200
        film = FilmService.fetch_film_by_uuid(db.session, uuid)
        if not film:
            return "", 404
        return self.film_schema.dump(film), 200

    @token_required
    def post(self):
        try:
            film = self.film_schema.load(request.json, session=db.session)
        except ValidationError as e:
            return {'message': str(e)}, 400
        db.session.add(film)
        db.session.commit()
        return self.film_schema.dump(film), 201

    @token_required
    def put(self, uuid):
        film = FilmService.fetch_film_by_uuid(db.session, uuid)
        if not film:
            return "", 404
        try:
            film = self.film_schema.load(request.json, instance=film, session=db.session)
        except ValidationError as e:
            return {'message': str(e)}, 400
        db.session.add(film)
        db.session.commit()
        return self.film_schema.dump(film), 200

    # @token_required
    def patch(self, uuid):
        pass

    @token_required
    def delete(self, uuid):
        film = FilmService.fetch_film_by_uuid(db.session, uuid)
        film_name, uuid = film.title, film.uuid
        if not film:
            return "", 404
        db.session.delete(film)
        db.session.commit()
        return f'film: {film_name} with uuid: {uuid} is deleted', 204
