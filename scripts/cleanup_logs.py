from dal.sql.sql_dal import NoSQLDal, logger

class ClenaupLogs:
    def __init__(self):
        self.__dal = NoSQLDal()
        self.__dal.delete_old_logs()

if __name__ == "__main__":
    ClenaupLogs()
