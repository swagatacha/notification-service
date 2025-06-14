import os
from dotenv import load_dotenv

load_dotenv()

THREAD_POOL_SIZE=os.getenv("THREAD_POOL_SIZE")
CUSTOMER_CARE = os.getenv("CUSTOMER_CARE")
AWS_SECRET_REGION_NAME = os.getenv("AWS_SECRET_REGION_NAME")
# Read RabbitMQ configuration from environment variables
RABBITMQ_CONNECTION_POOL = os.getenv("RABBITMQ_CONNECTION_POOL", "false").lower() == "true"
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT"))
RABBITMQ_MANAGEMENT_PORT = int(os.getenv("RABBITMQ_MANAGEMENT_PORT")) 
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME")
MSG_TTL_MS = os.getenv("MSG_TTL_MS")
REQUEUE_MAX_RETRIES=int(os.getenv("REQUEUE_MAX_RETRIES"))
# Read SMS Provider Details from environment variables
SMS_DEFAULT_HEADER = os.getenv("SMS_DEFAULT_HEADER")
SMS_PROVIDERS = os.getenv("SMS_PROVIDERS")
ACTIVE_SMS_PROVIDER = os.getenv("ACTIVE_SMS_PROVIDER")
INFOBIP_API_URL = os.getenv("INFOBIP_API_URL")
INFOBIP_AUTH_KEY = os.getenv("INFOBIP_AUTH_KEY")
VFIRST_API_URL = os.getenv("VFIRST_API_URL")
VFIRST_USERNAME = os.getenv("VFIRST_USERNAME")
VFIRST_PASSWORD = os.getenv("VFIRST_PASSWORD")
CONNECT_EXPRESS_API_URL = os.getenv("CONNECT_EXPRESS_API_URL")
CONNECT_EXPRESS_KEY = os.getenv("CONNECT_EXPRESS_KEY")
SMART_PING_API_URL = os.getenv("SMART_PING_API_URL")
SMART_PING_AUTH_KEY = os.getenv("SMART_PING_AUTH_KEY")
SMART_PING_USERNAME = os.getenv("SMART_PING_USERNAME")
SMART_PING_PWD = os.getenv("SMART_PING_PWD")
# Read EMAIL Provider Details from environment variables
SMTP_SERVER_HOST = os.getenv("SMTP_SERVER_HOST")
SMTP_SERVER_PORT = os.getenv("SMTP_SERVER_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_EMAIL_FROM = os.getenv("SMTP_EMAIL_FROM")
# Read MongoDB Details from environment variables
WA_DEFAULT__SRC = os.getenv("WA_DEFAULT__SRC")
WA_SENDER = os.getenv("WA_SENDER")
mongodb = {
    'auth_enabled': eval(os.getenv('MONGO_AUTH_ENABLED')),
    'socket': os.getenv('MONGO_SOCKET'),
    'username': os.getenv('MONGO_USER'),
    'password': os.getenv('MONGO_PASWD'),
    'dbname': os.getenv('MONGO_DBNAME'),
    'auth_mechanism': os.getenv('MONGO_AUTH_MECHANISM'),
    'auth_source': os.getenv('MONGO_USER'),
    'sspl_db': os.getenv('SSPL_DBNAME'),
}
# Read Redis Details
redis = {
    'host': os.getenv('REDIS_HOST'),
    'port': int(os.getenv('REDIS_PORT'))
}

STATUS_PRIORITY = {
    'order_placed': 1,
    'order_confirmed': 2,
    'order_shipped': 3,
    'order_delivered': 4,
    'order_cancelled': 5
}

TERMINATION_STATES = {"order_cancelled", "order_delivered", "customer_denied", "payment_failed"}
HOME_PAGE_URL= os.getenv("HOME_PAGE_URL")
SHORT_URL_PATH= os.getenv("SHORT_URL_PATH")