from app.services.parser import extract_api_from_nodejs, generate_api_specs_for_django
from app.schema.api_schema import ApiSpecsResponseModel


class Parser:

    def __init__(self, repo_url: str, framework_type: str) -> None:
        self.repo_url = repo_url
        self.framework_type = framework_type

    def parse(self):
        # invoke framework parser types
        if self.framework_type.lower() == 'nodejs':
            return self.parse_nodejs()
        elif self.framework_type.lower() == 'django':
            return self.parse_django()
        else:
            raise ValueError(
                "Unsupported framework type. Use 'nodejs' or 'django'.")

    def parse_nodejs(self) -> ApiSpecsResponseModel:
        return extract_api_from_nodejs(self.repo_url)

    def parse_django(self) -> ApiSpecsResponseModel:
        return generate_api_specs_for_django(self.repo_url)
