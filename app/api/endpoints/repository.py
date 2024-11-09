import os
from fastapi import APIRouter, HTTPException
from app.services.repo_utils import clone_repo, clean_up_repo
from app.schema.api_schema import ParseRequestModel, APISpecification
from app.services.repo_utils import clone_repo, clean_up_repo
from app.parsers.Parser import Parser
from app.database.database import api_collection
from app.test_case_gen import generate_test_cases_for_endpoint
from typing import Dict, List, Any
import traceback

router = APIRouter()


async def find_routes_directory(repo_path: str) -> str:
    """
    Find the directory containing route definitions in the repository
    """
    common_route_paths = [
        'routes',
        'api/routes',
        'src/routes',
        'app/routes',
        'api',
        'endpoints',
        'app/api',
        'app/endpoints'
    ]

    for route_path in common_route_paths:
        full_path = os.path.join(repo_path, route_path)
        if os.path.exists(full_path):
            return full_path

    return repo_path


@router.post("/parse")
async def process_repo_endpoint(request_data: ParseRequestModel):
    repo_url = request_data.repo_url
    framework_type = request_data.framework_type

    # Ensure necessary data is provided
    if not repo_url or not framework_type:
        raise HTTPException(
            status_code=400,
            detail="Missing repo_url or framework_type"
        )

    try:
        # Clone the repository temporarily
        repo_path = await clone_repo(repo_url)
        print(f"Repository cloned at: {repo_path}")

        try:
            # Find the routes directory
            routes_path = await find_routes_directory(repo_path)
            print(f"Routes directory identified at: {routes_path}")

            # Initialize the API Parser
            parser = Parser(
                repo_path=repo_path, framework_type=framework_type, routes_path=routes_path
            )

            # Extract API specifications
            api_specs = parser.parse()

            # Generate test cases for each endpoint
            for endpoint_spec in api_specs:
                test_cases = generate_test_cases_for_endpoint(endpoint_spec)
                endpoint_spec['test_cases'] = test_cases

            # Optionally store in database
            # if api_collection is not None:
            #     await api_collection.insert_many(api_specs)

            return {"api_specs": api_specs}

        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"Error processing repository: {error_trace}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing repository: {str(e)}"
            )

        finally:
            pass
            # Clean up cloned repository
            # await clean_up_repo(repo_path)

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error cloning repository: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cloning repository: {str(e)}"
        )
