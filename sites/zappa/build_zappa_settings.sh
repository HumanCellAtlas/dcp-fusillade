#!/usr/bin/env bash
#
# This script uses the AWS command line to get account information, substitutes it into the IAM policy document
# template, then inserts the policy statements from the policy doc into zappa_settings.json.
# 
# This script should be run with the service account that will run the lambdas.

set -euo pipefail

if [[ -z ${FUS_STAGE_TAG+foo} ]]; then
    echo 'Please run "source environment" in the dcp-fusillade repo root directory before running this command'
    exit 1
fi

export stage=$FUS_STAGE_TAG
export account_id=$(aws sts get-caller-identity | jq -r .Account)

zappa_settings="$(dirname $0)/zappa_settings.json"
zappa_settings_template="$(dirname $0)/zappa_settings_template.json"
iam_policy_template="$(dirname $0)/iam/policy-templates/dcp-fus-lambda.json"

# Step 1: extract "Statement" from IAM policy template
iam_policy_statement_template=$(cat $iam_policy_template | jq .Statement)
# Step 2: substitute env vars in template
iam_policy_statement=$(echo $iam_policy_statement_template | envsubst '$FUS_SECRETS_STORE $account_id $stage')
# Step 3: insert into zappa settings
cat "$zappa_settings_template" | jq ".$stage.extra_permissions = $iam_policy_statement" | sponge "$zappa_settings"

# use TF Bucket for Zappa Deployments
# TODO this might to support prefix in the bucket name...
cat "$zappa_settings" | jq ".$stage.s3_bucket=\"$FUS_TERRAFORM_BACKEND_BUCKET_TEMPLATE\"" |  sponge "$zappa_settings"

# Resource Tagging
export DEPLOY_ORIGIN="$(whoami)-$(hostname)-$(git describe --tags --always)-$(date -u +'%Y-%m-%d-%H-%M-%S').deploy"
cat "$zappa_settings" | jq ".$stage.tags.DSS_DEPLOY_ORIGIN=\"$DEPLOY_ORIGIN\" | \
	.$stage.tags.Name=\"${FUS_PROJECT_TAG}--${FUS_SERVICE_TAG}-${FUS_STAGE_TAG}\" | \
	.$stage.tags.service=\"${FUS_SERVICE_TAG}\"  | \
	.$stage.tags.project=\"$FUS_PROJECT_TAG\" | \
	.$stage.tags.owner=\"${FUS_OWNER_TAG}\" | \
	.$stage.tags.env=\"${FUS_STAGE_TAG}\""  | sponge "$zappa_settings"

# Lambda Env Variables into Config
for ENV_KEY in $EXPORT_ENV_VARS_TO_LAMBDA; do
	export env_val=$(printenv $ENV_KEY)
	cat "$zappa_settings" | jq ".$stage.environment_variables.$ENV_KEY=\"$env_val\"" |  sponge "$zappa_settings"
done

# Always Alpha Sort
cat "$zappa_settings" | jq -S "." | sponge "$zappa_settings"