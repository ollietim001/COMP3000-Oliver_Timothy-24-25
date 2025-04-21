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
    # Initialize Overpass API
    api = overpass.API(timeout=60000)  # 60s timeout (If timeout error occurs: Increase timeout or reduce 'out qt' to a lower number reducing number of geofences fetched 

    # Define the Overpass query for cafes, to get a single lat/lon for each feature
    # Select individual point locations (nodes)
    # If changing this check docker logs to make sure is "Number of processed geofence coordinates:" matches numGeofenceBoundaries
    query = """
    node["amenity"="cafe"](50.0,-10.0,60.0,2.0);
    out qt 1000;
    """

    try:
        result = api.get(query)     # Send the query to Overpass API, requesting GeoJSON format with central coordinates
        num_coordinates = len(result['features'])
        print(f"Total lon-lat pairs: {num_coordinates}")

        numGeofenceBoundaries = 500  # No. of geofence boundaries (Change this if you want more geofences, note this must not exceed 'out qt' value)

        # Raise an exception if there are fewer coordinates than required geofence boundaries
        if num_coordinates < numGeofenceBoundaries:
            raise ValueError(f"Insufficient coordinates: Found {num_coordinates}, but need at least {numGeofenceBoundaries}")
        
        # Extract lat and lon values, round to 5 dp, convert to radians
        for i in range(numGeofenceBoundaries):  # Limit to 'n' Cafes
            feature = result['features'][i]
            lon, lat = feature['geometry']['coordinates']
            lon_rounded, lat_rounded = round(lon, 6), round(lat, 6)

            '''
            To prevent floating-point equality after rounding (e.g., 28.523500 == 28.52350),
            which cause math domain errors in encrypted trigonometric operations,
            we add a small offset (1e-6) to the coordinate if both lon and lat end in zero.
            This offset shifts the coordinate by ~11.1 cm — negligible for geofencing accuracy.
            '''

            # Convert to string to check the last decimal digit
            lon_str = f"{lon_rounded:.{6}f}"
            lat_str = f"{lat_rounded:.{6}f}"

            if lon_str[-1] == "0" and lat_str[-1] == "0":
            # Add a tiny offset to lat_rounded to make last digit a '1' 
                lat_rounded += 10**-6  # 0.000001
                lat_rounded = round(lat_rounded, 6)  # Round again just in case

            print(f"longitude: {lon_rounded}, latitude: {lat_rounded}") # Print geofences coordinates for testing
            geofence_coordinates.append([math.radians(lon_rounded), math.radians(lat_rounded)])
        
        print(f"Number of processed geofence coordinates: {len(geofence_coordinates)}")
        print("Geofence coordinates fetched successfully.")
    except Exception as e:
            print(f"Failed to fetch geofence coordinates: {e.__class__.__name__}: {e}")
            

# Fetch the geofence point coordinates once at startup
get_geofence_coordinates()

@app.route("/submit-user-location-ref", methods=['POST'])
def submit_user_location_ref():
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
    
    public_key_n_current = get_carer_public_key()
    public_key = paillier.PaillierPublicKey(public_key_n_current)

    # Verify the provided public key matches the server's public key
    if data['public_key_n'] != public_key_n_current:
        return jsonify({
            "status": "error",
            "message": "Public key mismatch. Encryption was not done with the correct public key."
        }), 400
    
    # Extract the user's values from the data
    try:
        encrypted_values = extract_encrypted_location_ref(data, public_key)
    except ValueError as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 400
    
    request_size = len(request.data)
    # Write Recieved Communication KB Reference to file
    with open("commGeoOutRef.txt", "a") as f:
        f.write(f"{request_size/1024}\n")

    # Calculate intermediate values for carer to decrypt
    intermediate_values = calculate_intermediate_haversine_value_ref(*encrypted_values, data['number_of_geofences'])

    # Submit intermediate values to carer
    submit_geofence_results_to_carer(public_key_n_current, intermediate_values, "submit-geofence-result-ref")

    # Return a success response
    return jsonify({
        "status": "success",
        "message": "Location data recieved"
    }), 200


@app.route("/submit-user-location-prop", methods=['POST'])
def submit_user_location_prop():
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
    
    public_key_n_current = get_carer_public_key()
    public_key = paillier.PaillierPublicKey(public_key_n_current)

    # Verify the provided public key matches the carer's public key
    if data['public_key_n'] != public_key_n_current:
        return jsonify({
            "status": "error",
            "message": "Public key mismatch. Encryption was not done with the correct public key."
        }), 400
    
    # Extract the user's values from the data
    try:
        encrypted_values = extract_encrypted_location_prop(data, public_key)
    except ValueError as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 400
    
    request_size = len(request.data)
    # Write Recieved Communication KB Proposed to file
    with open("commGeoOutProp.txt", "a") as f:
        f.write(f"{request_size/1024}\n")

    # Calculate intermediate values for carer to decrypt
    intermediate_values = calculate_intermediate_haversine_value_prop(*encrypted_values, data['number_of_geofences'])

    # Submit intermediate values to key authority
    submit_geofence_results_to_carer(public_key_n_current, intermediate_values, "submit-geofence-result-prop")

    # Return a success response
    return jsonify({
        "status": "success",
        "message": "Location data recieved"
    }), 200
    
def get_carer_public_key():
    try:
        response = requests.get('http://carer:5002/get-public-key')
        response.raise_for_status()

        data = response.json()
        return data.get('public_key_n') 

    except requests.exceptions.RequestException as e:
        # Catch HTTP errors (from raise_for_status) and other request-related issues
        print(f"Failed to fetch public key: {e}")
        return None
    

def extract_encrypted_location_ref(data, public_key):
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
        raise ValueError(f"Missing required keys in 'user_encrypted_location': {', '.join(missing_keys)}")
    
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

def extract_encrypted_location_prop(data, public_key):
    # Define the required keys for 'user_encrypted_location'
    required_keys = [
        'c1_ct', 'c1_exp',
        'c2_ct', 'c2_exp',
        'c3_ct', 'c3_exp'
    ]
    
    # Check for missing keys
    missing_keys = [key for key in required_keys if key not in data['user_encrypted_location']]
    
    if missing_keys:
        raise ValueError(f"Missing required keys in 'user_encrypted_location': {', '.join(missing_keys)}")
    
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

def calculate_intermediate_haversine_value_ref(
        alpha_sq, gamma_sq, alpha_gamma_product_A, 
        zeta_theta_sq_product_A, zeta_theta_mu_product_A, zeta_mu_sq_product_A,
        number_of_geofences):
    
    start = time.time()

    haversine_intermediate_values = []

    for center_longitude, center_latitude in geofence_coordinates[:number_of_geofences]: 
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

    print("(Runtime Performance Experiment) Computation Runtime Reference:", round((end-start), 3), "s")

    # Write Computation Runtime Reference to file
    with open("runCompOutRef.txt", "a") as f:
        f.write(f"{(end-start)}\n")

    # Serialize results after timing ends
    serialized_values = []
    for intermediate_value in haversine_intermediate_values:
        ciphertext = intermediate_value.ciphertext()
        exponent = intermediate_value.exponent
        serialized_values.append({'ciphertext': ciphertext, 'exponent': exponent})

    return serialized_values


def calculate_intermediate_haversine_value_prop(c1, c2, c3, number_of_geofences):
    
    start = time.time()

    haversine_intermediate_values = []

    for center_longitude, center_latitude in geofence_coordinates[:number_of_geofences]: 
        # Compute haversine intermediate value
        
        haversine_intermediate = c1 * math.sin(center_latitude) - c2 * math.cos(center_latitude) * math.cos(center_longitude) - c3 * math.cos(center_latitude) * math.sin(center_longitude)

        haversine_intermediate_values.append(haversine_intermediate)  # Store computation result

    end = time.time()

    print("(Runtime Performance Experiment) Computation Runtime Proposed:", round((end-start), 3), "s")

    # Write Computation Runtime Proposed to file
    with open("runCompOutProp.txt", "a") as f:
        f.write(f"{(end-start)}\n")

    # Serialize results after timing ends
    serialized_values = []
    for intermediate_value in haversine_intermediate_values:
        ciphertext = intermediate_value.ciphertext()
        exponent = intermediate_value.exponent
        serialized_values.append({'ciphertext': ciphertext, 'exponent': exponent})

    return serialized_values


def submit_geofence_results_to_carer(public_key_n, intermediate_values, endpoint):
    try:
        payload = {
            "public_key_n": public_key_n, 
            "encrypted_results": intermediate_values
        }
        
        # Make the POST request
        response = requests.post(
            f"http://carer:5002/{endpoint}",
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