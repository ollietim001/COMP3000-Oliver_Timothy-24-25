from phe import paillier
import requests
import math
import time
import threading


public_key_n = None

def get_key_authority_public_key():
    global public_key_n
    try:
        # Fetch public key from key authority service
        response = requests.get('http://localhost:5002/get-public-key')
        response.raise_for_status()

        data = response.json()
        public_key_n = data.get('public_key_n')
        public_key = paillier.PaillierPublicKey(public_key_n)
        return public_key

    except requests.exceptions.RequestException as e:
        # Catch HTTP errors (from raise_for_status) and other request-related issues
        print(f"Failed to fetch public key: {e}")
        return None


def compute_and_encrypt_user_location_terms_ref(user_latitude, user_longitude, public_key):

    start_ref = time.time()

    # Terms derived from User point (original, squared, combined, encrypted where applicable)
    alpha = math.cos(user_latitude / 2)
    alpha_sq = alpha**2
    alpha_sq_enc = public_key.encrypt(alpha_sq)
    gamma = math.sin(user_latitude / 2)
    gamma_sq = gamma**2
    gamma_sq_enc = public_key.encrypt(gamma_sq)
    zeta = math.cos(user_latitude)
    theta = math.sin(user_longitude / 2)
    theta_sq = theta**2
    mu = math.cos(user_longitude / 2)
    mu_sq = mu**2

    alpha_gamma_product_A = alpha * gamma            
    alpha_gamma_product_A_enc = public_key.encrypt(alpha_gamma_product_A)       # A-specific part for term2

    zeta_theta_sq_product_A  = zeta * theta_sq          
    zeta_theta_sq_product_A_enc = public_key.encrypt(zeta_theta_sq_product_A)   # A-specific part for term4

    zeta_theta_mu_product_A = zeta * theta * mu
    zeta_theta_mu_product_A_enc = public_key.encrypt(zeta_theta_mu_product_A)   # A-specific part for term5

    zeta_mu_sq_product_A = zeta * mu_sq             
    zeta_mu_sq_product_A_enc = public_key.encrypt(zeta_mu_sq_product_A)

    end_ref = time.time()

    print("(Runtime Performance Experiment) Encryption Runtime Reference:", round((end_ref-start_ref), 3), "s")

    # Print encrypted values to confirm they are encrypted
    print("alpha_sq_enc:", alpha_sq_enc)
    print("gamma_sq_enc:", gamma_sq_enc)
    print("alpha_gamma_product_A_enc:", alpha_gamma_product_A_enc)
    print("zeta_theta_sq_product_A_enc:", zeta_theta_sq_product_A_enc)
    print("zeta_theta_mu_product_A_enc:", zeta_theta_mu_product_A_enc)
    print("zeta_mu_sq_product_A_enc:", zeta_mu_sq_product_A_enc)


    return (alpha_sq_enc, gamma_sq_enc, alpha_gamma_product_A_enc, 
            zeta_theta_sq_product_A_enc, zeta_theta_mu_product_A_enc, 
            zeta_mu_sq_product_A_enc)


def compute_and_encrypt_user_location_terms_prop(user_latitude, user_longitude, public_key):

    start = time.time()

    # Terms derived from User point
    c1 = public_key.encrypt(math.sin(user_latitude))
    c2 = public_key.encrypt(math.cos(user_latitude) * math.cos(user_longitude))
    c3 = public_key.encrypt(math.cos(user_latitude) * math.sin(user_longitude))

    end = time.time()

    print("(Runtime Performance Experiment) Encryption Runtime Proposed:", round((end-start), 3), "s")

    # Print encrypted values to confirm they are encrypted
    print("c1_enc:", c1)
    print("c2_enc:", c2)
    print("c3_enc:", c3)

    return (c1, c2, c3)


def send_encrypted_location_to_geofencing_service_ref(
        alpha_sq_enc, gamma_sq_enc, alpha_gamma_product_A_enc, 
        zeta_theta_sq_product_A_enc, zeta_theta_mu_product_A_enc, 
        zeta_mu_sq_product_A_enc):

    try:
        # Serialize the User's terms
        alpha_sq_ct = alpha_sq_enc.ciphertext()
        alpha_sq_exp = alpha_sq_enc.exponent

        gamma_sq_ct = gamma_sq_enc.ciphertext()
        gamma_sq_exp = gamma_sq_enc.exponent

        alpha_gamma_product_A_ct = alpha_gamma_product_A_enc.ciphertext()
        alpha_gamma_product_A_exp = alpha_gamma_product_A_enc.exponent

        zeta_theta_sq_product_A_ct = zeta_theta_sq_product_A_enc.ciphertext()
        zeta_theta_sq_product_A_exp = zeta_theta_sq_product_A_enc.exponent

        zeta_theta_mu_product_A_ct = zeta_theta_mu_product_A_enc.ciphertext()
        zeta_theta_mu_product_A_exp = zeta_theta_mu_product_A_enc.exponent

        zeta_mu_sq_product_A_ct = zeta_mu_sq_product_A_enc.ciphertext()
        zeta_mu_sq_product_A_exp = zeta_mu_sq_product_A_enc.exponent

        # Create payload
        payload = {
            "user_encrypted_location": {
                "alpha_sq_ct": alpha_sq_ct, "alpha_sq_exp": alpha_sq_exp, 
                "gamma_sq_ct": gamma_sq_ct, "gamma_sq_exp": gamma_sq_exp,
                "alpha_gamma_product_A_ct": alpha_gamma_product_A_ct, "alpha_gamma_product_A_exp": alpha_gamma_product_A_exp,
                "zeta_theta_sq_product_A_ct": zeta_theta_sq_product_A_ct, "zeta_theta_sq_product_A_exp": zeta_theta_sq_product_A_exp,
                "zeta_theta_mu_product_A_ct": zeta_theta_mu_product_A_ct, "zeta_theta_mu_product_A_exp": zeta_theta_mu_product_A_exp,
                "zeta_mu_sq_product_A_ct": zeta_mu_sq_product_A_ct, "zeta_mu_sq_product_A_exp": zeta_mu_sq_product_A_exp
            },
            "public_key_n": public_key_n,
        }
        
        # Make the POST request
        response = requests.post(
            'http://localhost:5001/submit-mobile-node-location-ref',
            json=payload
        )        
    
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        # Catch HTTP errors (from raise_for_status) and other request-related issues
        print(f"Failed to post results to key authority: {e}")
        return None


def send_encrypted_location_to_geofencing_service_prop(c1, c2, c3):

    try:
        # Serialize the User's terms
        c1_ct = c1.ciphertext()
        c1_exp = c1.exponent

        c2_ct = c2.ciphertext()
        c2_exp = c2.exponent

        c3_ct = c3.ciphertext()
        c3_exp = c3.exponent

        # Create payload
        payload = {
            "user_encrypted_location": {
                "c1_ct": c1_ct, "c1_exp": c1_exp, 
                "c2_ct": c2_ct, "c2_exp": c2_exp,
                "c3_ct": c3_ct, "c3_exp": c3_exp
            },
            "public_key_n": public_key_n,
        }
        
        # Make the POST request
        response = requests.post(
            'http://localhost:5001/submit-mobile-node-location-prop',
            json=payload
        )        
    
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        # Catch HTTP errors (from raise_for_status) and other request-related issues
        print(f"Failed to post results to key authority: {e}")
        return None


def scalability_experiment(user_location_terms_ref, user_location_terms_prop, num_requests):
    
    # Simulate multiple requests Referemce system
    start_time_ref = time.time()
    threads = []
    for i in range(num_requests):
        # Send location data to geofencing service
        thread = threading.Thread(target=send_encrypted_location_to_geofencing_service_ref, args=(user_location_terms_ref)) 
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time_ref = time.time()

    # Simulate multiple requests Proposed system
    start_time_prop = time.time()
    threads = []
    for i in range(num_requests):
        # Send location data to geofencing service
        thread = threading.Thread(target=send_encrypted_location_to_geofencing_service_prop, args=(user_location_terms_prop)) 
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time_prop = time.time()


    # Calculate total runtime
    total_runtime_ref = end_time_ref - start_time_ref
    total_runtime_prop = end_time_prop - start_time_prop

    # Calculate throughput and latency
    throughput_ref = num_requests / total_runtime_ref  # Queries per second
    throughput_prop = num_requests / total_runtime_prop
    latency_ref = total_runtime_ref / num_requests     # Average time per query
    latency_prop = total_runtime_prop / num_requests

    # Print results Reference system
    print(f"System runtime for {num_requests} requests excluding encryption runtime: {round(total_runtime_ref, 3)} s")
    print(f"Throughput: {round(throughput_ref, 3)} queries/second")
    print(f"Latency: {round(latency_ref, 3)} seconds/query")

    # Print results Proposed system
    print(f"Proposed system runtime for {num_requests} requests excluding encryption runtime: {round(total_runtime_prop, 3)} s")
    print(f"Proposed system throughput: {round(throughput_prop, 3)} queries/second")
    print(f"Proposed system latency: {round(latency_prop, 3)} seconds/query")


def main():
    # Get public key from key authority service
    public_key = get_key_authority_public_key()

    # User's location in radians
    user_latitude, user_longitude = math.radians(round(51.573037, 5)), math.radians(round(-9.724087, 5))

    # Precompute terms for use in haversine calculation
    user_location_terms = compute_and_encrypt_user_location_terms_ref(user_latitude, user_longitude, public_key)

    # Proposed geofencing system
    user_location_terms_prop = compute_and_encrypt_user_location_terms_prop(user_latitude, user_longitude, public_key)

    # Send location data to geofencing service (Uncomment these and comment scalability test to do runtime performance test)
    # send_encrypted_location_to_geofencing_service_ref(*user_location_terms)
    # send_encrypted_location_to_geofencing_service_prop(*user_location_terms_prop)

    scalability_experiment(user_location_terms, user_location_terms_prop, num_requests=10)


if __name__ == "__main__":
    main()
