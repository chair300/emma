import cherrypy
from app import flask_app

def run_server():

    cherrypy.tree.graft(flask_app, '/')

    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.config.update({'server.socket_port': 5000})

    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    run_server()