import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import cherrypy
import json
from peewee import IntegrityError, OperationalError, DoesNotExist
from shared_models import User, db_a, initialize_db_a_tables
from cherrypy_db_connection import DBConnectionTool

# --- UserAPI Class ---
@cherrypy.tools.json_out()
class UserAPI:
    exposed = True  # supaya kelas ini bisa diakses

    def GET(self, user_id=None, query=None):
        try:
            if user_id:
                try:
                    user = User.get(User.id == int(user_id))
                    user_data = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'fullname': user.fullname
                    }
                    return {'status': 'success', 'data': user_data}
                except DoesNotExist:
                    cherrypy.response.status = 404
                    return {'status': 'error', 'message': f'User with ID {user_id} not found.'}
            else:
                users_query = User.select()
                if query:
                    users_query = users_query.where(
                        (User.username.contains(query)) |
                        (User.email.contains(query)) |
                        (User.fullname.contains(query))
                    )
                all_users = []
                for user in users_query:
                    all_users.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'fullname': user.fullname
                    })
                return {'status': 'success', 'data': all_users}
        except OperationalError as e:
            cherrypy.response.status = 500
            return {'status': 'error', 'message': f'Database operational error: {e}'}
        except Exception as e:
            cherrypy.response.status = 500
            return {'status': 'error', 'message': f'An unexpected error occurred: {e}'}

    @cherrypy.tools.json_in()
    def POST(self):
        try:
            data = cherrypy.request.json
            required_fields = ["username", "email"]
            if not all(field in data for field in required_fields):
                cherrypy.response.status = 400
                return {"status": "error", "message": "Missing required fields (username, email)."}

            new_user = User.create(
                username=data['username'],
                email=data['email'],
                fullname=data.get('fullname')
            )
            cherrypy.response.status = 201
            return {"status": "success", "message": "User created successfully", "id": new_user.id}
        except IntegrityError:
            cherrypy.response.status = 409
            return {"status": "error", "message": "Failed to save data. Possible duplicate username or email."}
        except KeyError as e:
            cherrypy.response.status = 400
            return {"status": "error", "message": f"Invalid data format: Missing key {e}"}
        except OperationalError as e:
            cherrypy.log(f"Database error on POST /users: {e}", traceback=True)
            cherrypy.response.status = 500
            return {"status": "error", "message": "Database connection error."}
        except Exception as e:
            cherrypy.log(f"An unexpected error occurred on POST /users: {e}", traceback=True)
            cherrypy.response.status = 500
            return {"status": "error", "message": "An unexpected error occurred."}

    @cherrypy.tools.json_in()
    def PUT(self, user_id=None):
        if not user_id:
            cherrypy.response.status = 400
            return {"status": "error", "message": "User ID is required for update."}
        try:
            data = cherrypy.request.json
            if not data:
                cherrypy.response.status = 400
                return {"status": "error", "message": "No data provided for update."}

            user_id = int(user_id)
            user_to_update = User.get_or_none(User.id == user_id)
            if not user_to_update:
                cherrypy.response.status = 404
                return {"status": "error", "message": f"User with ID {user_id} not found."}

            updated_fields = {}
            if 'username' in data:
                updated_fields['username'] = data['username']
            if 'email' in data:
                updated_fields['email'] = data['email']
            if 'fullname' in data:
                updated_fields['fullname'] = data['fullname']

            if not updated_fields:
                return {"status": "success", "message": "No valid fields provided for update."}

            query = User.update(**updated_fields).where(User.id == user_id)
            updated_count = query.execute()

            if updated_count:
                return {"status": "success", "message": f"User with ID {user_id} updated successfully."}
            else:
                return {"status": "success", "message": f"User with ID {user_id} found, but no changes were made."}
        except ValueError:
            cherrypy.response.status = 400
            return {"status": "error", "message": "Invalid user ID. Must be an integer."}
        except IntegrityError:
            cherrypy.response.status = 409
            return {"status": "error", "message": "Failed to update data. Possible duplicate username or email."}
        except OperationalError as e:
            cherrypy.log(f"Database error on PUT /users/{user_id}: {e}", traceback=True)
            cherrypy.response.status = 500
            return {"status": "error", "message": "Database connection error."}
        except Exception as e:
            cherrypy.log(f"An unexpected error occurred on PUT /users/{user_id}: {e}", traceback=True)
            cherrypy.response.status = 500
            return {"status": "error", "message": "An unexpected error occurred."}

    def DELETE(self, user_id=None):
        if not user_id:
            cherrypy.response.status = 400
            return {"status": "error", "message": "User ID is required for deletion."}
        try:
            user_id = int(user_id)
            deleted_count = User.delete().where(User.id == user_id).execute()
            if deleted_count:
                return {"status": "success", "message": f"User with ID {user_id} deleted successfully."}
            else:
                cherrypy.response.status = 404
                return {"status": "error", "message": f"User with ID {user_id} not found."}
        except ValueError:
            cherrypy.response.status = 400
            return {"status": "error", "message": "Invalid user ID. Must be an integer."}
        except OperationalError as e:
            cherrypy.log(f"Database error on DELETE /users/{user_id}: {e}", traceback=True)
            cherrypy.response.status = 500
            return {"status": "error", "message": "Database connection error."}
        except Exception as e:
            cherrypy.log(f"An unexpected error occurred on DELETE /users/{user_id}: {e}", traceback=True)
            cherrypy.response.status = 500
            return {"status": "error", "message": "An unexpected error occurred."}

    def OPTIONS(self, *args, **kwargs):
        # Untuk CORS preflight
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.status = 200
        return ""

if __name__ == "__main__":
    try:
        initialize_db_a_tables()
        print("UserAPI: Database db_a.sqlite initialized with User table.")
    except OperationalError as e:
        cherrypy.log(f"FATAL: Could not connect to database for UserAPI: {e}", context='STARTUP', traceback=True)
        import sys
        sys.exit(1)
    except Exception as e:
        cherrypy.log(f"FATAL: An unexpected error occurred during UserAPI database setup: {e}", context='STARTUP', traceback=True)
        import sys
        sys.exit(1)

    cherrypy.tools.CORS = cherrypy.Tool('before_handler', lambda: cherrypy.response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }))

    config = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [("Content-Type", "application/json")],
            'tools.CORS.on': True,
            'tools.db_connection.on': True,
            'tools.db_connection.dbname': 'db_a'
        }
    }

    cherrypy.config.update({
        "server.socket_host": "0.0.0.0",
        "server.socket_port": 5052,
        "log.screen": True
    })

    cherrypy.tree.mount(
        UserAPI(), '/users', config
    )

    print(f"UserAPI running on http://0.0.0.0:5052/users")
    cherrypy.engine.start()
    cherrypy.engine.block()
