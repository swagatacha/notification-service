import csv
import json
import requests
import datetime
from lib.helper import string_character_check, event_validate, user_type_validate
from schemas.template_upload import TemplateAddRequest, TemplateAddApiRequest, ParameterEncoder
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from enum import Enum

HOST = "127.0.0.1"
PORT = "8000"
num = 5

DEFAULT_TIMEOUT = 1

mandatory_columns = ["Event", "PaymentType", "ActionBy", "PrincipalTemplateId", "TemplateId", 
                     "Header", "IsSMS", "SMSContent", "CreatedBy", "IsPush", "PushTitle",
                     "PushContent", "PushActionLink", "IsEmail", "EmailSubject", 
                     "EmailContent", "EmailReceipient"]


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
    column_value_mapping = {col: None for col in mandatory_columns}
    current_time = datetime.datetime.now().isoformat()
    for idx in range(len(header)):
        column = header[idx]
        value = data[idx]

        if len(value) == 0:
            pass
        else:
            column_value_mapping[column] = str(value)
            column_value_mapping["CreatedAt"] = current_time

    if not is_valid_input(column_value_mapping):
        raise Exception("Invalid input data")
    return TemplateAddRequest(column_value_mapping)


def is_valid_header(data):
    if len(data) != len(set(data)):
        raise Exception("Duplicate columns found in header")
    for value in mandatory_columns:
        if value not in data:
            raise Exception(f"Missing mandatory field: {value}")


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
    try:
        template_data = read_csv_file(path_name)
        api_call(template_data)

    except Exception as e:
        print(f"Error: {e}")

def api_call(batch_requests: list):
    parameter = TemplateAddApiRequest(batch_requests)
    try:
        response = http.post("http://" + HOST + ":" + PORT + "/api/v1/batch/template/add",
                             json=json.loads(json.dumps(parameter, cls=ParameterEncoder))
                             )
        print(response.status_code)
        print(response.json())
    except Exception as err:
        print(err)

if __name__ == "__main__":
    try:
        process_request('data/template_v1.csv')
    except Exception as e:
        print(e)
