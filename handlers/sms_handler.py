import http.client
import json
import urllib
from commons import config, restclient, NotificationLogger
from commons.utils import retry

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

class Sms:
    def __init__(self, sms_header=None):
        self.sms_header = sms_header or config.SMS_DEFAULT_HEADER

    @retry(max_retries=3, delay=1, backoff=2)
    def send_sms_infobip(self, msg, to, principaltempId="" , tempId=""):
        try:
            if to is None:
                msg = "MobileNo is not valid"
                return msg
            if msg is None:
                msg = "SMS Content is not valid"
                return msg
            
            apiUrl = config.INFOBIP_API_URL
            conn = http.client.HTTPSConnection(apiUrl)
            jsonData = {
                "messages": [
                    {
                        "from": self.sms_header,
                        "destinations": [
                            {
                                "to": to
                            }
                        ],
                        "text": msg,
                        "regional": {
                            "indiaDlt": {
                                "principalEntityId": principaltempId,
                                "contentTemplateId": tempId
                            }
                        }
                    }
                ]
            }

            payload = json.dumps(jsonData)

            headers = {
                'Authorization': f'App {config.INFOBIP_AUTH_KEY}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            conn.request("POST", "/sms/2/text/advanced", payload, headers)
            res = conn.getresponse()
            logger.info(f'sms api response code:{res.status}')
            
            data = res.read()

            return json.loads(data.decode("utf-8")), res.status
        except Exception as e:
            logger.error(f"Exception in send_sms_infobip: {str(e)}")
            raise e

    @retry(max_retries=3, delay=1, backoff=2)
    def send_sms_vfirst(self, msg, to):
        try:
            if to is None:
                msg = "MobileNo is not valid"
                return msg
            if msg is None:
                msg = "SMS Content is not valid"
                return msg
    
            apiUrl = f'{config.VFIRST_API_URL}/psms/servlet/psms.Eservice2'
            userName = config.VFIRST_USERNAME
            password = config.VFIRST_PASSWORD
            fromName = self.sms_header

            data = '<?xml version="1.0" encoding="ISO-8859-1"?><!DOCTYPE MESSAGE SYSTEM "http://127.0.0.1:80/psms/dtd/messagev12.dtd"><MESSAGE VER="1.2"><USER USERNAME="{}" PASSWORD="{}"/><SMS UDH="0" CODING="1" TEXT="{}" PROPERTY="0" ID="1">'.format(userName, password, msg)
            for i in range(len(to)):
                data += '<ADDRESS FROM="{}" TO="{}" SEQ="{}" TAG="some clientside random data"/>'.format(fromName,to[i], i+1)
            
            data += '</SMS></MESSAGE>'


            resp_text, resp = restclient.post(url = apiUrl,
                    data = {'data' : data, 'action' : 'send'}, 
                    headers = {'Content-Type' : 'application/x-www-form-urlencoded'}, ssl=True)
            
            return resp_text, resp.status_code
        except Exception as e:
            logger.error(f"Exception in send_sms_vfirst: {str(e)}")
            raise e
    
    @retry(max_retries=3, delay=1, backoff=2)
    def send_sms_connectexpress(self, msg, to):
        try:
            if to is None:
                msg = "MobileNo is not valid"
                return msg
            if msg is None:
                msg = "SMS Content is not valid"
                return msg
            
            apiUrl  = f'{config.CONNECT_EXPRESS_API_URL}/api/v3/index.php'
            apiKey = config.CONNECT_EXPRESS_KEY

            data = {'to':to, 'message':urllib.parse.quote_plus(msg), 'method':'sms', 'api_key':apiKey, 'sender':self.sms_header, 'format':'json'}
            resp_text, resp = restclient.post(url=apiUrl, data=data, headers={'Content-Type': 'application/jsonp'}, ssl=True)

            return resp_text, resp.status_code
        except Exception as e:
            logger.error(f"Exception in send_sms_infobip: {str(e)}")
            raise e
        
    @retry(max_retries=3, delay=1, backoff=2)
    def send_sms_smartping(self, msg, to):
        pass