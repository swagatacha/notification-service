import http.client
import json
import urllib
from commons import config, restclient, NotificationLogger
from commons.utils import retry

log_clt = NotificationLogger()
logger = log_clt.get_logger(__name__)

class Whatsapp:
    def __init__(self, wa_header=None):
        self.wa_header = wa_header or config.WA_DEFAULT__SRC

    @retry(max_retries=3, delay=1, backoff=2)
    def send_wa_infobip(self, template_name, header_content, body_content, buttons_content, mobileno):
        try:
            if mobileno is None:
                msg = "MobileNo is not valid"
                return msg
            if template_name is None:
                msg = "Template is not valid"
                return msg
            
            apiUrl = config.INFOBIP_API_URL
            conn = http.client.HTTPSConnection(apiUrl)
            jsonData = {
                        "messages": [
                            {
                                "from": config.WA_SENDER,
                                "to": mobileno,
                                "content": {
                                    "templateName": template_name,
                                    "templateData": {},
                                    "language": "en_GB"
                                }
                            }
                        ]
                    }
            
            json_template = jsonData["messages"][0]["content"]["templateData"]
            if body_content and isinstance(body_content, list) and len(body_content) >0:
                json_template["body"] = {"placeholders": body_content}

            if header_content and isinstance(header_content, dict):
                header = {
                        "type": header_content['format'].upper(),
                        "mediaUrl": header_content['link']
                    }
                json_template["header"] = header

            if buttons_content and isinstance(buttons_content, list) and len(buttons_content) > 0:
                json_template["buttons"] = buttons_content

            payload = json.dumps(jsonData)

            headers = {
                'Authorization': f'{config.INFOBIP_AUTH_KEY}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            conn.request("POST", "/whatsapp/1/message/template", payload, headers)
            res = conn.getresponse()
            logger.info(f'wa api response code:{res.status}')
            
            data = res.read()

            return data.decode("utf-8"), res.status
        except Exception as e:
            logger.error(f"Exception in send_wa_infobip: {str(e)}")
            raise e
    
    @retry(max_retries=3, delay=1, backoff=2)
    def send_wa_connectexpress(self, template_name, header_content, body_content, mobileno):
        try:
            if mobileno is None:
                return f'MobileNo is not valid'
            if template_name is None:
                return f'Template is not valid'
            
            apiUrl  = config.CONNECT_EXPRESS_API_URL
            conn = http.client.HTTPSConnection(apiUrl)

            template = {"id": template_name}
            if body_content and isinstance(body_content, list) and len(body_content) >0:
                template["params"] = body_content

            payload = {
                'template': json.dumps(template),
                'source': config.WA_SENDER,
                'destination': mobileno,
                'src.name': self.wa_header
            }

            if header_content is not None:
                payload['message'] = json.dumps({"image":{"link":f"{header_content['link']}"},"type":f"{header_content['format'].lower()}"})

            headers = {
                'accept': 'application/json',
                'apikey': f'{config.CONNECT_EXPRESS_KEY}',
                'content-type': 'application/x-www-form-urlencoded'
            }

            conn.request("POST", "/wa/api/v1/template/msg", urllib.parse.urlencode(payload), headers)
            res = conn.getresponse()
            logger.info(f'wa api response code:{res.status}')

            data = res.read()
            return data.decode("utf-8"), res.status
        except Exception as e:
            logger.error(f"Exception in send_wa_connectexpress: {str(e)} for mobileno: {mobileno}")
            raise e
        
    @retry(max_retries=3, delay=1, backoff=2)
    def send_wa_smartping(self, template_name, header_content, body_content, buttons_content, mobileno):
        try:
            if mobileno is None:
                return f'MobileNo is not valid'
            if template_name is None:
                return f'Template is not valid'
            
            apiUrl  = config.SMART_PING_API_URL
            conn = http.client.HTTPSConnection(apiUrl)

            jsonData = {
                            "to": mobileno,
                            "type": "template",
                            "template": {
                                "language": {
                                "policy": "deterministic",
                                "code": "en"
                                },
                                "name": template_name,
                                "components": []
                            }
                        }

            json_template = jsonData["template"]["components"]
            if body_content and isinstance(body_content, list) and len(body_content) >0:
                body = {
                            "type": "body",
                            "parameters": []
                        }
                for params in body_content:
                    body["parameters"].append({
                                    "type": "text",
                                    "text": params
                                })
                json_template.append(body)

            if header_content and isinstance(header_content, dict):
                header = {
                            "type": "header",
                            "parameters": [
                                {
                                    "type": header_content["format"].lower(),
                                    "image": {
                                        "link": header_content["link"]
                                    }
                                }
                            ]
                        }
                json_template.append(header)

            if buttons_content and isinstance(buttons_content, list) and len(buttons_content) > 0:
                for btn in buttons_content:
                    buttons= {
                                    "type": "button",
                                    "sub_type": "url",
                                    "index": "1",
                                    "parameters": [
                                    {
                                        "type": "text",
                                        "text": "part-of-the-link"
                                    }
                                    ]
                                }
                json_template.append(buttons_content)
            
            payload = json.dumps(jsonData)

            headers = {
                'Content-Type': "application/json",
                'Accept': "application/json",
                'Authorization': f"Bearer {config.SMART_PING_AUTH_KEY}"
            }

            conn.request("POST", "/v1/messages", urllib.parse.urlencode(payload), headers)
            res = conn.getresponse()
            logger.info(f'wa api response code:{res.status}')

            data = res.read()
            return data.decode("utf-8"), res.status
        except Exception as e:
            logger.error(f"Exception in send_wa_connectexpress: {str(e)} for mobileno: {mobileno}")
            raise e