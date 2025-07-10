import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cherrypy
import json
from decimal import Decimal
from peewee import IntegrityError, OperationalError, DoesNotExist
from shared_models import TBCarsWeb, db_a, initialize_db_a_tables
from cherrypy_db_connection import DBConnectionTool


# Aktifkan CORS global
cherrypy.tools.CORS = cherrypy.Tool('before_handler', lambda: cherrypy.response.headers.update({
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400'
}))


@cherrypy.expose
@cherrypy.tools.json_out()
class CarAPI:
    def GET(self, car_id=None, query=None):
        try:
            if car_id:
                car_id = int(car_id)
                car = TBCarsWeb.get(TBCarsWeb.id == car_id)
                return {
                    "status": "success",
                    "data": {
                        "id": car.id,
                        "carname": car.carname,
                        "carbrand": car.carbrand,
                        "carmodel": car.carmodel,
                        "carprice": str(car.carprice),
                        "description": car.description
                    }
                }
            else:
                cars = TBCarsWeb.select()
                if query:
                    cars = cars.where(
                        (TBCarsWeb.carname.contains(query)) |
                        (TBCarsWeb.carbrand.contains(query)) |
                        (TBCarsWeb.carmodel.contains(query)) |
                        (TBCarsWeb.description.contains(query))
                    )
                return {
                    "status": "success",
                    "data": [
                        {
                            "id": c.id,
                            "carname": c.carname,
                            "carbrand": c.carbrand,
                            "carmodel": c.carmodel,
                            "carprice": str(c.carprice),
                            "description": c.description
                        } for c in cars
                    ]
                }
        except DoesNotExist:
            cherrypy.response.status = 404
            return {"status": "error", "message": "Car not found"}
        except Exception as e:
            cherrypy.response.status = 500
            return {"status": "error", "message": str(e)}

    @cherrypy.tools.json_in()
    def POST(self):
        try:
            data = cherrypy.request.json
            car = TBCarsWeb.create(
                carname=data['carname'],
                carbrand=data['carbrand'],
                carmodel=data['carmodel'],
                carprice=Decimal(str(data['carprice'])),
                description=data.get('description', '')
            )
            cherrypy.response.status = 201
            return {"status": "success", "id": car.id}
        except IntegrityError:
            cherrypy.response.status = 409
            return {"status": "error", "message": "Duplicate car"}
        except Exception as e:
            cherrypy.response.status = 400
            return {"status": "error", "message": str(e)}

    @cherrypy.tools.json_in()
    def PUT(self, car_id):
        try:
            car_id = int(car_id)
            data = cherrypy.request.json
            query = TBCarsWeb.update(
                carname=data.get('carname'),
                carbrand=data.get('carbrand'),
                carmodel=data.get('carmodel'),
                carprice=Decimal(str(data.get('carprice'))),
                description=data.get('description')
            ).where(TBCarsWeb.id == car_id)
            updated = query.execute()
            if updated:
                return {"status": "success", "message": "Car updated"}
            else:
                return {"status": "error", "message": "Car not found or no change"}
        except Exception as e:
            cherrypy.response.status = 400
            return {"status": "error", "message": str(e)}

    def DELETE(self, car_id):
        try:
            car_id = int(car_id)
            deleted = TBCarsWeb.delete().where(TBCarsWeb.id == car_id).execute()
            if deleted:
                return {"status": "success", "message": "Car deleted"}
            else:
                cherrypy.response.status = 404
                return {"status": "error", "message": "Car not found"}
        except Exception as e:
            cherrypy.response.status = 400
            return {"status": "error", "message": str(e)}

    def OPTIONS(self, *args, **kwargs):
        cherrypy.response.status = 200
        return ""


if __name__ == '__main__':
    # Setup DB & CORS
    initialize_db_a_tables()

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 5051,
        'log.screen': True
    })

    config = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')],
            'tools.CORS.on': True,
            'tools.trailing_slash.on': False,
            'tools.db_connection.on': True,
            'tools.db_connection.dbname': 'db_a'
        }
    }

    cherrypy.tree.mount(CarAPI(), '/cars', config)
    cherrypy.engine.start()
    cherrypy.engine.block()
