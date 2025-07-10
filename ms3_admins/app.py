import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cherrypy
from peewee import IntegrityError, OperationalError
from shared_models import Admin, initialize_db_b_tables

@cherrypy.expose
@cherrypy.tools.json_out()
class AdminAPI:

    @cherrypy.tools.json_in()
    def GET(self, admin_id=None, query=None):
        try:
            if admin_id:
                admin = Admin.get_or_none(Admin.id == int(admin_id))
                if not admin:
                    cherrypy.response.status = 404
                    return {'status': 'error', 'message': f'Admin with ID {admin_id} not found.'}
                return {
                    'status': 'success',
                    'data': {
                        'id': admin.id,
                        'username': admin.username,
                        'email': admin.email,
                        'role': admin.role
                    }
                }
            else:
                admins_query = Admin.select()
                if query:
                    admins_query = admins_query.where(
                        (Admin.username.contains(query)) |
                        (Admin.email.contains(query)) |
                        (Admin.role.contains(query))
                    )
                admins_list = [{
                    'id': a.id,
                    'username': a.username,
                    'email': a.email,
                    'role': a.role
                } for a in admins_query]
                return {'status': 'success', 'data': admins_list}
        except OperationalError as e:
            cherrypy.response.status = 500
            return {'status': 'error', 'message': f'Database operational error: {e}'}
        except Exception as e:
            cherrypy.response.status = 500
            return {'status': 'error', 'message': f'Unexpected error: {e}'}

    @cherrypy.tools.json_in()
    def POST(self):
        try:
            data = cherrypy.request.json
            required_fields = ["username", "email"]
            if not all(field in data for field in required_fields):
                cherrypy.response.status = 400
                return {"status": "error", "message": "Missing required fields (username, email)."}

            new_admin = Admin.create(
                username=data['username'],
                email=data['email'],
                role=data.get('role')
            )
            cherrypy.response.status = 201
            return {"status": "success", "message": "Admin created successfully", "id": new_admin.id}
        except IntegrityError:
            cherrypy.response.status = 409
            return {"status": "error", "message": "Duplicate username or email."}
        except Exception as e:
            cherrypy.response.status = 500
            return {"status": "error", "message": f"Unexpected error: {e}"}

    @cherrypy.tools.json_in()
    def PUT(self, admin_id=None):
        if not admin_id:
            cherrypy.response.status = 400
            return {"status": "error", "message": "admin_id is required for update."}
        try:
            data = cherrypy.request.json
            if not data:
                cherrypy.response.status = 400
                return {"status": "error", "message": "No data provided for update."}

            admin_to_update = Admin.get_or_none(Admin.id == int(admin_id))
            if not admin_to_update:
                cherrypy.response.status = 404
                return {"status": "error", "message": f"Admin with ID {admin_id} not found."}

            update_data = {}
            for field in ['username', 'email', 'role']:
                if field in data:
                    update_data[field] = data[field]

            if not update_data:
                return {"status": "success", "message": "No valid fields to update."}

            Admin.update(**update_data).where(Admin.id == int(admin_id)).execute()
            return {"status": "success", "message": f"Admin with ID {admin_id} updated successfully."}
        except IntegrityError:
            cherrypy.response.status = 409
            return {"status": "error", "message": "Duplicate username or email."}
        except Exception as e:
            cherrypy.response.status = 500
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def DELETE(self, admin_id=None):
        if not admin_id:
            cherrypy.response.status = 400
            return {"status": "error", "message": "admin_id is required for delete."}
        try:
            deleted_count = Admin.delete().where(Admin.id == int(admin_id)).execute()
            if deleted_count:
                return {"status": "success", "message": f"Admin with ID {admin_id} deleted successfully."}
            else:
                cherrypy.response.status = 404
                return {"status": "error", "message": f"Admin with ID {admin_id} not found."}
        except Exception as e:
            cherrypy.response.status = 500
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def OPTIONS(self, *args, **kwargs):
        cherrypy.response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        cherrypy.response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        cherrypy.response.status = 200
        return ""

if __name__ == "__main__":
    initialize_db_b_tables()

    # Definisikan tool CORS sederhana
    cherrypy.tools.CORS = cherrypy.Tool('before_handler', lambda: cherrypy.response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }))

    config = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.trailing_slash.on': True,  # penting supaya /admins dan /admins/ sama-sama diterima
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [("Content-Type", "application/json")],
            'tools.CORS.on': True,
            # 'tools.db_connection.on': True,  # aktifkan kalau kamu punya tool ini
            # 'tools.db_connection.dbname': 'db_b',
        }
    }

    cherrypy.config.update({
        "server.socket_host": "0.0.0.0",
        "server.socket_port": 5053,
        "log.screen": True
    })

    cherrypy.tree.mount(AdminAPI(), '/admins', config)

    print("AdminAPI running on http://0.0.0.0:5053/admins")

    cherrypy.engine.start()
    cherrypy.engine.block()
