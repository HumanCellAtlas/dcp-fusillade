import os
import json
from flask import Flask, abort, jsonify, redirect, url_for, render_template
from flask_dance.contrib.github import make_github_blueprint, github

from .config import DefaultConfig
from .controllers import GitlabController, FileController


gitlab = GitlabController()


def get_groups():
    group_file_path = "config/groups.json"
    resp = gitlab.get_file_from_repo(group_file_path)
    group_data = json.loads(resp.text).get('groups')
    groups_in_file = [k for k,v in group_data if k != "user_default"]
    return groups_in_file


def add_user_to_group(service_account:str, groups:list):
    group_file_path = "config/groups.json"
    resp = gitlab.get_file_from_repo(group_file_path)
    groups_file = FileController(resp.text, group_file_path)
    # modify groups.json file thats committed currently
    groups_file.updated_data = groups_file.add_user_to_groups(service_account, groups)
    # create new branch, push changes
    gitlab.create_branch(service_account)
    gitlab.commit_changes_(service_account,groups_file)
    # TODO alerts


def get_headers():
    """Convenient way to get headers for assembling responses"""
    return {"Content-Type": "text/html", "Access-Control-Allow-Origin": "*"}


def create_app():
    """App factory method, see http://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/"""
    # app = Flask(__name__)
    app = Flask(__name__, template_folder="templates", static_folder="static")
    configure_app(app)
    configure_blueprints(app)
    configure_error_handlers(app)
    configure_endpoints(app)
    return app


def configure_app(app):
    """Set flask app configuration"""

    # Set config variables using an object
    # http://flask.pocoo.org/docs/api/#configuration
    app.config.from_object(DefaultConfig)

    # Set config variables using a python file
    # http://flask.pocoo.org/docs/config/#instance-folders
    app.config.from_pyfile('production.cfg', silent=True)

    # Set this if behind a TLS/HTTPS proxy
    # app.wsgi_app = ProxyFix(app.wsgi_app)

    # Set flask app secret key
    app.secret_key = app.config["FLASK_SECRET_KEY"]

    if app.secret_key == None:
        raise Exception("Error: environment variable FLASK_SECRET_KEY not set")


def configure_blueprints(app):
    """Apply blueprints to flask app"""

    # Apply flask-dance Github OAuth blueprint; client id and secret are already set in app.config
    github_bp = make_github_blueprint(scope="read:org")
    app.register_blueprint(github_bp, url_prefix="/login")
    

def configure_error_handlers(app):
    """Configure error handlers for flask app"""

    # Configure 404 error handlers
    # http://flask.pocoo.org/docs/latest/errorhandling/
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(403)
    def access_denied(error):
        return render_template("403.html"), 403


def configure_logging(app):
    """Configure logging for the flask app"""
    if app.debug or app.testing:
        # Skip logging in debug/test mode
        return

    import logging
    app.logger.setLevel(logging.INFO)


def configure_endpoints(app):

    # Simple hello world endpoint to test things out
    @app.route('/hello')
    def hello_world():
        return jsonify({"message": "Hello World!"})

    # When users hit the index,
    # - check if authorized
    #   - if not, redirect to lgoin url, taken care of by the github blueprint
    #   - if so, use the github object to call github api directly, check if user is in org
    #       - if not, 403 access denied
    #       - if so, show them the form
    @app.route('/')
    def index():
        # check if user is logged in, if not redirect to /login
        if not github.authorized:
            return redirect(url_for("github.login"))
    
        # check if user is in HCA github org
        resp = github.get("/user/orgs")
        if resp.ok:
            all_orgs = resp.json()
            for org in all_orgs:
                if org['login']==GH_ORG:
                    # Render the index (main form)
                    context = {"groups": get_groups()}
                    return render_template("index.html"), 200
    
            # Not in HCA org
            abort(403)
    
        else:
            # Error with Github API
            abort(404)
