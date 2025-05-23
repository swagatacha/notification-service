import base64
import boto3
from botocore.exceptions import ClientError
import json
from commons.config import AWS_SECRET_REGION_NAME
import logging


class AwsSecret:
    def __init__(self, secret_name, region_name):
        self.secret_name = secret_name
        self.region_name = region_name

    def get_secret(self):
        '''
        Get AWS Secret directly by API calling, No use of cache.
        :return: dict
        '''
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=self.region_name,
        )
        secret = ""

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=self.secret_name
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logging.info("The requested secret " + self.secret_name + " was not found")
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                logging.info("The request was invalid due to:"+e)
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                logging.info("The request had invalid params:"+e)
            elif e.response['Error']['Code'] == 'DecryptionFailure':
                logging.info("The requested secret can't be decrypted using the provided KMS key:"+e)
            elif e.response['Error']['Code'] == 'InternalServiceError':
                logging.info("An error occurred on service side:"+e)
        else:
            if 'SecretString' in get_secret_value_response:
                secret = get_secret_value_response['SecretString']
            else:
                secret = base64.b64decode(get_secret_value_response['SecretBinary'])
        return secret


class ExtractSecret:
    def __init__(self, secret_name, region_name=AWS_SECRET_REGION_NAME, skip_cache=False):
        self.__secret_data = AwsSecret(secret_name=secret_name, region_name=region_name).get_secret()

    def get_secret_data(self):
        return self.__secret_data



