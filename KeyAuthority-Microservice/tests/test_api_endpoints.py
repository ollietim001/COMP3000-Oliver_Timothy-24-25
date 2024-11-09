import pytest
import json
from src.app import app, public_key  # Import app and public_key from Flask app


# Pytest fixture to set up the test client for Flask app
@pytest.fixture
def client():
    # Create a test client instance and yield it for use in tests
    with app.test_client() as client:
        yield client

# Test the /get-public-key API endpoint to ensure it returns a valid public key
def test_get_public_key(client):
    # Send a GET request to retrieve the public key
    response = client.get("/get-public-key")

    # Check if the response status code is OK
    assert response.status_code == 200
    
    # Parse the JSON response and verify the structure
    public_key_data = response.get_json()
    assert "n" in public_key_data, "public_key_data should contain n"
    assert isinstance(public_key_data["n"], int), "'n' should be an integer"
    assert public_key_data["n"] > 0, "'n' should be a positive integer"

# Test the /submit-geofence-result API endpoint to ensure it processes and responds to encrypted geofence data correctly
def test_submit_geofence_result(client):
    # Test value to be encrypted and submitted
    test_value = 100

    encrypted_result = public_key.encrypt(test_value)  # Encrypt the test value using the public key from the Flask app
    ciphertext_value = encrypted_result.ciphertext()   # Get the encrypted ciphertext
    exponent = encrypted_result.exponent               # Get the exponent used for encryption
    public_key_n = public_key.n                        # Get the modulus 'n' from the public key

    # Prepare the payload with encrypted data
    data = {
        "encrypted_result": [ciphertext_value, exponent],
        "public_key_n": public_key_n
    }

    # Send POST request to the /submit-geofence-result endpoint using the test client
    response = client.post(
        "/submit-geofence-result",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 200                                           # Check if the response status code is OK
    response_json = response.get_json()                                          # Parse JSON from response
    assert response_json["status"] == "success"                                  # Confirm response status
    assert response_json["message"] == "Geofence result processed successfully"  # Confirm success message
