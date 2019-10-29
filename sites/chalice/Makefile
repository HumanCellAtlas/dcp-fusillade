include ../common.mk

deploy:
	git clean -df chalicelib vendor
	cp -R ../controller  chalicelib
	aws secretsmanager get-secret-value --secret-id ${GCP_SERVICE_ACCOUNT_KEY_SECRET_ID} | jq -r .SecretString > chalicelib/gcp-credentials.json
	./build_deploy_config.sh
	chalice deploy --no-autogen-policy --stage $(FUS_STAGE_TAG) --api-gateway-stage $(FUS_STAGE_TAG)
