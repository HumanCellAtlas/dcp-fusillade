SHELL:=/bin/bash

api_gateway_id:=$(shell aws apigateway get-rest-apis | jq -r '.items[] | select(.name=="fusillade-${FUS_DEPLOYMENT_STAGE}") | .id')
api_gateway_root_resource_id:=$(shell aws apigateway get-resources --rest-api-id $(api_gateway_id) | jq -r '.items[] | select(.path=="/") | .id')
api_gateway_dcp_resource_id:=$(shell aws apigateway get-resources --rest-api-id $(api_gateway_id) | jq -r '.items[] | select(.path=="/dcp") | .id')
apig-create-resource:
	aws apigateway create-resource --rest-api-id $(api_gateway_id) --parent-id $(api_gateway_root_resource_id) --path-part 'dcp'
put-method:
	aws apigateway put-method --rest-api-id $(api_gateway_id) --http-method GET --resource-id $(api_gateway_dcp_resource_id) --authorization-type NONE

e-a:
	echo $(api_gateway_id)
	echo $(api_gateway_root_resource_id)

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
