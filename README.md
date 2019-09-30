# Detailed Design

How do we want to use groups and roles in the DCP? 

We need to define some basic groups for assigning our users, this list of groups should be in a central location and 
the roles associated with them are defined by each component. Components are responsible for managing those roles and 
ensuring they are available when the group is created and modified.

## Component Organization Convention

Components will define a configuration file defining their roles. It will follow the same format as 
`dcp-fusillade/config/roles.json`. Deploy the roles to fusillade using the script `dcp-fusillade/scripts/setup_fusillade.py`. You will need a service 
account with permission to create and modify roles in fusillade to run the script. Contact trent.smith@chanzuckerberg.com for a service account.
 
## DCP Fusillade Organization Management Convention

In `dcp-fusillade/config/`, a directory named `fusillade` will contain a `groups` directory with all of the groups.
Initially the `groups` directory will only have one group which is `user_default`. All users are added to this group
when they are first created.

## Guidelines

### Group and Role Name Convention

- For component specific groups, name it as follows: `{component}-{name}`
- For DCP wide groups, name it as follows: `DCP-{name}`

**Note:** `group/user_default`, `role/fusillade_admin`, and `role/default_user` do not follow this naming convention.
 See [using fusillade as a service](https://github.com/HumanCellAtlas/fusillade#using-fusillade-as-a-service) for 
 more information.

## Component Dev Environment

DCP Components should use the Fusillade testing environment to test their dev code. This is to ensure relative 
stability when developing for the DCP.

All other component stages should use fusillade integration, staging, and production respectively.

## Resource

For resource set the **partition** to `hca`, set your **service** name to the name of your component, and set the 
**account-id** to the deployment stage. All other fields can be used as needed or use \* for wild cards. Resource names
 are case sensitive. See [fusillade policies](https://github.com/HumanCellAtlas/fusillade#policies) to learn more.

### Examples

- **arn**:**hca**:**fusillade**:region:**dev**:resource
- **arn**:**hca**:**dss**:region:**staging**:resourcetype/resource
- **arn**:**hca**:**query**:region:**integration**:resourcetype/resource/qualifier
- **arn**:**hca**:**ingest**:region:**prod**:resourcetype/resource:qualifier
- **arn**:**hca**:**azul**:region:**dev**:resourcetype:resource
- **arn**:**hca**:**matrix**:region:**staging**:resourcetype:resource:qualifier

All fields in **bold** must be used. All other fields are free to use by the component.

## Tools Needed

### Fusillade Setup

```bash
$ ./scripts/setup_fusillade.py -h
usage: setup_fusillade.py [-h] --file FILE [--secret SECRET] [--dry-run]
                          [--force]
                          stage

This scripts updates groups, roles, and users deployed to a fusillade
instance. Roles will be created or updated if specified in the configuration.
Users will be added or removed from a group if specified in the group. Roles
will be added or removed from a group as needed. Users will be created as
needed. If a role does not exist in fusillade and is not in the configuration,
it will not be added to the group. To use you must have a google service
account that has been authorized to create and modify groups and users in
fusillade.

positional arguments:
  stage            The stage of fusillade you would like apply the
                   configuration.

optional arguments:
  -h, --help       show this help message and exit
  --file FILE      A file containing a fusillade configuration.
  --secret SECRET  secretId of a service account in AWS with permission to
                   modify groups in the fusillade deployment
  --dry-run, -d    See the changes without applying them.
  --force, -f      Makes the changes without requiring the user to confirm.
```

## How To?

### As a component of the DCP, how do I control access to my resources?

1. Define what actions and resources you'd like to control. Actions should take
   the form `{component}:{Action}`, for example to get a bundle from the DSS
   the action could be `dss:GetBundle`. Resources are what actions affect. The
   same action can be applied to multiple different resources. For the resource,
   use the AWS ARN format.

1. Define the different types of users you need to support based on what
   actions and resource they will need permission for. The user types that you
   define will become roles. 

1. Create a file `roles.json` to house the roles your service supports. Using
   the resource and actions previously define, write a policy in the AWS IAM
   policy format that express what each role can do. If it isn't explicitly
   stated, it is assumed the user with this role does not have permission. For
   the resource field, `*` can be used as a wild card in the same way it's used
   in AWS IAM policies. Here is an example `roles.json` file:

   ```json
   {
     "roles": {
       "role_1234": {
         "policy": {
           "Version": "2012-10-17",
           "Statement": [
             {
               "Effect": "Allow",
               "Action": [
                 "fake:GetUser"
               ],
               "Resource": "arn:hca:fus:*:*:user/${fus:user_email}/*"
             }
           ]
         }
       },
       "another_role": {
         "policy": {
           "Version": "2012-10-17",
           "Statement": [
             {
               "Sid": "fus_user",
               "Effect": "Disallow",
               "Action": [
                 "fake:GetUser"
               ],
               "Resource": "arn:hca:fus:*:*:user/${fus:user_email}/*"
             }
           ]
         }
       }
     }
   }
   ```
   
1. Run the script `setup_fusillade.py {stage} --file roles.json` to add your roles to fusillade. It's important to 
   check that the role name's have not already been used by another component. You can check by run this script locally
   and check if you would be replacing an existing role's permissions.

1. Users should now be assigned to the new roles. The preferred method of adding users
   to a role is to assign the role to a group and add users to that group (although users
   may be granted roles directly). In the DCP, groups are managed in the 
   [dcp-fusillade](https://github.com/HumanCellAtlas/dcp-fusillade) repo. 

### As a DCP operator how do I had groups to the DCP?

A service account with permission to create and modify fusillade groups is
required to perform this process.

1. In `dcp-fusillade/config` create or modify a file named `groups.json`. Here is an example of the contents of a 
   `groups.json` file:

   ```json
   {
     "groups": {
       "name_of_the_group": {
         "description": "a description of the group",
         "users": [
           "a_list_of_user_emails@example.example",
           "a_list_of_service_account_emails@example.example"
         ],
         "roles": [
           "the_roles_assigned_to_this_group"
         ]
       },
       "another_group": {
         "description": "a different description",
         "users": [
           "a_list_of_user_emails@example.example"
         ],
         "roles": [
           "the_roles_assigned_to_this_group",
           "more_roles"
         ]
       }
     }
   }
   ``` 

1. In DCP infra run the script `setup_fusillade.py {stage} --file groups.json`
   to add your group to Fusillade. If any roles specified in the group do not
   exist, they will not be added to the group. If any user specified in the group
   are not in the group, they will be added to the group.

### As a DCP operator how do I remove a role from a group?
#### Option 1: Using `setup_fusillade.py`
1. Remove the role from the group defined in `dcp-fusillade/config/groups.json`. 
1. Run the script `setup_fusillade.py {stage} --file groups.json`. Alternatively if using CICD, make a pull request 
   with the changes and allow your CICD flow to apply the changes.

#### Option 2: Using API
1. Use the `PUT /v1/group/{group_id}/roles` endpoint to remove a role from a group. This must be done using a user 
   account or service account that has permission to modify groups.

### As a DCP operator how do I remove a user from a group?
#### Option 1: Using `setup_fusillade.py`
1. Remove the user from the group defined in `dcp-fusillade/config/groups.json`. 
1. Run the script `setup_fusillade.py {stage} --file groups.json`. Alternatively if using CICD, make a pull request 
   with the changes and allow your CICD flow to apply the changes.

#### Option 2: Using API
1. Use the `PUT /v1/user/{user_id}/groups` endpoint to remove a user from a group. This must be done using a user 
   account or service account that has permission to modify users.

### As a DCP operator how do I give a user or service account permissions?
#### Option 1: Using `setup_fusillade.py`
1. Add the user to the group defined in `dcp-fusillade/config/groups.json` that has the desired permissions. 
1. Run the script `setup_fusillade.py {stage} --file groups.json`. Alternatively if using CICD, make a pull request 
   with the changes and allow your CICD flow to apply the changes.

#### Option 2: Using API
1. Use the `PUT /v1/user/{user_id}/groups` endpoint to add a user to a group. This must be done using a user 
   account or service account that has permission to modify users.

### As a DCP component how do I give all new users a default level of access to the DCP?
1. In `dcp-fusillade/config/groups.json` add a role to the group *default_user* that provides the permissions the 
   desired permissions. All new and existing users will be assigned to this group.
1. Run the script `setup_fusillade.py {stage} --file groups.json`. Alternatively if using CICD, make a pull request 
   with the changes and allow your CICD flow to apply the changes.

#### Option 2: Using API
1. Use the `PUT /v1/group/default_user/roles` endpoint to add or remove a role in a group. This must be done using a 
   user account or service account that has permission to modify users.
   
### As a DCP component how do I test my permissions?

1. Create a service account with permission to use the fusillade `POST /v1/policies/evaluate` endpoint.
1. Create a role and add it to the fusillade deployment
1. Assign the roles to a user directly, or to a group with the user is a member.
1. Using an authorized service account make a request to fusillade `POST /v1/policies/evaluate` with a user assigned 
   that role as the principal in the request.

## Unresolved Questions

- Does this process work for all of the existing components' deployment process?
- Does this provide enough guidance for components to integrate fusillade?
- What environment should be used for component development testing? Should a new one be created? 
- *What aspects of the design do you expect to clarify later during iterative development of this RFC?*

## Drawbacks and Limitations [optional]

- This will add additional processes and impose additional conventions on the DCP.
- Component roles and DCP groups live in separate repositories. This will
  require two PRs to add a new role, but only one PR to modify an existing role.
- Having components use fusillade staging to test both their dev and staging
  environments could be problematic.

## Alternatives [optional]

*Highlight other possible approaches to delivering the value proposed in this RFC.*

- Manage fusillade configuration in each component repo. Components will need
  to be careful not to interfere with other components permissions.

## Instructions

1. Install requirements: `$ pip install -r requirements.txt`
1. Set the deployment: `$ export DEPLOYMENT=dev`
1. Setup service account: `$ make deploy-infra`
1. Assign that service account 
