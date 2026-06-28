# 初始化蓝图，导出所有蓝图
# routes/__init__.py
from .job import job_bp
from .match import match_bp
from .report import report_bp
from .auth import auth_bp
from .content import content_bp   # 新增
from .admin import admin_bp
from .llm import llm_bp
from .profile import profile_bp   # 新增
from .assessment import assessment_bp

def register_blueprints(app):

    app.register_blueprint(job_bp)
    app.register_blueprint(match_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(content_bp)  # 新增
    app.register_blueprint(admin_bp)
    app.register_blueprint(llm_bp)
    app.register_blueprint(profile_bp)  # 新增

    app.register_blueprint(assessment_bp)
   