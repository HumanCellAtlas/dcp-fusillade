import boto3
import jmespath
import json
import os

apigateway_client = boto3.client("apigateway")
lambda_client = boto3.client("lambda")
sts_client = boto3.client("sts")
stage = os.getenv("FUS_DEPLOYMENT_STAGE")
lambda_name = os.getenv('DCP_LAMBDA_NAME')
aws_region = os.getenv("AWS_DEFAULT_REGION")
aws_account_id =  sts_client.get_caller_identity().get("Account")


# There is an order to things.
def get_api_gateway(gateway_name: str):
    rest_apis = apigateway_client.get_rest_apis(limit=500).get("items")
    for api in rest_apis:
        if api['name'] == gateway_name:
            return api
            break
    return None


def get_api_resource(api_id, resource_path):
    resources = apigateway_client.get_resources(restApiId=api_id).get("items")
    resource_found = None
    for resource in resources:
        if resource['path'] == resource_path:
            resource_found = resource
            break
    return resource_found

def create_api_resource(api_id, parent_id, resource_part):
    created_resource = apigateway_client.create_resource(restApiId=api_id,parentId=parent_id,pathPart=resource_part)
    return created_resource

def put_method(api_id, resource_id):
    method = apigateway_client.put_method(restApiId=api_id, resourceId=resource_id, httpMethod='HTTP',authorizationType='NONE')
    return method

def put_integration(api_id, resource_id, uri):
    integration = apigateway_client.put_integration(restApiId=api_id, resourceId=resource_id, uri=uri, httpMethod="ANY",type="AWS_PROXY",integrationHttpMethod="POST")

def put_api_method_response(api_id, resource_id):
    resp = apigateway_client.put_method_response(restApiId=api_id, resourceId=resource_id,httpMethod='ANY', statusCode=200, repsonseModels={"application/json": "EMPTY"}) # TODO fix this dict maybe
    return resp

def put_api_integration_response(api_id, resource_id):
    resp = apigateway_client.put_integration_response(restApiId=api_id, resourceId=resource_id,httpMethod='ANY', statusCode=200, repsonseModels={"application/json": ""}) # TODO fix this dict maybe
    return resp

def put_lambda_permission(function_name, source_arn):
    resp = lambda_client.add_permission(functionName=function_name, action="lambda/InvokeFunction", principal='apigateway.amazonaws.com', sourceArn=source_arn, statementId=function_name)
    return resp

def deploy_api(api_id):
    resp = lambda_client.create_deployment(region=aws_region, restApiId=api_id, stage=stage)
    return resp

lambda_data = lambda_client.get_function_configuration(functionName=lambda_name)
api_data = get_api_gateway(f'fusillade-{stage}')
api_id = api_data.get('id')
root_resource = get_api_resource(api_data['id'], resource_path='/')
dcp_resource = get_api_resource(api_data['id'],resource_path='/dcp')

integration_path = f'arn:aws:apigateway:{aws_region}:lambda:path/2015-03-31/functions/{lambda_data["FunctionArn"]}/invocations'
source_arn = f'arn:aws:execute-api:{aws_region}:{aws_account_id}:{api_id}/{stage}/POST/dcp'
# check if the api has the injection to the endpoint we want.
if dcp_resource is None:
    # can this var be dcp_resource?
    created = create_api_resource(api_id=api_id,parent_id=root_resource['id'],resource_part='dcp')
    #TODO  might need to pass created['id'] down stream....
    method = put_method(api_id=api_id,resource_id=dcp_resource['id'])
    integration = put_integration(api_id=api_id,resource_id=dcp_resource['id'],uri=integration_path)
    api_method_resp = put_api_method_response(api_id=api_id,resource_id=dcp_resource['id'])
    api_integration_resp = put_api_integration_response(api_id=api_id,resource_id=dcp_resource['id'])
    lambda_permission = put_lambda_permission(function_name=lambda_name,source_arn=source_arn)
    deploy_api_resp = deploy_api(api_id=api_id)
else:
    #TODO retry deployment, take stuff out that does not need to be present. 