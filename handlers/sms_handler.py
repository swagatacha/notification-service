import http.client
import json
import logging
import urllib
from commons import config, restclient

logger = logging.getLogger(__name__)

class Sms:
    def __init__(self, sms_header=None):
        self.sms_header = sms_header or config.SMS_DEFAULT_HEADER

    def send_sms_infobip(self, msg, to, principaltempId , tempId=""):
        try:
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

            if res.status != 200:
                logger.error(f"Infobip SMS send failed: {res.status} {res.reason}")
                return None
            
            data = res.read()

            return data.decode("utf-8")
        except Exception as e:
            logger.exception(f"Exception in send_sms_infobip: {str(e)}")
            return None

    def send_sms_vfirst(self, msg, to):
        try:
            apiUrl = config.VFIRST_API_URL
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
            
            return resp_text
        except Exception as e:
            logger.exception(f"Exception in send_sms_vfirst: {str(e)}")
            return None
    
    def send_sms_connectexpress(self, msg, to):
        try:
            apiUrl  = config.CONNECT_EXPRESS_API_URL
            apiKey = config.CONNECT_EXPRESS_KEY

            data = {'to':to, 'message':urllib.parse.quote_plus(msg), 'method':'sms', 'api_key':apiKey, 'sender':self.sms_header, 'format':'json'}
            resp_text, resp = restclient.post(url=apiUrl,data=data,headers={'Content-Type': 'application/jsonp'}, ssl=True)

            return resp_text
        except Exception as e:
            logger.exception(f"Exception in send_sms_infobip: {str(e)}")
            return None