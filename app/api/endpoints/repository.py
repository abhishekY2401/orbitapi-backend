from fastapi import APIRouter, HTTPException
from app.services.repo_utils import clone_repo, clean_up_repo
from app.schema.api_schema import ParseRequestModel, ApiSpecsResponseModel
from app.services.repo_utils import clone_repo, clean_up_repo
from app.parsers.Parser import Parser

router = APIRouter()


@router.post("/parse", response_model=ApiSpecsResponseModel)
async def process_repo_endpoint(request_data: ParseRequestModel):
    repo_url = request_data.repo_url
    framework_type = request_data.framework_type

    print(repo_url, "", framework_type)

    # Ensure necessary data is provided
    if not repo_url or not framework_type:
        raise HTTPException(
            status_code=400, detail="Missing repo_url or framework_type")

    # clone the repository temporarily
    repo_path = await clone_repo(repo_url)

    print("Repo path:", repo_path)

    # Instantiate Parser and parse based on framework type
    try:
        print(type(Parser))
        parser = Parser(repo_url=f"{repo_path}",
                        framework_type=framework_type)
        api_specs = parser.parse()
        return {"api_specs": api_specs}
    except Exception as e:
        print(f"Error during parsing: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")
