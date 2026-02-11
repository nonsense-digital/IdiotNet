from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# thanks to https://flask-limiter.readthedocs.io/en/stable/
limiter = Limiter(
            get_remote_address,
            default_limits=["20 per second"],
            storage_uri="memory://",
        )

# thanks to https://stackoverflow.com/questions/73076749/flask-rate-limiter-not-working-with-flask-restful
def init(app):
    limiter.init_app(app)
