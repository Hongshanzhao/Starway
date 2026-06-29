from .admin import admin_bp
from .assessment import assessment_bp
from .assistant import assistant_bp
from .auth import auth_bp
from .content import content_bp
from .job import job_bp
from .llm import llm_bp
from .match import match_bp
from .profile import profile_bp
from .report import report_bp
from .user import user_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(match_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(llm_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(assistant_bp)
