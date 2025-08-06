
from enum import Enum
from typing import Optional


class EStatusCode(str, Enum):
    SUCCESS = "success",
    ERROR = "error"

class Response:
    def __init__(self,
                 status_code: EStatusCode,
                 message: Optional[str]=None,
                 obj_id: Optional[int]=None,
                 obj: Optional[dict]=None,
                 list_obj: Optional[list[dict]]=None):
        self.status = status_code
        self.message = message
        self.obj_id = obj_id
        self.obj = obj
        self.list_obj = list_obj
