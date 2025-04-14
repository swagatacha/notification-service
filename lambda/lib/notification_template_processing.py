import csv
import json
import requests
import datetime
from lib.helper import string_character_check, event_validate, user_type_validate
from schemas.v1.template_adding import TemplateAddRequest, TemplateAddApiRequest, ParameterEncoder
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from enum import Enum

HOST = "127.0.0.1"
PORT = "8000"
num = 5

DEFAULT_TIMEOUT = 1

mandatory_columns = ["Event", "ActionBy", "TemplateId", "Header","SMSContent","PushContent","EmailContent"]


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        try:
            timeout = kwargs.get("timeout")
            if timeout is None:
                kwargs["timeout"] = self.timeout
            return super().send(request, **kwargs)
        except ValueError:
            print(ValueError)


retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST"])
http = requests.Session()
http.mount("http://", TimeoutHTTPAdapter(max_retries=retries))


def is_valid_input(column_value_mapping: dict):
    if not user_type_validate(column_value_mapping):
        return False

    if not event_validate(column_value_mapping):
        return False

    if column_value_mapping['CreatedBy'] is None or not string_character_check(
            column_value_mapping['CreatedBy'],
            '[A-Za-z0-9]+$'):
        return False

    return True


def parse_to_template_add_request(data: list, header: list):
    column_value_mapping = {
        "Event": None,
        "PaymentType": None,
        "ActionBy": None,
        "TemplateId": None,
        "Header": None,
        "SMSContent": None,
        "CreatedBy": None,
        "PushContent": None,
        "EmailContent": None,
        "CreatedAt": None
    }
    current_time = datetime.datetime.now().isoformat()
    for idx in range(len(header)):
        column = header[idx]
        value = data[idx]

        if len(value) == 0:
            pass
        else:
            if column in ["Event", "PaymentType", "ActionBy", "TemplateId", "Header", 
                          "SMSContent", "CreatedBy", "PushContent", "EmailContent"]:
                column_value_mapping[column] = value
                column_value_mapping["CreatedAt"] = current_time
            else:
                raise Exception("unknown column")

    if not is_valid_input(column_value_mapping):
        raise Exception("not valid input")
    return TemplateAddRequest(column_value_mapping)


def is_valid_header(data):
    if len(data) != len(set(data)):
        raise Exception("duplicate columns present")
    for value in mandatory_columns:
        if value not in data:
            raise Exception("field is missing")


def read_csv_file(path_name: str):
    template_requests = []
    with open(path_name , mode='r') as file:
        csv_file = csv.reader(file)
        header = next(csv_file)
        header = [column for column in header]
        is_valid_header(header)

        for row in csv_file:
            if len(row) == 0:
                next(csv_file)
            template_requests.append(parse_to_template_add_request(row, header))
    return template_requests



def process_request(path_name: str):
    template_data = read_csv_file(path_name)

    for index in range(0, len(template_data), 50):
        start_index = index
        end_index = index + 50

        if end_index > len(template_data):
            end_index = len(template_data)

        batch_requests = template_data[start_index:end_index]
        api_call(batch_requests)

def api_call(batch_requests: list):
    parameter = TemplateAddApiRequest(batch_requests)
    print(json.dumps(parameter, cls=ParameterEncoder))
    # try:
    #     response = http.post("http://" + HOST + ":" + PORT + "/api/v1/wallet/batch/credit",
    #                          data=json.dumps(parameter, cls=ParameterEncoder),
    #                          headers={'X-Idempotent-Id': file_name},
    #                          )
    #     print(response.status_code)
    #     print(response.json())
    # except Exception as err:
    #     print(err)

if __name__ == "__main__":
    try:
        process_request('data/template_v1.csv')
    except Exception as e:
        print(e)
