import os
from dotenv import load_dotenv

load_dotenv()

# Read RabbitMQ configuration from environment variables
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))
RABBITMQ_MANAGEMENT_PORT = int(os.getenv("RABBITMQ_MANAGEMENT_PORT")) 
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME")
# Read SMS Provider Details from environment variables
SMS_DEFAULT_HEADER = os.getenv("SMS_DEFAULT_HEADER")
ACTIVE_SMS_PROVIDER = os.getenv("ACTIVE_SMS_PROVIDER")
INFOBIP_API_URL = os.getenv("INFOBIP_API_URL")
INFOBIP_AUTH_KEY = os.getenv("INFOBIP_AUTH_KEY")
VFIRST_API_URL = os.getenv("VFIRST_API_URL")
VFIRST_USERNAME = os.getenv("VFIRST_USERNAME")
VFIRST_PASSWORD = os.getenv("VFIRST_PASSWORD")
CONNECT_EXPRESS_API_URL = os.getenv("CONNECT_EXPRESS_API_URL")
CONNECT_EXPRESS_KEY = os.getenv("CONNECT_EXPRESS_KEY")
# Read EMAIL Provider Details from environment variables
SMTP_SERVER_HOST = os.getenv("SMTP_SERVER_HOST")
SMTP_SERVER_PORT = os.getenv("SMTP_SERVER_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_EMAIL_FROM = os.getenv("SMTP_EMAIL_FROM")
# Read MongoDB Details from environment variables
mongodb = {
    'auth_enabled': eval(os.getenv('MONGO_AUTH_ENABLED')),
    'socket': os.getenv('MONGO_SOCKET'),
    'username': os.getenv('MONGO_USER'),
    'password': os.getenv('MONGO_PASWD'),
    'dbname': os.getenv('MONGO_DBNAME'),
    'auth_mechanism': os.getenv('MONGO_AUTH_MECHANISM')
}