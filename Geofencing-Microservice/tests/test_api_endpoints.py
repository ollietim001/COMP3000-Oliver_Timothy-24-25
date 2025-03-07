import pytest
import json
from phe import paillier
from unittest.mock import patch
from src.app import app

###### NOTE: if tests fail it can be due to the overpass query timing out ########

# Define global public key for tests
TEST_PUBLIC_KEY_N = 3210131167491402381360855405768136524723131583063401686939536377248206612898093902281517087989350447973680309349844939869625646069464283107102315140957135030855566698657728970743088872406086683005602981278782061462055117278358014685112717964828813688516035554137921655736181767637289690401259456491103568200339004419723774721415806936330885537229629641534942073956043863651976921040523281337551635982725737466262891323780975172451930241745652810226072575597011991165681288123337624183920090048905922282510614733081584888927789152871527795813868130394440878786340663453158764179621633859940291709225244925576473129803649759479666630736435849023151048963155970604007302450251210062572989831233579665555916445017421998785129641602069991707623738433829244731105324853096864425578633661846748179236139451724598230259714841024752729202889975310593161557704676030992651855327522255343082019593345265429213697707608079783448122041581

# Pytest fixture to set up the test client for Flask app
@pytest.fixture
def client():
    # Create a test client instance and yield it for use in tests
    with app.test_client() as client:
        yield client

# Test the /submit-mobile-node-location-ref API endpoint to ensure it processes and responds to encrypted user data correctly
# Mock public key function and geofence fetch function
@patch("src.app.get_key_authority_public_key", return_value=TEST_PUBLIC_KEY_N)
@patch("src.app.get_geofence_coordinates")
def test_submit_mobile_node_location_ref_success(mock_geo, mock_key, client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15
    public_key = paillier.PaillierPublicKey(TEST_PUBLIC_KEY_N)  # Create public key for encryption
    encrypted_result = public_key.encrypt(test_value)           # Encrypt the test value using the public key
    ciphertext_value = encrypted_result.ciphertext()            # Get the encrypted ciphertext
    exponent = encrypted_result.exponent                        # Get the exponent used for encryption


    # Prepare the payload with encrypted data
    data = {
            "user_encrypted_location": {
                "alpha_sq_ct": ciphertext_value, "alpha_sq_exp": exponent, 
                "gamma_sq_ct": ciphertext_value, "gamma_sq_exp": exponent,
                "alpha_gamma_product_A_ct": ciphertext_value, "alpha_gamma_product_A_exp": exponent,
                "zeta_theta_sq_product_A_ct": ciphertext_value, "zeta_theta_sq_product_A_exp": exponent,
                "zeta_theta_mu_product_A_ct": ciphertext_value, "zeta_theta_mu_product_A_exp": exponent,
                "zeta_mu_sq_product_A_ct": ciphertext_value, "zeta_mu_sq_product_A_exp": exponent
            },
            "public_key_n": TEST_PUBLIC_KEY_N,
    }

    # Send POST request to the /submit-mobile-node-location-ref endpoint using the test client
    response = client.post(
        "/submit-mobile-node-location-ref",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 200                                           # Check if the response status code is OK
    response_json = response.get_json()                                          # Parse JSON from response
    assert response_json["status"] == "success"                                  # Confirm response status
    assert response_json["message"] == "Location data recieved"                  # Confirm success message



# Test the /submit-mobile-node-location-ref API endpoint to ensure it responds to missing data correctly
# Mock public key function and geofence fetch function
@patch("src.app.get_key_authority_public_key", return_value=TEST_PUBLIC_KEY_N)
@patch("src.app.get_geofence_coordinates")
def test_submit_mobile_node_location_ref_missing_data(mock_geo, mock_key, client):
    # Send POST request to the /submit-mobile-node-location-ref endpoint using the test client
    response = client.post(
        "/submit-mobile-node-location-ref",
        data=json.dumps({}),           # Send no data
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                           # Check if the response status code is a Bad Request
    response_json = response.get_json()                                          # Parse JSON from response
    assert response_json["status"] == "error"                                    # Confirm response status
    assert response_json["message"] == "Request data is missing"                 # Confirm error message



# Test the /submit-mobile-node-location-ref API endpoint to ensure it responds to missing fields correctly
# Mock public key function and geofence fetch function
@patch("src.app.get_key_authority_public_key", return_value=TEST_PUBLIC_KEY_N)
@patch("src.app.get_geofence_coordinates")
def test_submit_mobile_node_location_ref_missing_fields(mock_geo, mock_key, client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15
    public_key = paillier.PaillierPublicKey(TEST_PUBLIC_KEY_N)  # Create public key for encryption
    encrypted_result = public_key.encrypt(test_value)           # Encrypt the test value using the public key


    # Prepare the payload with encrypted data
    data = {"public_key_n": TEST_PUBLIC_KEY_N,}

    # Send POST request to the /submit-mobile-node-location-ref endpoint using the test client
    response = client.post(
        "/submit-mobile-node-location-ref",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                                                          # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                         # Parse JSON from response
    assert response_json["status"] == "error"                                                                   # Confirm response status
    assert response_json["message"] == "Missing 'user_encrypted_location' or 'public_key_n' in request data"    # Confirm error message



# Test the /submit-mobile-node-location-ref API endpoint to ensure it responds to public key mismatch correctly
# Mock public key function and geofence fetch function
@patch("src.app.get_key_authority_public_key", return_value=TEST_PUBLIC_KEY_N)
@patch("src.app.get_geofence_coordinates")
def test_submit_mobile_node_location_ref_public_key_mismatch(mock_geo, mock_key, client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15
    public_key = paillier.PaillierPublicKey(TEST_PUBLIC_KEY_N)  # Create public key for encryption
    encrypted_result = public_key.encrypt(test_value)           # Encrypt the test value using the public key
    ciphertext_value = encrypted_result.ciphertext()            # Get the encrypted ciphertext
    exponent = encrypted_result.exponent                        # Get the exponent used for encryption


    # Prepare the payload with encrypted data
    data = {
            "user_encrypted_location": {
                "alpha_sq_ct": ciphertext_value, "alpha_sq_exp": exponent, 
                "gamma_sq_ct": ciphertext_value, "gamma_sq_exp": exponent,
                "alpha_gamma_product_A_ct": ciphertext_value, "alpha_gamma_product_A_exp": exponent,
                "zeta_theta_sq_product_A_ct": ciphertext_value, "zeta_theta_sq_product_A_exp": exponent,
                "zeta_theta_mu_product_A_ct": ciphertext_value, "zeta_theta_mu_product_A_exp": exponent,
                "zeta_mu_sq_product_A_ct": ciphertext_value, "zeta_mu_sq_product_A_exp": exponent
            },
            "public_key_n": 123, # Different public key
    }

    # Send POST request to the /submit-mobile-node-location-ref endpoint using the test client
    response = client.post(
        "/submit-mobile-node-location-ref",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                                                                # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                               # Parse JSON from response
    assert response_json["status"] == "error"                                                                         # Confirm response status
    assert response_json["message"] == "Public key mismatch. Encryption was not done with the correct public key."    # Confirm error message



# Test the /submit-mobile-node-location-ref API endpoint to ensure it responds to missing keys correctly
# Mock public key function and geofence fetch function
@patch("src.app.get_key_authority_public_key", return_value=TEST_PUBLIC_KEY_N)
@patch("src.app.get_geofence_coordinates")
def test_submit_mobile_node_location_ref_missing_keys(mock_geo, mock_key, client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15
    public_key = paillier.PaillierPublicKey(TEST_PUBLIC_KEY_N)  # Create public key for encryption
    encrypted_result = public_key.encrypt(test_value)           # Encrypt the test value using the public key
    ciphertext_value = encrypted_result.ciphertext()            # Get the encrypted ciphertext
    exponent = encrypted_result.exponent                        # Get the exponent used for encryption


    # Prepare the payload with encrypted data
    data = {
            "user_encrypted_location": {
                "alpha_sq_ct": ciphertext_value,
                "gamma_sq_ct": ciphertext_value, "gamma_sq_exp": exponent,
                "alpha_gamma_product_A_ct": ciphertext_value, "alpha_gamma_product_A_exp": exponent,
                "zeta_theta_sq_product_A_ct": ciphertext_value, "zeta_theta_sq_product_A_exp": exponent,
                "zeta_theta_mu_product_A_ct": ciphertext_value, "zeta_theta_mu_product_A_exp": exponent,
                "zeta_mu_sq_product_A_ct": ciphertext_value, "zeta_mu_sq_product_A_exp": exponent
            },
            "public_key_n": TEST_PUBLIC_KEY_N,
    }

    # Send POST request to the /submit-mobile-node-location-ref endpoint using the test client
    response = client.post(
        "/submit-mobile-node-location-ref",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                                                      # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                     # Parse JSON from response
    assert response_json["status"] == "error"                                                               # Confirm response status
    assert response_json["message"] == "Missing required keys in 'user_encrypted_location': alpha_sq_exp"   # Confirm error message



# Test the /submit-mobile-node-location-prop API endpoint to ensure it processes and responds to encrypted user data correctly
# Mock public key function and geofence fetch function
@patch("src.app.get_key_authority_public_key", return_value=TEST_PUBLIC_KEY_N)
@patch("src.app.get_geofence_coordinates")
def test_submit_mobile_node_location_prop_succcess(mock_geo, mock_key, client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15
    public_key = paillier.PaillierPublicKey(TEST_PUBLIC_KEY_N)  # Create public key for encryption
    encrypted_result = public_key.encrypt(test_value)           # Encrypt the test value using the public key
    ciphertext_value = encrypted_result.ciphertext()            # Get the encrypted ciphertext
    exponent = encrypted_result.exponent                        # Get the exponent used for encryption


    # Prepare the payload with encrypted data
    data = {
            "user_encrypted_location": {
                "c1_ct": ciphertext_value, "c1_exp": exponent, 
                "c2_ct": ciphertext_value, "c2_exp": exponent,
                "c3_ct": ciphertext_value, "c3_exp": exponent
            },
            "public_key_n": TEST_PUBLIC_KEY_N,
    }

    # Send POST request to the /submit-mobile-node-location-prop endpoint using the test client
    response = client.post(
        "/submit-mobile-node-location-prop",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 200                                           # Check if the response status code is OK
    response_json = response.get_json()                                          # Parse JSON from response
    assert response_json["status"] == "success"                                  # Confirm response status
    assert response_json["message"] == "Location data recieved"                  # Confirm success message



# Test the /submit-mobile-node-location-prop API endpoint to ensure it responds to missing data correctly
# Mock public key function and geofence fetch function
@patch("src.app.get_key_authority_public_key", return_value=TEST_PUBLIC_KEY_N)
@patch("src.app.get_geofence_coordinates")
def test_submit_mobile_node_location_prop_missing_data(mock_geo, mock_key, client):
    # Send POST request to the /submit-mobile-node-location-prop endpoint using the test client
    response = client.post(
        "/submit-mobile-node-location-prop",
        data=json.dumps({}),           # Send no data
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                           # Check if the response status code is a Bad Request
    response_json = response.get_json()                                          # Parse JSON from response
    assert response_json["status"] == "error"                                    # Confirm response status
    assert response_json["message"] == "Request data is missing"                 # Confirm error message



# Test the /submit-mobile-node-location-prop API endpoint to ensure it responds to missing fields correctly
# Mock public key function and geofence fetch function
@patch("src.app.get_key_authority_public_key", return_value=TEST_PUBLIC_KEY_N)
@patch("src.app.get_geofence_coordinates")
def test_submit_mobile_node_location_prop_missing_fields(mock_geo, mock_key, client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15
    public_key = paillier.PaillierPublicKey(TEST_PUBLIC_KEY_N)  # Create public key for encryption
    encrypted_result = public_key.encrypt(test_value)           # Encrypt the test value using the public key


    # Prepare the payload with encrypted data
    data = {"public_key_n": TEST_PUBLIC_KEY_N,}

    # Send POST request to the /submit-mobile-node-location-prop endpoint using the test client
    response = client.post(
        "/submit-mobile-node-location-prop",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                                                          # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                         # Parse JSON from response
    assert response_json["status"] == "error"                                                                   # Confirm response status
    assert response_json["message"] == "Missing 'user_encrypted_location' or 'public_key_n' in request data"    # Confirm error message



# Test the /submit-mobile-node-location-prop API endpoint to ensure it responds to public key mismatch correctly
# Mock public key function and geofence fetch function
@patch("src.app.get_key_authority_public_key", return_value=TEST_PUBLIC_KEY_N)
@patch("src.app.get_geofence_coordinates")
def test_submit_mobile_node_location_prop_public_key_mismatch(mock_geo, mock_key, client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15
    public_key = paillier.PaillierPublicKey(TEST_PUBLIC_KEY_N)  # Create public key for encryption
    encrypted_result = public_key.encrypt(test_value)           # Encrypt the test value using the public key
    ciphertext_value = encrypted_result.ciphertext()            # Get the encrypted ciphertext
    exponent = encrypted_result.exponent                        # Get the exponent used for encryption


    # Prepare the payload with encrypted data
    data = {
            "user_encrypted_location": {
                "c1_ct": ciphertext_value, "c1_exp": exponent, 
                "c2_ct": ciphertext_value, "c2_exp": exponent,
                "c3_ct": ciphertext_value, "c3_exp": exponent
            },
            "public_key_n": 123, # Different public key
    }

    # Send POST request to the /submit-mobile-node-location-prop endpoint using the test client
    response = client.post(
        "/submit-mobile-node-location-prop",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                                                                # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                               # Parse JSON from response
    assert response_json["status"] == "error"                                                                         # Confirm response status
    assert response_json["message"] == "Public key mismatch. Encryption was not done with the correct public key."    # Confirm error message



# Test the /submit-mobile-node-location-prop API endpoint to ensure it responds to missing keys correctly
# Mock public key function and geofence fetch function
@patch("src.app.get_key_authority_public_key", return_value=TEST_PUBLIC_KEY_N)
@patch("src.app.get_geofence_coordinates")
def test_submit_mobile_node_location_prop_missing_keys(mock_geo, mock_key, client):
    # Test value to be encrypted and submitted
    test_value = 1.1672744938776433e-15
    public_key = paillier.PaillierPublicKey(TEST_PUBLIC_KEY_N)  # Create public key for encryption
    encrypted_result = public_key.encrypt(test_value)           # Encrypt the test value using the public key
    ciphertext_value = encrypted_result.ciphertext()            # Get the encrypted ciphertext
    exponent = encrypted_result.exponent                        # Get the exponent used for encryption


    # Prepare the payload with encrypted data
    data = {
            "user_encrypted_location": {
                "c1_ct": ciphertext_value,
                "c2_ct": ciphertext_value, "c2_exp": exponent,
                "c3_ct": ciphertext_value, "c3_exp": exponent
            },
            "public_key_n": TEST_PUBLIC_KEY_N,
    }

    # Send POST request to the /submit-mobile-node-location-prop endpoint using the test client
    response = client.post(
        "/submit-mobile-node-location-prop",
        data=json.dumps(data),
        content_type="application/json"
    )

    # Verify the response status code and content
    assert response.status_code == 400                                                                      # Check if the response status code is a Bad Request
    response_json = response.get_json()                                                                     # Parse JSON from response
    assert response_json["status"] == "error"                                                               # Confirm response status
    assert response_json["message"] == "Missing required keys in 'user_encrypted_location': c1_exp"         # Confirm error message