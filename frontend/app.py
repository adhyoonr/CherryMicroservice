import cherrypy
import os

class FrontendServer:
    @cherrypy.expose
    def index(self):
        # Serve the index.html file
        return open(os.path.join(cherrypy.tools.staticdir.dir, 'index.html'))

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(current_dir, 'static')

    config = {
        '/': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': static_dir,
            'tools.staticdir.index': 'index.html',
        }
    }

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080, # Port untuk frontend
        'log.screen': True,
    })

    cherrypy.quickstart(FrontendServer(), '/', config)