from .info_routes import *
from .grades_routes import *
from .assignments_routes import *
from .auth_routes import *
from .transcript_routes import *
from .report_routes import *
from .session_routes import *
from .lookup_routes import *


def register_routes(app):
    app.register_blueprint(info_bp)
    app.register_blueprint(grades_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(transcript_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(lookup_bp)

