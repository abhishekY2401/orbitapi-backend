from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class RequestDataModel(BaseModel):
    body: Dict[str, Any] = {}
    params: Dict[str, Any] = {}
    headers: Dict[str, Any] = {}
    query: Dict[str, Any] = {}


class ResponseDataModel(BaseModel):
    status_code: int
    body: Dict[str, Any] = {}


class ApiSpecModel(BaseModel):
    endpoint: str
    method: str
    controller_signature: str
    controller_code: str
    request_data: RequestDataModel
    expected_response: ResponseDataModel
    auth_required: bool = False
    db_state: Optional[str] = ''


class ApiSpecsResponseModel(BaseModel):
    api_specs: List[ApiSpecModel]


class ParseRequestModel(BaseModel):
    repo_url: str
    framework_type: str
