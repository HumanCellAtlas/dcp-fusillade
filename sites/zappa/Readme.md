# zappa flask app

This folder contains a [zappa](https://github.com/Miserlou/Zappa) web app for
DCP operators to add users (service accounts) to groups for Fusillade's 
authentication/authorization layer.

[zappa](https://github.com/Miserlou/Zappa) is a framework for deploying dynamic
sites that use Flask via AWS Lambda functions.


# necessary parts

## installing zappa

To install:

    pip install zappa

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

This deployment utilizes the `environment` file at the root of this repo.
Env vars used include:

* `FUS_DEPLOYMENT_STAGE`
* `FUS_API_ENDPOINT`
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

This is addressed in the `zappa_settings.json` file by setting `manage_roles` to `false` and setting the variables
`role_name` and `role_arn` (code from the zappa readme):

```
{
    "dev": {
        ...
        "manage_roles": false, // Disable Zappa client managing roles.
        "role_name": "MyLambdaRole", // Name of your Zappa execution role. Optional, default: <project_name>-<env>-ZappaExecutionRole.
        "role_arn": "arn:aws:iam::12345:role/app-ZappaLambdaExecutionRole", // ARN of your Zappa execution role. Optional.
        ...
    },
    ...
}
```

Specific permissions can be attached (code from the zappa readme):

```
{
    "dev": {
        ...
        "extra_permissions": [{ // Attach any extra permissions to this policy.
            "Effect": "Allow",
            "Action": ["rekognition:*"], // AWS Service ARN
            "Resource": "*"
        }]
    },
    ...
}
```

# dcp-fusillade users-groups webapp



## deploying





## faq

### what does zappa deploy do?

From the [Zappa reamde](https://github.com/Miserlou/Zappa):

>>> To explain what's going on, when you call deploy, Zappa will automatically package up your application and
    local virtual environment into a Lambda-compatible archive, replace any dependencies with versions precompiled for
    Lambda, set up the function handler and necessary WSGI Middleware, upload the archive to S3, create and manage
    the necessary Amazon IAM policies and roles, register it as a new Lambda function, create a new API Gateway
    resource, create WSGI-compatible routes for it, link it to the new Lambda function, and finally delete the
    archive from your S3 bucket.

### what security implications does this have?

Zappa creates a default IAM role and policy:

>>> Be aware that the default IAM role and policy created for executing Lambda applies a liberal set of
    permissions. These are most likely not appropriate for production deployment of important applications. See the
    section Custom AWS IAM Roles and Policies for Execution for more detail.

This is addressed in the `zappa_settings.json` file by setting `manage_roles` to `false` and setting the variables
`role_name` and `role_arn` (code from the zappa readme):

```
{
    "dev": {
        ...
        "manage_roles": false, // Disable Zappa client managing roles.
        "role_name": "MyLambdaRole", // Name of your Zappa execution role. Optional, default: <project_name>-<env>-ZappaExecutionRole.
        "role_arn": "arn:aws:iam::12345:role/app-ZappaLambdaExecutionRole", // ARN of your Zappa execution role. Optional.
        ...
    },
    ...
}
```

Specific permissions can be attached (code from the zappa readme):

```
{
    "dev": {
        ...
        "extra_permissions": [{ // Attach any extra permissions to this policy.
            "Effect": "Allow",
            "Action": ["rekognition:*"], // AWS Service ARN
            "Resource": "*"
        }]
    },
    ...
}
```














