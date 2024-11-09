from pathlib import Path
import re
import os
from typing import Optional, Dict, Any, List
from app.schema.api_schema import APISpecification


class NodeJSParser:
    def __init__(self, routes_path: str, repo_path: str):
        self.routes_path = Path(routes_path)
        self.repo_path = repo_path
        self.api_specifications: List[APISpecification] = []
        self.processed_files: set = set()
        self.middleware_patterns = {
            'express': r'app\.use\((.*?)\)',
            'router': r'router\.use\((.*?)\)',
        }
        self.route_patterns = [
            r"router\.(get|post|put|patch|delete)\(['\"](.+?)['\"],\s*(\w+|\(.*?\)\s*=>\s*\{.*?\})"
        ]

    def _read_file_content(self, file_path: Path) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""

    def _extract_controller_imports(self, content: str) -> Dict[str, str]:
        controller_imports = {}

        require_matches = re.findall(
            r"(?:const|let|var)\s*{?\s*([\w\s,]+)\s*}?\s*=\s*require\(['\"](.+?)['\"]\);", content
        )
        for controllers, file_path in require_matches:
            controller_names = [
                name.strip() for name in controllers.split(",")
            ]
            for controller_name in controller_names:
                controller_imports[controller_name] = file_path

        print(controller_imports)

        return controller_imports

    def _get_controller_code(self, controller_name: str, controller_file: str) -> str:

        controller_path = os.path.join(self.repo_path, controller_file)

        # Check if the path has no extension; if so, add .js extension
        if not controller_path.endswith(".js"):
            controller_path += ".js"
        print(f"controller file: {controller_path}")

        # controller_file_path = os.path.normpath(controller_file_path)
        controller_path = controller_path.split("..")

        base_path = controller_path[0].split('\\')

        base_path = "/".join(base_path)

        controller_file_path = ''

        if controller_path[1][0] == '/':
            controller_file_path = controller_path[1][1:]

        # print(base_path)
        # print(controller_file_path)

        merged_path = base_path + controller_file_path

        print(f"after merging path: {merged_path}")
        if not os.path.exists(merged_path):
            return f"Controller file '{controller_file}' not found."

        with open(merged_path, 'r', encoding='utf-8') as file:
            content = file.read()
            pattern = rf"(?:const|let|var)\s+" + rf"{
                controller_name}\s*=\s*async\s*\([^)]*\)\s*=>\s*\{{(?:[^{{}}]|{{\s*(?:[^{{}}]|{{\s*(?:[^{{}}]|{{\s*[^{{}}]*\}})*\}})*\}})*\}}"

            match = re.search(pattern, content, re.DOTALL)

            return match.group(0) if match else f"Controller '{controller_name}' not found in '{controller_file}'."

    def _extract_route_info(self, content: str, controller_imports: Dict[str, str]) -> List[Dict[str, Any]]:
        routes = []
        for pattern in self.route_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            for method, endpoint, controller in matches:
                controller_code = ""
                if "(" in controller:
                    controller_code = controller.strip()
                elif controller in controller_imports:
                    controller_code = self._get_controller_code(
                        controller, controller_imports[controller])
                routes.append({
                    'method': method.lower(),
                    'endpoint': endpoint,
                    'controller_signature': controller,
                    'controller_code': controller_code,
                })

        return routes

    def _extract_middleware(self, content: str) -> List[str]:
        middleware = []
        for pattern in self.middleware_patterns.values():
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                middleware_content = match.group(1)
                if middleware_content:
                    middleware.append(middleware_content.strip())
        return middleware

    def _extract_request_data(self, handler: str) -> Dict[str, Any]:
        print(f"Extracting request data for the following handler:\n{handler}")
        schema = {}

        body_pattern = r'const\s*{\s*([^}]+)\s*}\s*=\s*req\.body'
        body_match = re.search(body_pattern, handler)

        if body_match:
            schema['body'] = [param.strip()
                              for param in body_match.group(1).split(',')]

        # Pattern to extract request params
        params_pattern = r'const\s*{\s*([^}]+)\s*}\s*=\s*req\.params'
        params_match = re.search(params_pattern, handler)
        if params_match:
            # Clean up and split the parameters
            schema['params'] = [param.strip()
                                for param in params_match.group(1).split(',')]

        print(f"Final schema: {schema}")

        return schema

    def _extract_response_data(self, handler: str) -> List[Dict[str, Any]]:

        response_pattern = r"""
            res
            (?:\.status\((\d+)\))?
            \.(?:json|send)
            \((
                \{[^;]*?\}
                |
                [^;]+
            )\)
        """

        responses = []
        matches = re.finditer(
            response_pattern, handler, re.VERBOSE | re.DOTALL)

        for match in matches:
            status_code = match.group(1) or '200'
            response_body = match.group(2).strip()

            # clean up the response body
            response_body = self._clean_response_body(response_body)

            responses.append({
                'status_code': status_code,
                'response_body': response_body
            })

        return responses

    def _clean_response_body(self, body: str) -> str:
        """cleans and formats the response body"""
        body = re.sub(r'\s+', ' ', body)
        return body.strip()

    def _process_file(self, file_path: Path) -> None:
        if file_path in self.processed_files or not file_path.suffix == '.js':
            return
        content = self._read_file_content(file_path)
        if not content:
            return

        controller_imports = self._extract_controller_imports(content)
        print(controller_imports)
        routes = self._extract_route_info(content, controller_imports)
        middleware = self._extract_middleware(content)

        for route in routes:
            handler = route['controller_code']
            request_data = self._extract_request_data(handler)
            response_data = self._extract_response_data(handler)
            auth_required = any(
                'auth' in mw.lower() or 'authenticate' in mw.lower() or 'jwt' in mw.lower()
                for mw in middleware
            )

            api_spec = APISpecification(
                endpoint=route['endpoint'],
                method=route['method'],
                controller_signature=route['controller_signature'],
                controller_code=route['controller_code'],
                request_data=request_data,
                expected_response=response_data,
                auth_required=auth_required,
                test_cases="",
                files=str(file_path),
                api_schema={},
                middleware=middleware
            )
            self.api_specifications.append(api_spec)

        self.processed_files.add(file_path)

    def _process_directory(self, dir_path: Path) -> None:
        try:
            for path in dir_path.iterdir():
                if path.is_file() and path.suffix == '.js':
                    self._process_file(path)
                elif path.is_dir() and not path.name.startswith('.'):
                    self._process_directory(path)
        except Exception as e:
            print(f"Error processing directory {dir_path}: {e}")

    def extract_apis(self) -> List[Dict[str, Any]]:

        if self.routes_path.is_dir():
            self._process_directory(self.routes_path)
        else:
            self._process_file(self.routes_path)
        return [api_spec.model_dump() for api_spec in self.api_specifications]
