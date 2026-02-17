import boto3
import json
from botocore.exceptions import ClientError
from vault.agent_services.utilities.env_loader import load_env

def get_aws_secret(parameter_name, region_name=None):
    """
    Retrieves a parameter from AWS SSM Parameter Store and returns the plain text value.
    If the value is a JSON string, it returns a dictionary.
    """
    # Load AWS Region from env if not provided
    if region_name is None:
        region_name = load_env("AWS_REGION")

    # Create an SSM client
    session = boto3.session.Session()
    client = session.client(
        service_name='ssm',
        region_name=region_name
    )

    try:
        # WithDecryption=True handles SecureStrings; 
        # it is ignored for standard Strings, so it's safe to keep.
        response = client.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        
        raw_value = response['Parameter']['Value']

        # Attempt to parse as JSON; if it fails, return as plain text string
        try:
            return json.loads(raw_value)
        except (json.JSONDecodeError, TypeError):
            return raw_value

    except ClientError as e:
        print(f"Error retrieving SSM parameter {parameter_name}: {e}")
        raise e