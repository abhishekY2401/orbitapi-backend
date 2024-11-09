from typing import List, Dict, Any
from app.schema.api_schema import APISpecification
from app.parsers.NodeParser import NodeJSParser
from pathlib import Path


class Parser:
    def __init__(self, repo_path: str, framework_type: str, routes_path: str):
        self.repo_path = repo_path
        self.framework_type = framework_type.lower()
        self.routes_path = Path(routes_path)

    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse the repository and extract API specifications
        """

        parser = NodeJSParser(
            routes_path=str(self.routes_path), repo_path=self.repo_path
        )
        return parser.extract_apis()
