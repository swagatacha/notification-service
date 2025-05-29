from json import JSONEncoder
from typing import List, Optional, Any
from pydantic import BaseModel

class ProviderDetail(BaseModel):
    name:str
    isActive:bool
    createdBy: str

class DalProviderDetail(ProviderDetail):
    CreatedAt: str

class ServiceProviders(BaseModel):
    providerList:List[ProviderDetail]
