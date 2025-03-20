import pytest
import json
from phe import paillier
from src.app import app, public_key  # Import app and public_key from Flask app

# Define global public key for tests
TEST_PUBLIC_KEY_N = 3210131167491402381360855405768136524723131583063401686939536377248206612898093902281517087989350447973680309349844939869625646069464283107102315140957135030855566698657728970743088872406086683005602981278782061462055117278358014685112717964828813688516035554137921655736181767637289690401259456491103568200339004419723774721415806936330885537229629641534942073956043863651976921040523281337551635982725737466262891323780975172451930241745652810226072575597011991165681288123337624183920090048905922282510614733081584888927789152871527795813868130394440878786340663453158764179621633859940291709225244925576473129803649759479666630736435849023151048963155970604007302450251210062572989831233579665555916445017421998785129641602069991707623738433829244731105324853096864425578633661846748179236139451724598230259714841024752729202889975310593161557704676030992651855327522255343082019593345265429213697707608079783448122041581

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
    assert "public_key_n" in public_key_data, "public_key_data should contain public_key_n"
    assert isinstance(public_key_data["public_key_n"], int), "'public_key_n' should be an integer"
    assert public_key_data["public_key_n"] > 0, "'public_key_n' should be a positive integer"


# Test the /submit-geofence-result-ref API endpoint to ensure it processes and responds to encrypted geofence data correctly
def test_submit_geofence_result_ref_success(client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15

    encrypted_result = public_key.encrypt(test_value)  # Encrypt the test value using the public key from the Flask app
    ciphertext_value = encrypted_result.ciphertext()   # Get the encrypted ciphertext
    exponent = encrypted_result.exponent               # Get the exponent used for encryption
    public_key_n = public_key.n                        # Get the modulus 'n' from the public key

    # Prepare the payload with encrypted data
    data = {
            "encrypted_results": [
                {"ciphertext": ciphertext_value, "exponent": exponent},
                {"ciphertext": ciphertext_value, "exponent": exponent}
        ],
        "public_key_n": public_key_n
    }

    # Send POST request to the /submit-geofence-result-ref endpoint using the test client
    response = client.post(
        "/submit-geofence-result-ref",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 200                                           # Check if the response status code is OK
    response_json = response.get_json()                                          # Parse JSON from response
    assert response_json["status"] == "success"                                  # Confirm response status
    assert response_json["message"] == "Geofence result processed successfully"  # Confirm success message



# Test the /submit-geofence-result-ref API endpoint to ensure it responds to missing fields correctly
def test_submit_geofence_result_ref_missing_fields(client):
    # Test value to be encrypted and submitted
    public_key_n = public_key.n                        # Get the modulus 'n' from the public key

    # Prepare the payload with encrypted data
    data = {
        "public_key_n": public_key_n
    }

    # Send POST request to the /submit-geofence-result-ref endpoint using the test client
    response = client.post(
        "/submit-geofence-result-ref",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                                                          # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                         # Parse JSON from response
    assert response_json["status"] == "error"                                                                   # Confirm response status
    assert response_json["message"] == "Missing 'encrypted_results' or 'public_key_n' in request data"          # Confirm error message



# Test the /submit-geofence-result-ref API endpoint to ensure it processes and responds to public key mismatch correctly
def test_submit_geofence_result_ref_public_key_mismatch(client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15

    encrypted_result = public_key.encrypt(test_value)  # Encrypt the test value using the public key from the Flask app
    ciphertext_value = encrypted_result.ciphertext()   # Get the encrypted ciphertext
    exponent = encrypted_result.exponent               # Get the exponent used for encryption
    public_key_n = 1234                                # Public key changed

    # Prepare the payload with encrypted data
    data = {
            "encrypted_results": [
                {"ciphertext": ciphertext_value, "exponent": exponent},
                {"ciphertext": ciphertext_value, "exponent": exponent}
        ],
        "public_key_n": public_key_n
    }

    # Send POST request to the /submit-geofence-result-ref endpoint using the test client
    response = client.post(
        "/submit-geofence-result-ref",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                                                              # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                             # Parse JSON from response
    assert response_json["status"] == "error"                                                                       # Confirm response status
    assert response_json["message"] == "Public key mismatch. Encryption was not done with the correct public key."  # Confirm error message



# Test the /submit-geofence-result-ref API endpoint to ensure it handles decryption failures correctly
def test_submit_geofence_result_ref_decryption_failure(client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15
    wrong_public_key = paillier.PaillierPublicKey(TEST_PUBLIC_KEY_N)  # Create public key for encryption
    encrypted_result = wrong_public_key.encrypt(test_value)  # Encrypt the test value using the public key from the Flask app
    ciphertext_value = encrypted_result.ciphertext()   # Get the encrypted ciphertext
    exponent = encrypted_result.exponent               # Get the exponent used for encryption
    public_key_n = public_key.n                        # Get the modulus 'n' from the public key

    # Prepare the payload with encrypted data
    data = {
            "encrypted_results": [
                {"ciphertext": ciphertext_value, "exponent": exponent},
                {"ciphertext": ciphertext_value, "exponent": exponent}
        ],
        "public_key_n": public_key_n
    }

    # Send POST request to the /submit-geofence-result-ref endpoint using the test client
    response = client.post(
        "/submit-geofence-result-ref",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 500                                                                              # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                             # Parse JSON from response
    assert response_json["status"] == "error"                                                                       # Confirm response status
    assert response_json["message"] == "Couldn't decrypt encrypted results"                                          # Confirm error message



# Test the /submit-geofence-result-prop API endpoint to ensure it processes and responds to encrypted geofence data correctly
def test_submit_geofence_result_prop_success(client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15

    encrypted_result = public_key.encrypt(test_value)  # Encrypt the test value using the public key from the Flask app
    ciphertext_value = encrypted_result.ciphertext()   # Get the encrypted ciphertext
    exponent = encrypted_result.exponent               # Get the exponent used for encryption
    public_key_n = public_key.n                        # Get the modulus 'n' from the public key

    # Prepare the payload with encrypted data
    data = {
            "encrypted_results": [
                {"ciphertext": ciphertext_value, "exponent": exponent},
                {"ciphertext": ciphertext_value, "exponent": exponent}
        ],
        "public_key_n": public_key_n
    }

    # Send POST request to the /submit-geofence-result-prop endpoint using the test client
    response = client.post(
        "/submit-geofence-result-prop",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 200                                           # Check if the response status code is OK
    response_json = response.get_json()                                          # Parse JSON from response
    assert response_json["status"] == "success"                                  # Confirm response status
    assert response_json["message"] == "Geofence result processed successfully"  # Confirm success message



# Test the /submit-geofence-result-prop API endpoint to ensure it responds to missing fields correctly
def test_submit_geofence_result_prop_missing_fields(client):
    # Test value to be encrypted and submitted
    public_key_n = public_key.n                        # Get the modulus 'n' from the public key

    # Prepare the payload with encrypted data
    data = {
        "public_key_n": public_key_n
    }

    # Send POST request to the /submit-geofence-result-prop endpoint using the test client
    response = client.post(
        "/submit-geofence-result-prop",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                                                          # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                         # Parse JSON from response
    assert response_json["status"] == "error"                                                                   # Confirm response status
    assert response_json["message"] == "Missing 'encrypted_results' or 'public_key_n' in request data"          # Confirm error message



# Test the /submit-geofence-result-prop API endpoint to ensure it processes and responds to public key mismatch correctly
def test_submit_geofence_result_prop_public_key_mismatch(client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15

    encrypted_result = public_key.encrypt(test_value)  # Encrypt the test value using the public key from the Flask app
    ciphertext_value = encrypted_result.ciphertext()   # Get the encrypted ciphertext
    exponent = encrypted_result.exponent               # Get the exponent used for encryption
    public_key_n = 1234                                # Public key changed

    # Prepare the payload with encrypted data
    data = {
            "encrypted_results": [
                {"ciphertext": ciphertext_value, "exponent": exponent},
                {"ciphertext": ciphertext_value, "exponent": exponent}
        ],
        "public_key_n": public_key_n
    }

    # Send POST request to the /submit-geofence-result-prop endpoint using the test client
    response = client.post(
        "/submit-geofence-result-prop",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                                                              # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                             # Parse JSON from response
    assert response_json["status"] == "error"                                                                       # Confirm response status
    assert response_json["message"] == "Public key mismatch. Encryption was not done with the correct public key."  # Confirm error message



# Test the /submit-geofence-result-prop API endpoint to ensure it handles decryption failures correctly
def test_submit_geofence_result_prop_decryption_failure(client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15
    wrong_public_key = paillier.PaillierPublicKey(TEST_PUBLIC_KEY_N)  # Create public key for encryption
    encrypted_result = wrong_public_key.encrypt(test_value)  # Encrypt the test value using the public key from the Flask app
    ciphertext_value = encrypted_result.ciphertext()   # Get the encrypted ciphertext
    exponent = encrypted_result.exponent               # Get the exponent used for encryption
    public_key_n = public_key.n                        # Get the modulus 'n' from the public key

    # Prepare the payload with encrypted data
    data = {
            "encrypted_results": [
                {"ciphertext": ciphertext_value, "exponent": exponent},
                {"ciphertext": ciphertext_value, "exponent": exponent}
        ],
        "public_key_n": public_key_n
    }

    # Send POST request to the /submit-geofence-result-prop endpoint using the test client
    response = client.post(
        "/submit-geofence-result-prop",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 500                                                                              # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                             # Parse JSON from response
    assert response_json["status"] == "error"                                                                       # Confirm response status
    assert response_json["message"] == "Couldn't decrypt encrypted results"                                          # Confirm error message