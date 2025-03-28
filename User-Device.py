from phe import paillier
import requests
import math
import time
import threading
import stats
import numpy as np
import pandas as pd
import argparse
from tabulate import tabulate


public_key_n = None

def get_carer_public_key():
    global public_key_n
    try:
        # Fetch public key from carer's devoce
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

    # Write Encryption Runtime Reference to file
    with open("Outputs/runEncOutRef.txt", "a") as f:
        f.write(f"{(end_ref-start_ref)}\n")

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

    # Write Encryption Runtime Proposed to file
    with open("Outputs/runEncOutProp.txt", "a") as f:
        f.write(f"{(end-start)}\n")

    # Print encrypted values to confirm they are encrypted
    print("c1_enc:", c1)
    print("c2_enc:", c2)
    print("c3_enc:", c3)

    return (c1, c2, c3)


def send_encrypted_location_to_geofencing_service_ref(
        alpha_sq_enc, gamma_sq_enc, alpha_gamma_product_A_enc, 
        zeta_theta_sq_product_A_enc, zeta_theta_mu_product_A_enc, 
        zeta_mu_sq_product_A_enc, number_of_geofences=10):

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
            "number_of_geofences": number_of_geofences,
        }
        
        # Make the POST request
        response = requests.post(
            'http://localhost:5001/submit-user-location-ref',
            json=payload
        )        
    
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        # Catch HTTP errors (from raise_for_status) and other request-related issues
        print(f"Failed to post results: {e}")
        return None


def send_encrypted_location_to_geofencing_service_prop(c1, c2, c3, number_of_geofences=10):

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
            "number_of_geofences": number_of_geofences,
        }
        
        # Make the POST request
        response = requests.post(
            'http://localhost:5001/submit-user-location-prop',
            json=payload
        )        
    
        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        # Catch HTTP errors (from raise_for_status) and other request-related issues
        print(f"Failed to post results: {e}")
        return None


def scalability_experiment(user_location_terms_ref, user_location_terms_prop, num_repitions_mean):
    tableResults = []

    # Output files with temporary data
    files= ["Outputs/scaleRunOutRef.txt", "Outputs/scaleRunOutProp.txt", "Outputs/scaleThroughputOutRef.txt", "Outputs/scaleThroughputOutProp.txt", "Outputs/scaleLatencyOutRef.txt", "Outputs/scaleLatencyOutProp.txt"]

    requests_counts = [1, 10, 50, 100]

    # Run different test cases
    for num_requests in requests_counts:

        # Clear output files of temporary data
        for file_name in files:
            with open(file_name, 'w'):
                pass

        # Repeat for average
        for i in range(num_repitions_mean):

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

            # Write Total Runtime Reference to file
            with open("Outputs/scaleRunOutRef.txt", "a") as f:
                f.write(f"{(total_runtime_ref)}\n")

            # Write Total Runtime Proposed to file
            with open("Outputs/scaleRunOutProp.txt", "a") as f:
                f.write(f"{(total_runtime_prop)}\n")
            
            # Write Throughput Reference to file
            with open("Outputs/scaleThroughputOutRef.txt", "a") as f:
                f.write(f"{(throughput_ref)}\n")

            # Write Throughput Proposed to file
            with open("Outputs/scaleThroughputOutProp.txt", "a") as f:
                f.write(f"{(throughput_prop)}\n")

            # Write Latency Reference to file
            with open("Outputs/scaleLatencyOutRef.txt", "a") as f:
                f.write(f"{(latency_ref)}\n")

            # Write Latency Proposed to file
            with open("Outputs/scaleLatencyOutProp.txt", "a") as f:
                f.write(f"{(latency_prop)}\n")

        # Calculate staistics and present in table
        scalability_stats = stats.main(files)

        tableResults.append(
            [num_requests,"Runtime (s)", 
            f"{round(scalability_stats[0]['Mean'], 3)} ± {round(scalability_stats[0]['Standard Deviation'], 3)} (95% CI: {round(scalability_stats[0]['95% Confidence Interval'][0], 3)}, {round(scalability_stats[0]['95% Confidence Interval'][1], 3)})", 
            f"{round(scalability_stats[1]['Mean'], 3)} ± {round(scalability_stats[1]['Standard Deviation'], 3)} (95% CI: {round(scalability_stats[1]['95% Confidence Interval'][0], 3)}, {round(scalability_stats[1]['95% Confidence Interval'][1], 3)})"]
        )

        tableResults.append(
            ["", "Throughput (q/s)", 
            f"{round(scalability_stats[2]['Mean'], 3)} ± {round(scalability_stats[2]['Standard Deviation'], 3)} (95% CI: {round(scalability_stats[2]['95% Confidence Interval'][0], 3)}, {round(scalability_stats[2]['95% Confidence Interval'][1], 3)})", 
            f"{round(scalability_stats[3]['Mean'], 3)} ± {round(scalability_stats[3]['Standard Deviation'], 3)} (95% CI: {round(scalability_stats[3]['95% Confidence Interval'][0], 3)}, {round(scalability_stats[3]['95% Confidence Interval'][1], 3)})"]
        )

        tableResults.append(            
            ["", "Latency (s/q)", 
            f"{round(scalability_stats[4]['Mean'], 3)} ± {round(scalability_stats[4]['Standard Deviation'], 3)} (95% CI: {round(scalability_stats[4]['95% Confidence Interval'][0], 3)}, {round(scalability_stats[4]['95% Confidence Interval'][1], 3)})", 
            f"{round(scalability_stats[5]['Mean'], 3)} ± {round(scalability_stats[5]['Standard Deviation'], 3)} (95% CI: {round(scalability_stats[5]['95% Confidence Interval'][0], 3)}, {round(scalability_stats[5]['95% Confidence Interval'][1], 3)})"]
        )


    head = ["Queries", "Metric", "Ref. Alg.", "Prop. Alg."]

    save_results(tableResults, head, "Results/scalability.csv")

    print(f"Scalability results saved to Results/scalability.csv\n")

    # # Print results Reference system
    # print(f"System runtime for {num_requests} requests excluding encryption runtime: {round(total_runtime_ref, 3)} s")
    # print(f"Throughput: {round(throughput_ref, 3)} queries/second")
    # print(f"Latency: {round(latency_ref, 3)} seconds/query")

    # # Print results Proposed system
    # print(f"Proposed system runtime for {num_requests} requests excluding encryption runtime: {round(total_runtime_prop, 3)} s")
    # print(f"Proposed system throughput: {round(throughput_prop, 3)} queries/second")
    # print(f"Proposed system latency: {round(latency_prop, 3)} seconds/query")


def runtime_experiment(user_latitude, user_longitude, public_key, num_repitions_mean):
    tableResults = []
    commTableResults = []

    # Output files with temporary data
    files = ["Outputs/runEncOutRef.txt", "Outputs/runEncOutProp.txt", "Outputs/runCompOutRef.txt", "Outputs/runCompOutProp.txt", "Outputs/runDecOutRef.txt", "Outputs/runDecOutProp.txt", "Outputs/runTotalOutRef.txt", "Outputs/runTotalOutProp.txt",
             "Outputs/commGeoOutRef.txt", "Outputs/commGeoOutProp.txt", "Outputs/commCarerOutRef.txt", "Outputs/commCarerOutProp.txt"
    ]

    geofence_counts = [1, 10, 100, 200, 300]

    # Run different test cases
    for num_geofences in geofence_counts:

        # Clear output files of temporary data
        for file_name in files:
            with open(file_name, 'w'):
                pass

        # Repeat for average
        for i in range(num_repitions_mean):

            # Compute user terms
            user_location_terms = compute_and_encrypt_user_location_terms_ref(user_latitude, user_longitude, public_key)
            user_location_terms_prop = compute_and_encrypt_user_location_terms_prop(user_latitude, user_longitude, public_key)
            # Send location data to geofencing service
            send_encrypted_location_to_geofencing_service_ref(*user_location_terms, number_of_geofences=num_geofences)
            send_encrypted_location_to_geofencing_service_prop(*user_location_terms_prop, number_of_geofences=num_geofences)

        # Load temporary data to calculate total runtime and save in temporary file
        data1 = np.loadtxt(files[0], dtype=float)
        data2 = np.loadtxt(files[1], dtype=float)
        data3 = np.loadtxt(files[2], dtype=float)
        data4 = np.loadtxt(files[3], dtype=float)
        data5 = np.loadtxt(files[4], dtype=float)
        data6 = np.loadtxt(files[5], dtype=float)

        total_runtime_ref = data1 + data3 + data5
        total_runtime_prop = data2 + data4 + data6

        np.savetxt(files[6], total_runtime_ref)
        np.savetxt(files[7], total_runtime_prop)

        # Calculate staistics and present in table
        runtime_stats = stats.main(files)

        tableResults.append(
            [num_geofences,"Encryption (s)", 
            f"{round(runtime_stats[0]['Mean'], 3)} ± {round(runtime_stats[0]['Standard Deviation'], 3)} (95% CI: {round(runtime_stats[0]['95% Confidence Interval'][0], 3)}, {round(runtime_stats[0]['95% Confidence Interval'][1], 3)})", 
            f"{round(runtime_stats[1]['Mean'], 3)} ± {round(runtime_stats[1]['Standard Deviation'], 3)} (95% CI: {round(runtime_stats[1]['95% Confidence Interval'][0], 3)}, {round(runtime_stats[1]['95% Confidence Interval'][1], 3)})"]
        )

        tableResults.append(
            ["", "Computation (s)", 
            f"{round(runtime_stats[2]['Mean'], 3)} ± {round(runtime_stats[2]['Standard Deviation'], 3)} (95% CI: {round(runtime_stats[2]['95% Confidence Interval'][0], 3)}, {round(runtime_stats[2]['95% Confidence Interval'][1], 3)})", 
            f"{round(runtime_stats[3]['Mean'], 3)} ± {round(runtime_stats[3]['Standard Deviation'], 3)} (95% CI: {round(runtime_stats[3]['95% Confidence Interval'][0], 3)}, {round(runtime_stats[3]['95% Confidence Interval'][1], 3)})"]
        )

        tableResults.append(            
            ["", "Decryption (s)", 
            f"{round(runtime_stats[4]['Mean'], 3)} ± {round(runtime_stats[4]['Standard Deviation'], 3)} (95% CI: {round(runtime_stats[4]['95% Confidence Interval'][0], 3)}, {round(runtime_stats[4]['95% Confidence Interval'][1], 3)})", 
            f"{round(runtime_stats[5]['Mean'], 3)} ± {round(runtime_stats[5]['Standard Deviation'], 3)} (95% CI: {round(runtime_stats[5]['95% Confidence Interval'][0], 3)}, {round(runtime_stats[5]['95% Confidence Interval'][1], 3)})"]
        )

        tableResults.append(            
            ["", "Total Runtime (s)", 
            f"{round(runtime_stats[6]['Mean'], 3)} ± {round(runtime_stats[6]['Standard Deviation'], 3)} (95% CI: {round(runtime_stats[6]['95% Confidence Interval'][0], 3)}, {round(runtime_stats[6]['95% Confidence Interval'][1], 3)})", 
            f"{round(runtime_stats[7]['Mean'], 3)} ± {round(runtime_stats[7]['Standard Deviation'], 3)} (95% CI: {round(runtime_stats[7]['95% Confidence Interval'][0], 3)}, {round(runtime_stats[7]['95% Confidence Interval'][1], 3)})"]
        )

        # Runtime tests include communication overhead
        commTableResults.append(
            [num_geofences,"Geofencing Recieved Communication (KB)", 
            f"{round(runtime_stats[8]['Mean'], 3)}", 
            f"{round(runtime_stats[9]['Mean'], 3)}"]
        )

        commTableResults.append(
            ["","Carer Device Received Communication (KB)", 
            f"{round(runtime_stats[10]['Mean'], 3)}", 
            f"{round(runtime_stats[11]['Mean'], 3)}"]
        )


    head = ["Geofences", "Metric", "Ref. Alg.", "Prop. Alg."]
    head_comm = ["Geofences", "Metric", "Ref. Alg.", "Prop. Alg."]

    save_results(tableResults, head, "Results/runtime_performance.csv")
    save_results(commTableResults, head_comm, "Results/communication.csv")

    print(f"Runtime performance results saved to Results/runtime_performance.csv\n")
    print(f"Communication results saved to Results/communication.csv\n")


def save_results(table_data, headers, filename):
    df = pd.DataFrame(table_data, columns=headers)
    df.to_csv(filename, index=False, encoding="utf-8-sig")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run basic or experimental tests on geofencing system"
    )

    parser.add_argument(
        "-m", "--mode",
        choices=["basic", "runtime", "scalability"],
        default="basic",
        help="Run mode: basic (just send location), runtime (incl. communication overhead experiment), scalability"
    )

    parser.add_argument(
        "-r", "--repetitions",
        type=int,
        default=30,
        help="Number of repetitions for runtime/scalability experiments to calculate mean"
    )

    parser.add_argument(
        "-gc", "--geofence-count",
        type=int,
        default=10,
        help="Number of geofences to simulate (only used in basic mode)"
    )

    return parser.parse_args()

def main():

    args = parse_arguments()

    # Get public key from carer's device
    public_key = get_carer_public_key()

    # User's location in radians
    user_latitude, user_longitude = math.radians(round(51.573037, 5)), math.radians(round(-9.724087, 5))

    # Precompute terms for use in haversine calculation
    user_location_terms = compute_and_encrypt_user_location_terms_ref(user_latitude, user_longitude, public_key)

    # Proposed geofencing system
    user_location_terms_prop = compute_and_encrypt_user_location_terms_prop(user_latitude, user_longitude, public_key)

    # Handle selected mode
    if args.mode == "basic":
        send_encrypted_location_to_geofencing_service_ref(*user_location_terms, number_of_geofences=args.geofence_count)
        send_encrypted_location_to_geofencing_service_prop(*user_location_terms_prop, number_of_geofences=args.geofence_count)

    elif args.mode == "runtime":
        # Measures the runtime performance of the systems (incl. communication overhead experiment)
        runtime_experiment(user_latitude, user_longitude, public_key, num_repitions_mean=args.repetitions)

    elif args.mode == "scalability":
        # Evaluates the systems scalability under varying request loads
        scalability_experiment(user_location_terms, user_location_terms_prop, num_repitions_mean=args.repetitions)


if __name__ == "__main__":
    main()
