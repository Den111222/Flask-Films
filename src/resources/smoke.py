from flask_restful import Resource


class Smoke(Resource):
    def get(self):
        return {"message": "OK", "register": "/register", "get films": "/films",
                "login": "/login", "get actors": "/actors",
                "create film": "POST /films "
                               "header Authorization: 'Basic <login:password in base 64>'"
                               "json: "
                             '{'
                               '"title": "Test Title", '
                               '"distributed_by": "Test Company", '
                               '"release_date": "2010-04-01", '
                               '"description": "", '
                               '"length": 100, '
                               '"rating": 8.0'
                               '}',
                "update film": "PUT /films/uuid "
                               "header Authorization: 'Basic <login:password in base 64>'"
                               "json: "
                                '{'
                               '"title": "Update Title",'
                               '"distributed_by": "Update Company",'
                               '"release_date": "2010-04-01"'
                               '}',
                "delete film": "DELETE /films/uuid"
                               "header Authorization: 'Basic <login:password in base 64>'",
                "get aggregations": "/aggregations",
                "add films to base from site simple method": "POST /populate_db",
                "add films to base from site threaded method": "POST /populate_db_threaded",
                "add films to base from site Thread Pool Executor method": "POST /populate_db_executor",
                }
