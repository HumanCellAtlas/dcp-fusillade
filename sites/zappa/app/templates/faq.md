#### Who is this website for?

This website is for DCP operators to add DCP users (service accounts) to existing
DCP groups. This is required for access control. The DCP users, groups, roles, and
resources are handled by [Fusillade](https://github.com/HumanCellAtlas/fusillade).

#### Why am I asked to log in with Github? What permissions does it ask for?

This website is only available to members of the Human Cell Atlas organization (HCA org) on Github.

The website asks you to log in to Github before you can use the website. This is so that it can verify
that you are a member of the HCA org.

The Github OAuth app that performs verification of your HCA org membership will only ask for permission
to see what organizations you are a member of. The OAuth apps cannot see or ask for other information
about you.

#### What happens when this form is submitted?

This website's form makes modifications to the DCP Fusillade configuration files in the
[dcp-fusillade repository on Allspark](https://allspark.dev.data.humancellatlas.org/HumanCellAtlas/dcp-fusillade).

The dcp-fusillade repository stores users, groups, and membership relationships between the two
in a set of Fusillade configuration files (JSON format).

When DCP operators use this form to request a change in a user's group memberships, the form will
open a merge request in the dcp-fusillade repository in Allspark (to make the proposed modifications
to the DCP Fusillade configuration files).

You will receive a link to the final merge request opened in dcp-fusillade once you submit the form.

#### How are different stages handled?

Each stage has its own Github OAuth app, which specifies the corresponding callback URL and has its own
Github OAuth app client ID and client secret.

The deployment stage for this webapp is set by the `FUS_DEPLOYMENT_STAGE` environment variable.
