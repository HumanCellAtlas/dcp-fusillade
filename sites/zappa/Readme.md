# zappa flask app

This folder contains a [zappa](https://github.com/Miserlou/Zappa) web app for
DCP operators to add users (service accounts) to groups for Fusillade's 
authentication/authorization layer.

[zappa](https://github.com/Miserlou/Zappa) is a framework for deploying dynamic
sites that use Flask via AWS Lambda functions.

---

# necessary parts

## installing zappa

To install:

    pip install zappa

## setting up virtual environment

You should set up a virtual environment in the `zappa/` folder, and it should be independent of any virtual environment
anywhere else in the dcp-fusillade repo. (This avoids installing/uploading unnecessary software packages to the lambda.)

## making `zappa_settings.json`

New projects run `zappa init` to create `zappa_settings.json`, but this repo has a template version.

To generate the `zappa_settings.json`, run the script:

```
./zappa_settings_template.json 
```

This will get info about the IAM account, apply it to the IAM policy template, and generate a `zappa_settings.json`.

## stages

zappa has the concept of multiple stages baked in. We deploy one stage per
Fusillade deployment (per branch in the Allspark dcp-fusillade repo):

* testing
* dev
* integration
* staging
* prod

Set the stage for the zappa deployment using `FUS_DEPLOYMENT_STAGE`
env var in the `environment` file
[`../../environment`](../../environment) in the top level of the
dcp-fusillade repository.

## environment

This deployment utilizes the `environment` file at the root of this repo. To source these files:

```
source ../../environment
source ../../environment.local
```

Env vars used include:

* `FUS_DEPLOYMENT_STAGE`
* `GITLAB_URL`
* `GITLAB_PROJECT_ID`

Secrets should live in `environment.local`:

* `DCP_FUS_GL_TOKEN` - gitlab access token for user who will open gitlab pull 
  request in dcp-fusillade repo on Allspark
* `DCP_FUS_GH_CLIENT_ID` - github OAuth app client id
* `DCP_FUS_GH_CLIENT_TOKEN` - github OAuth app client token

## gitlab token

A Gitlab access token is needed to open PRs in dcp-fusillade on Allspark.

## github oauth app

A Github OAuth app is needed to verify operators are members of the HCA.

## infrastructure

what zappa does:

>>> To explain what's going on, when you call deploy, Zappa will automatically package up your application and
    local virtual environment into a Lambda-compatible archive, replace any dependencies with versions precompiled for
    Lambda, set up the function handler and necessary WSGI Middleware, upload the archive to S3, create and manage
    the necessary Amazon IAM policies and roles, register it as a new Lambda function, create a new API Gateway
    resource, create WSGI-compatible routes for it, link it to the new Lambda function, and finally delete the
    archive from your S3 bucket.

## permissions and iam roles

Zappa creates a default IAM role and policy:

>>> Be aware that the default IAM role and policy created for executing Lambda applies a liberal set of
    permissions. These are most likely not appropriate for production deployment of important applications. See the
    section Custom AWS IAM Roles and Policies for Execution for more detail.

To manage IAM permissions ourselves, we:

- use `zappa_settings_template.json` as a template settings file
- use `build_zappa_settings.sh` to turn the template settings file into a real settings file; this script will:
    - populate the `extra_permissions` key with a list of explicit permissions
- set `manage_roles` key to `false`

To create `zappa_settings.json`, run:

```
./build_zappa_settings.sh
```

---

# dcp-fusillade users-groups webapp

## package structure

The dcp-fusillade users-group webapp is a package in the `app` folder.

- `__init__.py` imports the top-level factory function, `create_app()`
- `config.py` turns environment variables/AWS secrets into Flask config variables
- `controllers.py` defines backend logic for interfacing with Gitlab and making branches/commits/pull requests
- `flask_app.py` defines the flask app, its configuration, and its routes
- `static/` and `templates/` contain files for Flask pages

## entry point

To run the flask app, use `run.py` in the `zappa` folder:

```
./run.py
```

This will run the Flask app locally at `http://localhost:5000`.

## deploying

TBD

---

# faq

## what does zappa deploy do?

From the [Zappa reamde](https://github.com/Miserlou/Zappa):

>>> To explain what's going on, when you call deploy, Zappa will automatically package up your application and
    local virtual environment into a Lambda-compatible archive, replace any dependencies with versions precompiled for
    Lambda, set up the function handler and necessary WSGI Middleware, upload the archive to S3, create and manage
    the necessary Amazon IAM policies and roles, register it as a new Lambda function, create a new API Gateway
    resource, create WSGI-compatible routes for it, link it to the new Lambda function, and finally delete the
    archive from your S3 bucket.

## what security implications does this have?

Zappa creates a default IAM role and policy:

>>> Be aware that the default IAM role and policy created for executing Lambda applies a liberal set of
    permissions. These are most likely not appropriate for production deployment of important applications. See the
    section Custom AWS IAM Roles and Policies for Execution for more detail.

We address this by setting `manage_roles` to `false` and defining explicit permissions to give the lambda IAM user.

