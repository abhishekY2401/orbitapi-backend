

import re
import os
from app.schema.api_schema import ApiSpecsResponseModel


def extract_api_from_nodejs(project_path: str) -> ApiSpecsResponseModel:
    api_specs = []
    routes_dir = os.path.join(project_path, 'routes')
    print("inside extraction api...")

    # Iterate through all the route files
    for filename in os.listdir(routes_dir):
        print("nodejs dir filename: ", filename)
        if filename.endswith(".js"):
            route_file_path = os.path.join(routes_dir, filename)
            with open(route_file_path, 'r') as file:
                content = file.read()

                # Step 1: Extract all imported controllers from the top of the file
                controller_imports = extract_controller_imports(content)
                print(f"imports: {controller_imports}")

                # Step 2: Identify all route definitions (endpoints, methods, controllers)
                routes = re.findall(
                    r"router\.(get|post|put|patch|delete)\(['\"](.+?)['\"],\s*(\w+|\(.*?\)\s*=>\s*\{.*?\})", content, re.DOTALL)
                print(f"routes: {routes}")
                for method, endpoint, controller in routes:

                    api_spec = {
                        'endpoint': endpoint,
                        'method': method,
                        'controller_signature': controller,
                        'controller_code': '',
                        'request_data': {
                            'body': {},
                            'params': {},
                            'headers': {},
                            'query': {}
                        },
                        'expected_response': {
                            'status_code': 200,
                            'body': {}
                        },
                        'auth_required': False,
                        'db_state': ''
                    }

                    if "(" in controller:
                        api_spec['controller_code'] = controller.strip()
                    else:
                        controller_file = controller_imports.get(controller)
                        if controller_file:
                            api_spec['controller_code'] = get_controller_code(
                                controller, controller_file, project_path)
                        else:
                            api_spec['controller_code'] = f"Controller '{
                                controller}' not found."

                    # Extract details from the controller code
                    extract_request_data(api_spec)
                    extract_response_info(api_spec)

                    api_specs.append(api_spec)

    return api_specs


def extract_controller_imports(content):
    # Extract import or require statements at the top of the file
    controller_imports = {}

    # Match both `require()` and destructured ES6 `import` syntax
    require_matches = re.findall(
        r"(?:const|let|var)\s*{?\s*([\w\s,]+)\s*}?\s*=\s*require\(['\"](.+?)['\"]\);", content)
    for controllers, file_path in require_matches:
        controller_names = [name.strip() for name in controllers.split(",")]
        for controller_name in controller_names:
            # Normalize the path to ensure it's relative to project_path
            relative_path = file_path.strip(".")
            relative_path = relative_path.split("/")
            relative_path = "\\".join(relative_path)
            print(relative_path)
            # Store the relative path as a key in imports dictionary
            controller_imports[controller_name] = relative_path

    return controller_imports


def get_controller_code(controller_name, relative_controller_file, project_path):
    # Construct the full path to the controller file
    controller_file_path = project_path + relative_controller_file
    print(controller_file_path)

    # If file doesn't exist, try adding .js extension
    if not controller_file_path.endswith(".js"):
        controller_file_path += ".js"

    # Check if the file exists now
    if not os.path.exists(controller_file_path):
        return f"Controller file '{controller_file_path}' not found."

    # Read the controller file content
    with open(controller_file_path, 'r') as file:
        content = file.read()

        # Search for the controller function in the content
        pattern = rf"(?:const|let|var)\s+" + \
            rf"{controller_name}\s*=\s*async\s*\([^)]*\)\s*=>\s*\{{(?:[^{{}}]|{{\s*(?:[^{{}}]|{{\s*(?:[^{{}}]|{{\s*[^{{}}]*\}})*\}})*\}})*\}}"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            # Extract the controller function code block
            return match.group(0)
        else:
            return f"Controller '{controller_name}' not found in '{controller_file_path}'."


def extract_request_data(api_spec):
    """
        Extract request data from controller code
    """

    controller_code = api_spec['controller_code']

    # patterns for extraction of body, params, headers and queries
    param_pattern = r"req\.params\.(\w+)"
    query_pattern = r"req\.query\.(\w+)"
    header_pattern = r"req\.headers\.(\w+)"
    body_pattern = r"req\.body\.(\w+)"

    # extract request parameters
    params = re.findall(param_pattern, controller_code, re.DOTALL)
    queries = re.findall(query_pattern, controller_code, re.DOTALL)
    headers = re.findall(header_pattern, controller_code, re.DOTALL)
    body = re.findall(body_pattern, controller_code, re.DOTALL)

    if body:
        api_spec['request_data']['body'] = list(set(body))
    if params:
        api_spec['request_data']['params'] = list(set(params))
    if headers:
        api_spec['request_data']['headers'] = list(set(headers))
    if queries:
        api_spec['request_data']['query'] = list(set(queries))


def extract_response_info(api_spec):
    """
        Extract response structure and status codes
    """
    controller_code = api_spec['controller_code']

    # Search for return statements to find response body and status code
    status_pattern = r"res\.status\((\d+)\)\.json\((.*?)\)"

    response_info = {
        'success_responses': {},  # Will store 2xx responses
        'error_responses': {},    # Will store 4xx and 5xx responses
    }

    # helper function to analyze response structure
    def analyze_structure(response):

        response = re.sub(r'//.*?\n|/\*.*?\*/', '', response, flags=re.DOTALL)
        response = response.strip()

        # extract if it's a direct string/ number / boolean
        if response.startswith('"') or response.startswith("'"):
            return {'type': 'string', 'example': response.strip('"\'')}
        elif response.isnumeric():
            return {'type': 'number', 'example': float(response)}
        elif response in ['true', 'false']:
            return {'type': 'boolean', 'example': response == 'true'}

        # If it's an object destructuring
        if response.startswith('{') and '}' in response:

            properties = {}

            # Extract properties from destructuring
            destructure_pattern = r'{([^}]+)}'
            match = re.search(destructure_pattern, response)
            if match:
                props = match.group(1).split(',')
                for prop in props:
                    prop = prop.strip()
                    if ':' in prop:
                        key, value = prop.split(':')
                        properties[key.strip()] = 'unknown'
                    else:
                        properties[prop] = 'unknown'
                return {'type': 'object', 'properties': properties}

        # If it's a variable
        if re.match(r'^[a-zA-Z_]\w*$', response):
            # Try to find variable definition/usage in code
            var_pattern = rf'{response}\s*=\s*(.+?)(?=;|$)'
            var_match = re.search(var_pattern, controller_code, re.DOTALL)
            if var_match:
                return analyze_structure(var_match.group(1))
            return {'type': 'unknown', 'variable': response}

        # If it's an error object
        if 'err' in response:
            return {
                'type': 'error',
                'properties': {
                    'message': 'string',
                    'stack': 'string'
                }
            }

        return {'type': 'unknown', 'raw': response}

    # Process responses with status codes
    status_matches = re.finditer(status_pattern, controller_code, re.DOTALL)
    found_success = False

    for match in status_matches:
        status_code = match.group(1)
        response_body = match.group(2)

        structure = analyze_structure(response_body)

        # Categorize based on status code
        if status_code.startswith('2'):
            response_info['success_responses'][status_code] = structure
            # Update the api_spec with the first success response found
            if not found_success:
                api_spec['expected_response']['status_code'] = int(status_code)
                api_spec['expected_response']['body'] = structure
                found_success = True
        else:
            response_info['error_responses'][status_code] = structure

    # If no success responses were found, use the first error response
    if not found_success and response_info['error_responses']:
        first_error = next(iter(response_info['error_responses'].items()))
        api_spec['expected_response']['status_code'] = int(first_error[0])
        api_spec['expected_response']['body'] = first_error[1]

    # Store all responses in api_spec for reference
    api_spec['all_responses'] = response_info


def extract_urlpatterns(file_path):
    urlpatterns = []
    with open(file_path, 'r') as file:
        content = file.read()
        pattern = r"path\('([^']+)'\s*,\s*([\w_]+)\s*,\s*name='([\w_]+)'\)"
        matches = re.findall(pattern, content)
        for url, view, name in matches:
            urlpatterns.append({
                'url_pattern': url,
                'view': view,
                'name': name
            })
    return urlpatterns

# Helper to extract fields from serializers using regex


def extract_serializer_fields(file_path, serializer_name):
    fields = {}
    with open(file_path, 'r') as file:
        content = file.read()
        class_pattern = rf"class {serializer_name}\(.*\):"
        if re.search(class_pattern, content):
            field_pattern = r'(\w+)\s*=\s*serializers\.\w+\('
            fields = {match: "sample_value" for match in re.findall(
                field_pattern, content)}
    return fields

# Extract HTTP methods, controller signature, request data, and expected responses in views.py using regex


def extract_view_methods_and_patterns(file_path, project_root):
    view_methods = {}
    with open(file_path, 'r') as file:
        content = file.read()

        # Updated pattern to capture views with either @api_view, @permission_classes, or no decorators
        function_pattern = r"(?:(@api_view\(\[(['\w, ]+)\]\))\n)?(?:(@permission_classes\(.+\)\n)?)def (\w+)\(request.?\):\n([\s\S]?)(?=^@|^def|\Z)"

        matches = re.findall(function_pattern, content, re.MULTILINE)

        for api_view_decorator, methods, permission_classes, view_name, body in matches:
            # If @api_view is present, parse HTTP methods
            if api_view_decorator:
                methods = [m.strip().replace("'", "")
                           for m in methods.split(",")]
            else:
                # Default to "GET" if @api_view is not specified
                methods = ["GET"]

            # Controller Signature (view function name)
            controller_signature = f"{
                view_name} (HTTP Methods: {', '.join(methods)})"

            # Full controller code including any decorators
            controller_code = (api_view_decorator + "\n" if api_view_decorator else "") + \
                              (permission_classes if permission_classes else "") + \
                "def " + view_name + "(request):\n" + body

            request_data = {"body": {}, "params": {},
                            "headers": {}, "query": {}}
            expected_response = {"status_code": 200, "body": {}}

            # Detect serializer and extract fields
            serializer_match = re.search(r'(\w+Serializer)\(', body)
            if serializer_match:
                serializer_name = serializer_match.group(1)
                for root, _, files in os.walk(project_root):
                    for file in files:
                        if file.endswith('.py') and serializer_name in open(os.path.join(root, file)).read():
                            fields = extract_serializer_fields(
                                os.path.join(root, file), serializer_name)
                            request_data["body"] = fields
                            expected_response["body"] = fields

            # Extract request data fields
            data_fields = re.findall(r"request\.data\.get\('(\w+)'\)", body)
            if data_fields:
                request_data["body"].update(
                    {field: "sample_value" for field in data_fields})

            # Detect request patterns
            if "request.POST" in body:
                request_data["body"] = request_data["body"] or {
                    "example_field": "sample_value"}
            if "request.GET" in body:
                request_data["query"] = {"query_param": "sample_value"}
            if "request.headers" in body:
                request_data["headers"] = {"Authorization": "Bearer token"}

            # Extract multiple response paths by finding all Response or JsonResponse patterns
            response_matches = re.findall(
                r'(JsonResponse|Response)\((.*?)\)', body)
            responses = []
            for response_type, response_content in response_matches:
                response_info = {"status_code": 200, "body": {}}
                if response_type == "JsonResponse":
                    response_info["body"] = expected_response["body"] or {
                        "key": "value"}
                elif response_type == "Response":
                    response_info["body"] = "Sample response content"
                status_code_match = re.search(
                    r'status=(\d+)', response_content)
                if status_code_match:
                    response_info["status_code"] = int(
                        status_code_match.group(1))
                responses.append(response_info)

            view_methods[view_name] = {
                "methods": methods,
                "controller_signature": controller_signature,
                "controller_code": controller_code,  # Full function code
                "request_data": request_data,
                "expected_response": responses if responses else [expected_response]
            }

    return view_methods

# Main extraction function for API specs


def generate_api_specs_for_django(project_root: str) -> ApiSpecsResponseModel:
    api_specs = []
    urls_files = []
    views_files = []
    models_files = []

    for root, _, files in os.walk(project_root):
        for file in files:
            if file == 'urls.py':
                urls_files.append(os.path.join(root, file))
            elif file == 'views.py':
                views_files.append(os.path.join(root, file))
            elif file == 'models.py':
                models_files.append(os.path.join(root, file))

    for urls_file in urls_files:
        urlpatterns = extract_urlpatterns(urls_file)

        all_view_methods = {}
        for views_file in views_files:
            view_methods = extract_view_methods_and_patterns(
                views_file, project_root)
            all_view_methods.update(view_methods)

        for pattern in urlpatterns:
            endpoint = pattern['url_pattern']
            view = pattern['view']
            methods_data = all_view_methods.get(view, {
                "methods": ["GET"],
                "controller_signature": view,
                "request_data": {},
                "expected_response": {}
            })

            for method in methods_data["methods"]:
                api_spec = {
                    'endpoint': endpoint,
                    'method': method,
                    'controller_signature': methods_data["controller_signature"],
                    'controller_code': methods_data["controller_code"],
                    'request_data': methods_data["request_data"],
                    'expected_response': methods_data["expected_response"],
                    'auth_required': False,
                }
                api_specs.append(api_spec)

    return api_specs
