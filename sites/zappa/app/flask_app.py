import os
import json
import urllib
import requests
from flask import Flask, current_app, request, abort, jsonify, redirect, url_for, render_template
from flaskext.markdown import Markdown
from flask_dance.contrib.github import make_github_blueprint, github

from .config import TestConfig, LocalConfig, LiveConfig
from .utils import get_groups_from_gitlab, add_user_to_group_merge_request
from .errors import GitlabError, EnvironmentVariableError, MalformedFusilladeConfigError


def get_headers():
    """Convenient way to get headers for assembling responses"""
    return {"Content-Type": "text/html", "Access-Control-Allow-Origin": "*"}


def create_app(user_config=None):
    """App factory method, see http://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/"""
    app = Flask(__name__, template_folder="templates", static_folder="static")
    configure_app(app, user_config)
    configure_extensions(app)
    configure_blueprints(app)
    configure_error_handlers(app)
    configure_endpoints(app)
    return app


def configure_app(app, user_config):
    """Set flask app configuration, and set the (optional) user-provided config"""

    # Set config variables using an object
    # http://flask.pocoo.org/docs/api/#configuration
    if user_config is not None:
        if user_config.get('TESTING', False):

            # User passed in a testing configuration
            app.config.from_object(TestConfig())
            app.config.update(user_config)

        elif user_config.get('LOCAL', False):
            # User is running the Flask app locally
            app.config.from_object(LocalConfig())
            app.config.update(user_config)

        else:
            # Probably never get here
            app.config.update(user_config)

    else:
        # Do it live
        app.config.from_object(LiveConfig())

    # Set this if behind a TLS/HTTPS proxy
    # app.wsgi_app = ProxyFix(app.wsgi_app)

    # Set flask app secret key
    app.secret_key = app.config["FLASK_SECRET_KEY"]

    if app.secret_key == None:
        raise EnvironmentVariableError("Error: environment variable FLASK_SECRET_KEY not set")


def configure_extensions(app):
    """Add Flask extensions for enhanced functionality"""
    Markdown(app, extensions=["fenced_code"])


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

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("500.html"), 500


def configure_logging(app):
    """Configure logging for the flask app"""
    if app.debug or app.testing:
        # Skip logging in debug/test mode
        return

    import logging
    app.logger.setLevel(logging.INFO)


def check_user_in_org(all_orgs, org_name):
    """Given a response from github.get("/user/orgs"), determine if the user is in an organization"""
    for org in all_orgs:
        if org["login"] == org_name:
            return True
    return False

def configure_endpoints(app):
    """Configure all endpoints for our flask app"""

    flask_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    github_org = app.config["GITHUB_ORG"]

    @app.route("/ping")
    def ping():
        """Simple ping pong endpoint"""
        return jsonify({"message": "pong"})

    @app.route("/")
    def index():
        """Ask non-authenticated users to log in via github, redirect users who are in HCA to form"""

        # Check if user is logged in, if not redirect to login landing page
        if not github.authorized:
            return render_template("login.html"), 200

        try:
            resp = github.get("/user/orgs")
        except requests.exceptions.ConnectionError:
            # Error with Github API
            abort(404)

        if resp.ok:
            if check_user_in_org(resp.json(), github_org):
                try:
                    context = {"groups": get_groups_from_gitlab(current_app.config)}
                    return render_template("index.html", **context), 200
                except GitlabError as e:
                    # To pass kwargs through to error pages, use a custom error class
                    # https://flask.palletsprojects.com/en/1.1.x/patterns/apierrors/
                    abort(500)
            else:
                # Not in HCA org
                abort(403)
        else:
            # Error with Github API
            abort(404)

    @app.route("/submit", methods=["POST"])
    def submit():
        """Endpoint for when the user submits the form"""

        # check if user is logged in, if not redirect to login landing page
        if not github.authorized:
            return render_template("login.html"), 200

        resp = github.get("/user/orgs")
        if resp.ok:
            if check_user_in_org(resp, github_org):
                # Extract the form data as a dictionary
                content_types = (["application/x-www-form-urlencoded"],)

                form_data = request.form
                email = form_data.get("email")
                groups = [j for j in form_data if form_data[j] == "on"]
                context = {"email": email, "groups": ", ".join(groups)}

                # If add user to group fails, we try to provide the operator with some additional useful info
                try:
                    merge_request_result = add_user_to_group_merge_request(email, groups, current_app.config)
                    pr_url = merge_request_result['web_url']
                    context['pr_url'] = pr_url
                except MalformedFusilladeConfigError:
                    context['error_message'] = "Malformed Fusillade Error: Fusillade configuration file is malformed and cannot be parsed"
                    return render_template("failure.html", **context), 200
                except GitlabError as e:
                    context['error_message'] = "Gitlab Error: Gitlab API calls resulted in an error: %s"%(str(e))
                    return render_template("failure.html", **context), 200
                except Exception as e:
                    context['error_message'] = "Error: could not add user to group: %s"%(str(e))
                    return render_template("failure.html", **context), 200
                else:
                    return render_template("success.html", **context), 200
            else:
                # Not in HCA org
                abort(403)
        else:
            # Error with Github API
            abort(404)


    @app.route("/faq")
    def faq():
        """Endpoint for static page of text describing the webapp"""
        with open(os.path.join(flask_root, "templates", "faq.md"), "r") as f:
            context = dict(markdown_body=f.read())
        return render_template("faq.html", **context), 200
