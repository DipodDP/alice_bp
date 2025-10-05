# alisa_skill/helpers.py

def build_alice_response_payload(response_text: str, request_data: dict):
    """
    Constructs the response payload dictionary to be sent to Alice.
    """
    return {
        "response": {"text": response_text},
        "session": request_data["session"],
        "version": request_data["version"],
    }
