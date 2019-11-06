SHELL:=/bin/bash

account_id:=$(aws sts  get-caller-identity |  jq -r  '.Account')
api_gateway_id:=$(shell aws apigateway get-rest-apis | jq -r '.items[] | select(.name=="fusillade-${FUS_DEPLOYMENT_STAGE}") | .id')
api_gateway_root_resource_id:=$(shell aws apigateway get-resources --rest-api-id $(api_gateway_id) | jq -r '.items[] | select(.path=="/") | .id')
api_gateway_dcp_resource_id:=$(shell aws apigateway get-resources --rest-api-id $(api_gateway_id) | jq -r '.items[] | select(.path=="/dcp") | .id')
deployed_lambda_arn:=$(shell aws lambda get-function-configuration --function-name ${DCP_LAMBDA_NAME} | jq -r ".FunctionArn")


api-create-resource:
	aws apigateway create-resource --rest-api-id $(api_gateway_id) --parent-id $(api_gateway_root_resource_id) --path '/dcp' --path-part "dcp"
put-method:
	aws apigateway put-method --rest-api-id $(api_gateway_id) --http-method ANY --resource-id $(api_gateway_dcp_resource_id) --authorization-type NONE
put-integration:
	aws apigateway put-integration --region ${AWS_DEFAULT_REGION} --rest-api-id $(api_gateway_id) --resource-id $(api_gateway_dcp_resource_id)  --http-method ANY --type AWS_PROXY --integration-http-method POST\
	--uri "arn:aws:apigateway:${AWS_DEFAULT_REGION}:lambda:path//2015-03-31/functions/$(deployed_lambda_arn)/invocations" --credentials

inject-dcp-endpoint:
	if [[ "$(api_gateway_dcp_resource_id)" == "" ]]; then \
		echo inside; \
		$(MAKE) api-create-resource; \
		$(MAKE) put-method; \
		$(MAKE) put-integration; \
	else \
		echo outside; \
		$(MAKE) put-method; \
		$(MAKE) put-integration; \
	fi; \

deploy-zappa:
	$(MAKE) -C sites/zappa deploy

plan-infra:
	source ./environment && $(MAKE) -C infra plan-all

deploy-infra:
	source ./environment && $(MAKE) -C infra apply-all

destroy-infra:
	source ./environment && $(MAKE) -C infra destroy-all
refresh_all_requirements:
	@echo -n '' >| requirements.txt
	@echo -n '' >| requirements-dev.txt
	@if [ $$(uname -s) == "Darwin" ]; then sleep 1; fi  # this is require because Darwin HFS+ only has second-resolution for timestamps.
	@touch requirements.txt.in requirements-dev.txt.in
	@$(MAKE) requirements.txt requirements-dev.txt

requirements.txt requirements-dev.txt : %.txt : %.txt.in
	[ ! -e .requirements-env ] || exit 1
	virtualenv -p $(shell which python3) .$<-env
	.$<-env/bin/pip install -r $@
	.$<-env/bin/pip install -r $<
	echo "# You should not edit this file directly.  Instead, you should edit $<." >| $@
	.$<-env/bin/pip freeze >> $@
	rm -rf .$<-env
	scripts/find_missing_wheels.py requirements.txt # Disable if causing circular dependency issues

requirements-dev.txt : requirements.txt.in

.PHONY: test release docs
