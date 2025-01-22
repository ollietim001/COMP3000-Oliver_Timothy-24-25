from flask import Flask, jsonify, request
from phe import paillier
import requests
import overpass
import math
import time


app = Flask(__name__)

# Global variable to store geofence point coordinates
geofence_coordinates = []

def get_geofence_coordinates():
    global geofence_coordinates  # Store globally
    api = overpass.API()         # Initialize Overpass API

    # Define the Overpass query for Sainsbury's supermarkets, using 'out center' to get a single lat/lon for each feature
    # Select individual point locations (nodes)
    # Select linear features or area outlines (ways) e.g. road
    # Select groups of elements (relations), e.g. nodes, ways and other relations
    query = """
    (
      node["shop"="supermarket"]["name"="Sainsbury's"];
      way["shop"="supermarket"]["name"="Sainsbury's"];
      relation["shop"="supermarket"]["name"="Sainsbury's"];
    );
    out center qt;
    """

    try:
        result = api.get(query)     # Send the query to Overpass API, requesting GeoJSON format with central coordinates

        count = 0                   
        numGeofenceBoundaries = 10  # No. of geofence boundaries

        # Extract lat and lon values, round to 5 dp, convert to radians
        for feature in result['features']:
            if count >= numGeofenceBoundaries:                          # Limit to 'n' sainsburys
                break
            lon, lat = feature['geometry']['coordinates']
            lon_rounded, lat_rounded = round(lon, 5), round(lat, 5)                             
            print(f"longitude: {lon_rounded}, latitude: {lat_rounded}") # Print geofences coordinates for testing
            geofence_coordinates.append([math.radians(lon_rounded), math.radians(lat_rounded)])
            count += 1
        
        print("Geofence coordinates fetched successfully.")
    except Exception as e:
        print(f"Failed to fetch geofence coordinates: {e}")

# Fetch the geofence point coordinates once at startup
get_geofence_coordinates()

@app.route("/submit-mobile-node-location", methods=['POST'])
def submit_mobile_node_location():
    # Retrieve JSON payload
    data = request.get_json()
    
    if not data:
        return jsonify({
            "status": "error",
            "message": "Request data is missing"
        }), 400

    # Check if user encrypted location and public key are provided in the payload
    if 'user_encrypted_location' not in data or 'public_key_n' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'user_encrypted_location' or 'public_key_n' in request data"
        }), 400
    
    public_key_n_current = get_key_authority_public_key()
    public_key = paillier.PaillierPublicKey(public_key_n_current)

    # Verify the provided public key matches the server's public key
    if data['public_key_n'] != public_key_n_current:
        return jsonify({
            "status": "error",
            "message": "Public key mismatch. Encryption was not done with the correct public key."
        }), 400
    
    # Extract the user's values from the data
    encrypted_values = extract_encrypted_location(data, public_key)

    # Calculate intermediate values for key authority to decrypt
    intermediate_values = calculate_intermediate_haversine_value(*encrypted_values)

    # Submit intermediate values to key authority
    submit_geofence_results_to_key_authority(public_key_n_current, intermediate_values)

    # Return a success response
    return jsonify({
        "status": "success",
        "message": "Location data recieved"
    }), 200


@app.route("/submit-mobile-node-location-opt", methods=['POST'])
def submit_mobile_node_location_opt():
    # Retrieve JSON payload
    data = request.get_json()
    
    if not data:
        return jsonify({
            "status": "error",
            "message": "Request data is missing"
        }), 400

    # Check if user encrypted location and public key are provided in the payload
    if 'user_encrypted_location' not in data or 'public_key_n' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'user_encrypted_location' or 'public_key_n' in request data"
        }), 400
    
    public_key_n_current = get_key_authority_public_key()
    public_key = paillier.PaillierPublicKey(public_key_n_current)

    # Verify the provided public key matches the server's public key
    if data['public_key_n'] != public_key_n_current:
        return jsonify({
            "status": "error",
            "message": "Public key mismatch. Encryption was not done with the correct public key."
        }), 400
    
    # Extract the user's values from the data
    encrypted_values = extract_encrypted_location_opt(data, public_key)

    # Calculate intermediate values for key authority to decrypt
    intermediate_values = calculate_intermediate_haversine_value_opt(*encrypted_values)

    # Submit intermediate values to key authority
    submit_opt_geofence_results_to_key_authority(public_key_n_current, intermediate_values)

    # Return a success response
    return jsonify({
        "status": "success",
        "message": "Location data recieved"
    }), 200
    
def get_key_authority_public_key():
    try:
        response = requests.get('http://keyauthority:5002/get-public-key')
        response.raise_for_status()

        data = response.json()
        return data.get('public_key_n') 

    except requests.exceptions.RequestException as e:
        # Catch HTTP errors (from raise_for_status) and other request-related issues
        print(f"Failed to fetch public key: {e}")
        return None
    

def extract_encrypted_location(data, public_key):
    # Define the required keys for 'user_encrypted_location'
    required_keys = [
        'alpha_sq_ct', 'alpha_sq_exp',
        'gamma_sq_ct', 'gamma_sq_exp',
        'alpha_gamma_product_A_ct', 'alpha_gamma_product_A_exp', 
        'zeta_theta_sq_product_A_ct', 'zeta_theta_sq_product_A_exp',
        'zeta_theta_mu_product_A_ct', 'zeta_theta_mu_product_A_exp',
        'zeta_mu_sq_product_A_ct', 'zeta_mu_sq_product_A_exp'
    ]
    
    # Check for missing keys
    missing_keys = [key for key in required_keys if key not in data['user_encrypted_location']]
    
    if missing_keys:
        return jsonify({
            "status": "error",
            "message": f"Missing required keys in 'user_encrypted_location': {', '.join(missing_keys)}"
        }), 400
    
    # Extract and deserialize data
    user_location_data = data['user_encrypted_location']
    alpha_sq = paillier.EncryptedNumber(public_key, user_location_data.get('alpha_sq_ct'), user_location_data.get('alpha_sq_exp'))
    gamma_sq = paillier.EncryptedNumber(public_key, user_location_data.get('gamma_sq_ct'), user_location_data.get('gamma_sq_exp'))
    alpha_gamma_product_A = paillier.EncryptedNumber(public_key, user_location_data.get('alpha_gamma_product_A_ct'), user_location_data.get('alpha_gamma_product_A_exp'))
    zeta_theta_sq_product_A = paillier.EncryptedNumber(public_key, user_location_data.get('zeta_theta_sq_product_A_ct'), user_location_data.get('zeta_theta_sq_product_A_exp'))
    zeta_theta_mu_product_A = paillier.EncryptedNumber(public_key, user_location_data.get('zeta_theta_mu_product_A_ct'), user_location_data.get('zeta_theta_mu_product_A_exp'))
    zeta_mu_sq_product_A = paillier.EncryptedNumber(public_key, user_location_data.get('zeta_mu_sq_product_A_ct'), user_location_data.get('zeta_mu_sq_product_A_exp'))
    
    # Print encrypted values to confirm they are encrypted
    print("alpha_sq_enc:", alpha_sq)
    print("gamma_sq_enc:", gamma_sq)
    print("alpha_gamma_product_A_enc:", alpha_gamma_product_A)
    print("zeta_theta_sq_product_A_enc:", zeta_theta_sq_product_A)
    print("zeta_theta_mu_product_A_enc:", zeta_theta_mu_product_A)
    print("zeta_mu_sq_product_A_enc:", zeta_mu_sq_product_A)

    # Return User's encrypted values
    return (alpha_sq, gamma_sq, alpha_gamma_product_A,
            zeta_theta_sq_product_A, zeta_theta_mu_product_A,
            zeta_mu_sq_product_A)

def extract_encrypted_location_opt(data, public_key):
    # Define the required keys for 'user_encrypted_location'
    required_keys = [
        'c1_ct', 'c1_exp',
        'c2_ct', 'c2_exp',
        'c3_ct', 'c3_exp'
    ]
    
    # Check for missing keys
    missing_keys = [key for key in required_keys if key not in data['user_encrypted_location']]
    
    if missing_keys:
        return jsonify({
            "status": "error",
            "message": f"Missing required keys in 'user_encrypted_location': {', '.join(missing_keys)}"
        }), 400
    
    # Extract and deserialize data
    user_location_data = data['user_encrypted_location']
    c1 = paillier.EncryptedNumber(public_key, user_location_data.get('c1_ct'), user_location_data.get('c1_exp'))
    c2 = paillier.EncryptedNumber(public_key, user_location_data.get('c2_ct'), user_location_data.get('c2_exp'))
    c3 = paillier.EncryptedNumber(public_key, user_location_data.get('c3_ct'), user_location_data.get('c3_exp'))

    
    # Print encrypted values to confirm they are encrypted
    print("c1:", c1)
    print("c2:", c2)
    print("c3:", c3)

    # Return User's encrypted values
    return (c1, c2, c3)

def calculate_intermediate_haversine_value(
        alpha_sq, gamma_sq, alpha_gamma_product_A, 
        zeta_theta_sq_product_A, zeta_theta_mu_product_A, zeta_mu_sq_product_A
        ):
    
    start = time.time()

    haversine_intermediate_values = []

    for center_longitude, center_latitude in geofence_coordinates: 
        # Terms derived from Center point (original, squared, and combined where applicable)
        beta = math.sin(center_latitude / 2)
        beta_sq = beta**2
        delta = math.cos(center_latitude / 2)
        delta_sq = delta**2
        eta = math.cos(center_latitude)
        lambda_ = math.cos(center_longitude / 2)
        lambda_sq = lambda_**2
        nu = math.sin(center_longitude / 2)
        nu_sq = nu**2

        beta_delta_product_B = beta * delta             # B-specific part for term2
        eta_lambda_sq_product_B = eta * lambda_sq       # B-specific part for term4
        eta_lambda_nu_product_B = eta * lambda_ * nu    # B-specific part for term5
        eta_nu_sq_product_B = eta * nu_sq               # B-specific part for term6
        
        # Compute haversine intermediate value
        term1 = alpha_sq * beta_sq
        term2 = -2 * (alpha_gamma_product_A * beta_delta_product_B)
        term3 = gamma_sq * delta_sq
        term4 = zeta_theta_sq_product_A * eta_lambda_sq_product_B
        term5 = -2 * (zeta_theta_mu_product_A * eta_lambda_nu_product_B)
        term6 = zeta_mu_sq_product_A * eta_nu_sq_product_B
        haversine_intermediate = term1 + term2 + term3 + term4 + term5 + term6

        haversine_intermediate_values.append(haversine_intermediate)  # Store computation result

    end = time.time()

    print("(Runtime Performance Experiment) Computation Runtime:", round((end-start), 3), "s")

    # Serialize results after timing ends
    serialized_values = []
    for intermediate_value in haversine_intermediate_values:
        ciphertext = intermediate_value.ciphertext()
        exponent = intermediate_value.exponent
        serialized_values.append({'ciphertext': ciphertext, 'exponent': exponent})

    return serialized_values


def calculate_intermediate_haversine_value_opt(c1, c2, c3):
    
    start = time.time()

    haversine_intermediate_values = []

    for center_longitude, center_latitude in geofence_coordinates: 
        # Compute haversine intermediate value
        
        haversine_intermediate = 1 - c1 * math.sin(center_latitude) - c2 * math.cos(center_latitude) * math.cos(center_longitude) - c3 * math.cos(center_latitude) * math.sin(center_longitude)

        haversine_intermediate_values.append(haversine_intermediate)  # Store computation result

    end = time.time()

    print("(Runtime Performance Experiment) Computation Runtime Optimised:", round((end-start), 3), "s")

    # Serialize results after timing ends
    serialized_values = []
    for intermediate_value in haversine_intermediate_values:
        ciphertext = intermediate_value.ciphertext()
        exponent = intermediate_value.exponent
        serialized_values.append({'ciphertext': ciphertext, 'exponent': exponent})

    return serialized_values


def submit_geofence_results_to_key_authority(public_key_n, intermediate_values):
    try:
        payload = {
            "public_key_n": public_key_n,
            "encrypted_results": intermediate_values
        }
        
        # Make the POST request
        response = requests.post(
            'http://keyauthority:5002/submit-geofence-result',
            json=payload
        )        
        
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        # Catch HTTP errors (from raise_for_status) and other request-related issues
        print(f"Failed to post results to key authority: {e}")
        return None

   
def submit_opt_geofence_results_to_key_authority(public_key_n, intermediate_values):
    try:
        payload = {
            "public_key_n": public_key_n,
            "encrypted_results": intermediate_values
        }
        
        # Make the POST request
        response = requests.post(
            'http://keyauthority:5002/submit-geofence-result-opt',
            json=payload
        )        
        
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        # Catch HTTP errors (from raise_for_status) and other request-related issues
        print(f"Failed to post results to key authority: {e}")
        return None


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001) 