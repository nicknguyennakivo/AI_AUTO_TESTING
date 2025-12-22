from flask_restx import Api

from app import Config

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-Key'
    }
}


api = Api(
    title='Social API',
    version=Config.VERSION,
    description='',
    authorizations=authorizations,
    security='apikey',
)
