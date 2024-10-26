import json
import google.generativeai as genai

# Initialize the Generative Model
model = genai.GenerativeModel('gemini-1.5-flash')
# Replace with your actual API key
genai.configure(api_key="AIzaSyAtBJJ4f7l4mz0npo6sIHizxYMgfgiRMPI")

# Generate test cases for each endpoint using the Generative Model


def generate_test_cases_for_endpoint(endpoint_data):
    print("inside test case generation..")
    prompt = (
        f"Generate test cases for an API endpoint with the following details:\n"
        f"Endpoint: {endpoint_data['endpoint']}\n"
        f"Method: {endpoint_data['method']}\n"
        f"Request Body: {endpoint_data['request_data']}\n"
        f"Expected response: {endpoint_data['expected_response']}\n"
        f"Authorization required: {
            endpoint_data['auth_required']}\n\n"
        f"Please provide sample test cases in JSON format."
    )

    # Send the prompt to the model and get the response
    response = model.generate_content([prompt])
    print("test case generation in process..")

    try:
        response = model.generate_content([prompt])
        test_cases = response.text if response else "No response generated."
        return test_cases
    except Exception as genai_error:
        print("Error in test case generation:", genai_error)
        return "Failed to generate test cases due to generation error"
