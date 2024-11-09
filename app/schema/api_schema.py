from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class APISpecification(BaseModel):
    endpoint: str
    method: str
    controller_signature: str
    controller_code: str
    request_data: Dict[str, Any]
    expected_response: List[Dict[str, Any]]
    auth_required: bool = False
    test_cases: str
    files: str
    api_schema: Dict[str, Any] = Field(default_factory=dict)
    middleware: List[str]


class ParseRequestModel(BaseModel):
    repo_url: str
    framework_type: str


class ApiSpecsResponseModel(BaseModel):
    api_specs: List[APISpecification]
