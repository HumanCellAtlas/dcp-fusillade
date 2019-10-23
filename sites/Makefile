include ../common.mk

deploy:
	git clean -df chalicelib vendor
	cp -R ../monitor  chalicelib
	./build_deploy_config.sh
	chalice deploy --no-autogen-policy --stage $(DSS_INFRA_TAG_STAGE) --api-gateway-stage $(DSS_INFRA_TAG_STAGE)
