import json
from datetime import datetime, timedelta

from commons import config
from dal.sql.sql_dal import NoSQLDal
from schemas.v1.service_provider import DalProviderDetail


class ProviderChange:
    SUCCESS_STATUS = ["DELIVERED_TO_HANDSET", "DELIVRD"]
    THRESHOLD_RATE = 90

    def __init__(self):
        self.__dal = NoSQLDal()
        self.evaluate_and_switch_provider()

    def evaluate_and_switch_provider(self):
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        logs = self.__dal.get_log(one_hour_ago)

        if not logs:
            print("No SMS logs found for the past hour.")
            return

        total = len(logs)
        successful = self.__count_successful_logs(logs)
        success_rate = (successful / total) * 100

        print(f"Total: {total}, Successful: {successful}, Success rate: {success_rate:.2f}%")

        self.__ensure_providers_initialized()

        if success_rate < self.THRESHOLD_RATE:
            self.__switch_to_alternative_provider()

    def __count_successful_logs(self, logs):
        count = 0
        for log in logs:
            if log.get("finalStatus") in self.SUCCESS_STATUS and log.get("http_status") == 200:
                count += 1
        return count

    def __ensure_providers_initialized(self):
        providers = self.__dal.get_provider_info()

        if isinstance(providers, list) and not providers:
            try:
                providers = json.loads(config.SMS_PROVIDERS)
                sorted_providers = sorted(providers, key=lambda x: x["priority"])

                for provider in sorted_providers:
                    try:
                        data_dict = {
                            "name": provider['name'],
                            "isActive": provider['priority'] == 1,
                            "createdBy": 10001,
                            "CreatedAt": datetime.utcnow().isoformat()
                        }
                        provider_obj = DalProviderDetail(**data_dict)
                        self.__dal.service_provider_add(provider_obj)
                    except Exception as e:
                        print(f"Failed to add provider '{provider['name']}': {str(e)}")

            except json.JSONDecodeError as e:
                print(f"Error loading providers from config: {str(e)}")

    def __switch_to_alternative_provider(self):
        providers = self.__dal.get_provider_info()
        inactive_providers = [p for p in providers if not p.get('isActive')]

        if not inactive_providers:
            print("No alternative provider found to switch to.")
            return

        new_provider = inactive_providers[0]
        provider_id = new_provider.get("_id")

        if provider_id:
            result = self.__dal.set_provider_active(provider_id)
            print(f"Switched SMS provider to {new_provider['name']}, modified_count: {result}")
        else:
            print("Selected provider does not have a valid '_id' field.")


if __name__ == "__main__":
    ProviderChange()
