deploy:
	# Currently not using this gcp-credential for anything
	# aws secretsmanager get-secret-value --secret-id ${GCP_SERVICE_ACCOUNT_KEY_SECRET_ID} | jq -r .SecretString > app/gcp-credentials.json
	./build_zappa_settings.sh
	cat zappa_settings.json
	zappa update
	python inject-apig.py

apigateway:
	python inject-apig.py