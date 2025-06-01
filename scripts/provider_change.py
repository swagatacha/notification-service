import json
from commons import config
from dal.sql.sql_dal import NoSQLDal
from datetime import datetime, timedelta

from schemas.v1.service_provider import DalProviderDetail

class ProviderChange:
    def __init__(self):
        self.__dal = NoSQLDal()
        self.SUCCESS_STATUS = ["DELIVERED_TO_HANDSET","DELIVRD"]
        self.THRESOLD_RATE = 90
        self.evaluate_and_switch_provider()

    def evaluate_and_switch_provider(self):
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        logs = self.__dal.get_log(one_hour_ago)

        if not logs:
            print("No SMS logs found for the past hour.")
            return
        total = len(logs)
        successful = sum(
            1 for log in logs if log.get("finalStatus") in self.SUCCESS_STATUS  and log.get("http_status") == 200
        )
        success_rate = (successful / total) * 100

        print(f"Total: {total}, Successful: {successful}, Success rate: {success_rate:.2f}%")
        if success_rate < self.THRESOLD_RATE:
            providers = self.__dal.get_provider_info()
            
            if isinstance(providers, list) and len(providers) == 0:
                providers = json.loads(config.SMS_PROVIDERS)
                sorted_providers = sorted(providers, key=lambda x: x["prority"])
                for provider in sorted_providers:
                    try:
                        data_dict = {
                            "name" : provider['name'],
                            "isActive": True if provider['priority'] == 1 else False,
                            "createdBy": 10001,
                            "CreatedAt" : datetime.utcnow().isoformat()
                        }
                        provider_obj = DalProviderDetail(**data_dict)
                        self.__dal.service_provider_add(provider_obj)
                    except Exception as e:
                        print(f'{provider["name"]} this provider is not added due to {str(e)}')

            alternative_providers = [p for p in providers if not p['isActive']]
            new_provider = alternative_providers[0] if alternative_providers else None

            if new_provider:
                new_provider_id = new_provider["_id"]
                resp = self.__dal.set_provider_active(new_provider_id)
                print(f"Switching SMS provider to {new_provider} modified_count:{resp}")
            else:
                print("No alternative provider found to switch to.")

if __name__ == "__main__":
    ProviderChange()
