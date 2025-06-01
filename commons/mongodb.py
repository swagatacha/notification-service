from pymongo import MongoClient
from commons import config


class Mongo:
    def __init__(self):
        self.__mongo_dbcon = None
        self.log_filename = __name__
        self.__con()
        
    def __con(self):
        if config.mongodb['auth_enabled']:
            self.__mongo_dbcon = MongoClient(config.mongodb['socket'],
                                              username=config.mongodb['username'],
                                                password=config.mongodb['password'], 
                                                authSource=config.mongodb['auth_source'], 
                                                authMechanism=config.mongodb['auth_mechanism'])
        else:
            self.__mongo_dbcon = MongoClient(config.mongodb['socket'])

    def db(self):
        return self.__mongo_dbcon[config.mongodb['dbname']]
    
    def sspl_db(self):
        return self.__mongo_dbcon[config.mongodb['sspl_db']]

    def close(self):
        if self.__mongo_dbcon:
            try:
                self.__mongo_dbcon.close()
            except Exception as e:
                print(e)
                print("Error while attempting to close mongo connection")

    def __del__(self):
        self.close()