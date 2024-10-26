from fastapi import APIRouter, HTTPException
from app.services.repo_utils import clone_repo, clean_up_repo
from app.schema.api_schema import ParseRequestModel, ApiSpecsResponseModel
from app.services.repo_utils import clone_repo, clean_up_repo
from app.parsers.Parser import Parser
from app.database.database import api_collection
from app.test_case_gen import generate_test_cases_for_endpoint
import traceback

router = APIRouter()


@router.post("/parse", response_model=ApiSpecsResponseModel)
async def process_repo_endpoint(request_data: ParseRequestModel):
    repo_url = request_data.repo_url
    framework_type = request_data.framework_type

    # Ensure necessary data is provided
    if not repo_url or not framework_type:
        raise HTTPException(
            status_code=400, detail="Missing repo_url or framework_type"
        )

    # Clone the repository temporarily
    repo_path = await clone_repo(repo_url)
    print("Repo path:", repo_path)

    # Instantiate Parser and parse based on framework type
    try:
        parser = Parser(repo_url=f"{repo_path}", framework_type=framework_type)
        api_specs = parser.parse()

        # Iterate over each API spec and generate test cases
        for endpoint in api_specs:
            test_cases = generate_test_cases_for_endpoint(endpoint)
            # Attach test cases to each endpoint
            endpoint["test_cases"] = test_cases

        # Optionally insert all endpoints and test cases to the database
        await api_collection.insert_many(api_specs)

        return {"api_specs": api_specs}
    except Exception as e:
        error_trace = traceback.format_exc()
        print("Detailed error trace:", error_trace)
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {error_trace}")
