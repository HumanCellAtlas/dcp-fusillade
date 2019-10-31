#!/usr/bin/env bash
#
# This script uses the AWS command line to get account information,
# then sets the appropriate IAM permissions in the zappa settings.
# Should run this with a service account.

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

# Step 1: extract Statement from IAM policy template
iam_policy_statement_template=$(cat $iam_policy_template | jq .Statement)
# Step 2: substitute env vars in template
iam_policy_statement=$(echo $iam_policy_statement_template | envsubst '$FUS_SECRETS_STORE $account_id $stage')
# Step 3: insert into zappa settings
cat "$zappa_settings_template" | jq ".$stage.extra_permissions = $iam_policy_statement" > $zappa_settings
