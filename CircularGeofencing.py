from phe import paillier
import math
import time
import random
import matplotlib.pyplot as plt
import stats
import argparse
import pandas as pd
from tabulate import tabulate


def generate_user_points(center_latitude, center_longitude, radius, earth_radius, num_points=10):
    points_inside = []
    points_outside = []
    points_edge = []

    for k in range(num_points):
        # Generate inside points
        random_theta = random.uniform(0, 2 * math.pi)                       # Generate a random angle (theta) in radians, between 0 and 2π (full circle)
        random_distance = random.uniform(0, radius)                         # Generate a random distance less than the radius ensuring the point is inside the geofence
        offset_lat = random_distance / earth_radius                         # Calculate latitude offset by scaling the random distance to an angular value
        offset_lon = offset_lat / math.cos(center_latitude)                 # Calculate longitude offset, adjusted by the cosine of the center latitude   
        inside_lat = center_latitude + offset_lat * math.sin(random_theta)  # Calculate new latitude by adding the vertical offset
        inside_lon = center_longitude + offset_lon * math.cos(random_theta) # Calculate new longitude by adding the horizontal offset
        points_inside.append((inside_lat, inside_lon))

        # Generate outside points
        random_theta = random.uniform(0, 2 * math.pi)
        random_distance = random.uniform(radius + 1, radius * 2)  # Greater than radius
        offset_lat = random_distance / earth_radius
        offset_lon = offset_lat / math.cos(center_latitude)
        outside_lat = center_latitude + offset_lat * math.sin(random_theta)
        outside_lon = center_longitude + offset_lon * math.cos(random_theta)
        points_outside.append((outside_lat, outside_lon))

        # Generate edge points
        random_theta = random.uniform(0, 2 * math.pi)
        offset_lat = radius / earth_radius
        offset_lon = offset_lat / math.cos(center_latitude)
        edge_lat = center_latitude + offset_lat * math.sin(random_theta)
        edge_lon = center_longitude + offset_lon * math.cos(random_theta)
        points_edge.append((edge_lat, edge_lon))

    return points_inside, points_outside, points_edge


def haversine(user_latitude, user_longitude, center_latitude, center_longitude, earth_radius):
    a = math.sin((user_latitude - center_latitude)/2)**2 + math.cos(user_latitude) * math.cos(center_latitude) * math.sin((user_longitude - center_longitude)/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = earth_radius * c
    return distance


def evaluate_geofence(user_latitude, user_longitude, center_latitude, center_longitude, radius, earth_radius):
    distance = haversine(user_latitude, user_longitude, center_latitude, center_longitude, earth_radius)
    # print(f"Distance from geofence centre: {round(distance, 2)} meters")
    return 1 if distance <= radius else 0


def initialize_keys():
    public_key, private_key = paillier.generate_paillier_keypair()
    return public_key, private_key

# Reference encrypted haversine system

def ref_precompute_user_terms(user_latitude, user_longitude, public_key):
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
    zeta_mu_sq_product_A_enc = public_key.encrypt(zeta_mu_sq_product_A)         # A-specific part for term6

    # Return all precomputed terms as a dictionary
    return {
        'alpha_sq_enc': alpha_sq_enc,
        'gamma_sq_enc': gamma_sq_enc,
        'alpha_gamma_product_A_enc': alpha_gamma_product_A_enc,
        'zeta_theta_sq_product_A_enc': zeta_theta_sq_product_A_enc,
        'zeta_theta_mu_product_A_enc': zeta_theta_mu_product_A_enc,
        'zeta_mu_sq_product_A_enc': zeta_mu_sq_product_A_enc,
    }


def ref_calculate_intermediate_haversine_value(user_precomputed, center_latitude, center_longitude):
    # Extract precomputed user terms
    alpha_sq_enc = user_precomputed['alpha_sq_enc']
    gamma_sq_enc = user_precomputed['gamma_sq_enc']
    alpha_gamma_product_A_enc = user_precomputed['alpha_gamma_product_A_enc']
    zeta_theta_sq_product_A_enc = user_precomputed['zeta_theta_sq_product_A_enc']
    zeta_theta_mu_product_A_enc = user_precomputed['zeta_theta_mu_product_A_enc']
    zeta_mu_sq_product_A_enc = user_precomputed['zeta_mu_sq_product_A_enc']

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
    term1 = alpha_sq_enc * beta_sq
    term2 = -2 * (alpha_gamma_product_A_enc * beta_delta_product_B)
    term3 = gamma_sq_enc * delta_sq
    term4 = zeta_theta_sq_product_A_enc * eta_lambda_sq_product_B
    term5 = -2 * (zeta_theta_mu_product_A_enc * eta_lambda_nu_product_B)
    term6 = zeta_mu_sq_product_A_enc * eta_nu_sq_product_B
    haversine_intermediate = term1 + term2 + term3 + term4 + term5 + term6

    return haversine_intermediate


def ref_evaluate_geofence_encrypted(encrypted_result, radius, earth_radius, private_key):
    haversine_intermediate = private_key.decrypt(encrypted_result)

    central_angle = 2 * math.atan2(math.sqrt(haversine_intermediate), math.sqrt(1 - haversine_intermediate))

    distance = earth_radius * central_angle 
    # print(f"Distance from geofence centre: {round(distance, 2)} meters")

    # Return 1 if distance is within the radius, else 0
    return 1 if distance <= radius else 0

# End of Reference encrypted haversine system

# Proposed encrypted haversine system
def prop_precompute_user_terms(user_latitude, user_longitude, public_key):
    # Terms derived from User point
    c1 = public_key.encrypt(math.sin(user_latitude))
    c2 = public_key.encrypt(math.cos(user_latitude) * math.cos(user_longitude))
    c3 = public_key.encrypt(math.cos(user_latitude) * math.sin(user_longitude))

    # Return all precomputed terms as a dictionary
    return {
        'c1': c1,
        'c2': c2,
        'c3': c3,
    }


def prop_calculate_intermediate_haversine_value(user_precomputed, center_latitude, center_longitude):
    # Extract precomputed user terms
    c1 = user_precomputed['c1']
    c2 = user_precomputed['c2']
    c3 = user_precomputed['c3']

    # Compute haversine intermediate value
    a = 1 - c1 * math.sin(center_latitude) - c2 * math.cos(center_latitude) * math.cos(center_longitude) - c3 * math.cos(center_latitude) * math.sin(center_longitude)
    return a


def prop_evaluate_geofence_encrypted(encrypted_result, radius, earth_radius, private_key):
    haversine_intermediate = private_key.decrypt(encrypted_result)

    distance = 2 * earth_radius * math.asin(math.sqrt(haversine_intermediate / 2))
    # print(f"Distance from geofence centre: {round(distance, 2)} meters")

    # Return 1 if distance is within the radius, else 0
    return 1 if distance <= radius else 0

# End of Proposed encrypted haversine system


def security_overhead_exeperiment(user_latitude, user_longitude, center_latitude, center_longitude, radius, earth_radius, public_key, private_key, num_repitions_mean):

    tableResults = []
    encryption_counts = [10, 50, 100]

    # Run different test cases
    for num_encryptions in encryption_counts:

        # Output files with temporary data
        files = ["Outputs/securityRunOutRef.txt", "Outputs/securityRunOutProp.txt", "Outputs/securityOverOutRef.txt", "Outputs/securityOverOutProp.txt"]

        # Clear output files of temporary data
        for file_name in files:
            with open(file_name, 'w'):
                pass

        runtimes = []
        for j in range(10000):  # Repeat baseline for average runtime, as rapid execution may yield a result of 0 seconds
            start = time.time()
            for i in range(num_encryptions):
                # Check if inside geofence
                evaluate_geofence(user_latitude, user_longitude, center_latitude, center_longitude, radius, earth_radius)

            end = time.time()
            runtime = (end-start)
            runtimes.append(runtime)

        average_runtime = sum(runtimes) / len(runtimes) # Average runtime for haversine formula (baseline)

        # Repeat for average
        for i in range(num_repitions_mean):
            start_encrypted_system_ref = time.time()

            for i in range(num_encryptions):
                # Encrypt user terms
                user_precomputed_ref = ref_precompute_user_terms(user_latitude, user_longitude, public_key)

                # Calculate haversine intermediate value
                encrypted_result_ref = ref_calculate_intermediate_haversine_value(user_precomputed_ref, center_latitude, center_longitude)

                # Check if inside geofence
                ref_evaluate_geofence_encrypted(encrypted_result_ref, radius, earth_radius, private_key)

            end_encrypted_system_ref = time.time()

            runtime_encrypted_system_ref = (end_encrypted_system_ref - start_encrypted_system_ref)

            start_encrypted_system_prop = time.time()

            for i in range(num_encryptions):
                # Encrypt user terms
                user_precomputed_prop = prop_precompute_user_terms(user_latitude, user_longitude, public_key)

                # Calculate haversine intermediate value
                encrypted_result_prop = prop_calculate_intermediate_haversine_value(user_precomputed_prop, center_latitude, center_longitude)

                # Check if inside geofence
                prop_evaluate_geofence_encrypted(encrypted_result_prop, radius, earth_radius, private_key)
            
            end_encrypted_system_prop = time.time()

            runtime_encrypted_system_prop = (end_encrypted_system_prop - start_encrypted_system_prop)

            overhead = ((runtime_encrypted_system_ref - average_runtime) / average_runtime) * 100
            overhead_prop = ((runtime_encrypted_system_prop - average_runtime) / average_runtime) * 100

            # Write Total Runtime Reference to file
            with open("Outputs/securityRunOutRef.txt", "a") as f:
                f.write(f"{(runtime_encrypted_system_ref)}\n")

            # Write Total Runtime Proposed to file
            with open("Outputs/securityRunOutProp.txt", "a") as f:
                f.write(f"{(runtime_encrypted_system_prop)}\n")

            # Write Security Overhead Reference to file
            with open("Outputs/securityOverOutRef.txt", "a") as f:
                f.write(f"{(overhead)}\n")

            # Write Security Overhead Proposed to file
            with open("Outputs/securityOverOutProp.txt", "a") as f:
                f.write(f"{(overhead_prop)}\n")

        # Calculate staistics and present in table
        security_stats = stats.main(files)

        tableResults.append(
            [num_encryptions, f"{average_runtime:.3e}", "Runtime (s)", 
            f"{round(security_stats[0]['Mean'], 3)} ± {round(security_stats[0]['Standard Deviation'], 3)} (95% CI: {round(security_stats[0]['95% Confidence Interval'][0], 3)}, {round(security_stats[0]['95% Confidence Interval'][1], 3)})", 
            f"{round(security_stats[1]['Mean'], 3)} ± {round(security_stats[1]['Standard Deviation'], 3)} (95% CI: {round(security_stats[1]['95% Confidence Interval'][0], 3)}, {round(security_stats[1]['95% Confidence Interval'][1], 3)})"]
        )

        tableResults.append(            
            ["", "", "Overhead (%)", 
            f"{security_stats[2]['Mean']:.3e} ± {security_stats[2]['Standard Deviation']:.3e} (95% CI: {security_stats[2]['95% Confidence Interval'][0]:.3e}, {security_stats[2]['95% Confidence Interval'][1]:.3e})", 
            f"{security_stats[3]['Mean']:.3e} ± {security_stats[3]['Standard Deviation']:.3e} (95% CI: {security_stats[3]['95% Confidence Interval'][0]:.3e}, {security_stats[3]['95% Confidence Interval'][1]:.3e})"]
        )
    
    head = ["Enc.", "Baseline (s)", "Metric", "Ref. Alg.", "Prop. Alg."]
    save_results(tableResults, head, "Results/security_overhead.csv")

    print(f"Security overhead results saved to Results/security_overhead.csv\n")


def accuracy_experiment(center_latitude, center_longitude, radius, earth_radius, user_points, public_key, private_key):
    accuracy_results = []
    for user_latitude, user_longitude in user_points:
        # Establish ground truth
        ground_truth = "Inside" if evaluate_geofence(user_latitude, user_longitude, center_latitude, center_longitude, radius, earth_radius) else "Outside"

        # Reference encrypted system
        user_precomputed_ref = ref_precompute_user_terms(user_latitude, user_longitude, public_key)
        encrypted_result_ref = ref_calculate_intermediate_haversine_value(user_precomputed_ref, center_latitude, center_longitude)
        system_result_ref = "Inside" if ref_evaluate_geofence_encrypted(encrypted_result_ref, radius, earth_radius, private_key) else "Outside"

        # Proposed encrypted system
        user_precomputed_prop = prop_precompute_user_terms(user_latitude, user_longitude, public_key)
        encrypted_result_prop = prop_calculate_intermediate_haversine_value(user_precomputed_prop, center_latitude, center_longitude)
        system_result_prop = "Inside" if prop_evaluate_geofence_encrypted(encrypted_result_prop, radius, earth_radius, private_key) else "Outside"

        # Check if both systems are correctly identifying if a point is inside/outside
        final_result_ref = "Correct" if ground_truth == system_result_ref else "Incorrect"
        final_result_prop = "Correct" if ground_truth == system_result_prop else "Incorrect"

        accuracy_results.append((user_latitude, user_longitude, ground_truth, system_result_ref, final_result_ref, 
                                 system_result_prop, final_result_prop))

    head = ["Latitude", "Longitude", "Ground Truth", "Reference Result", "Reference Correct/Incorrect",
            "Proposed result", "Proposed Correct/Incorrect"]
    
    save_results(accuracy_results, head, "Results/accuracy.csv")

    print(f"Accuracy results saved to Results/accuracy.csv\n")
    
    correct_count_ref = sum(1 for test_point in accuracy_results if test_point[4] == "Correct")
    accuracy_ref = correct_count_ref / len(accuracy_results) * 100

    correct_count_prop = sum(1 for test_point in accuracy_results if test_point[6] == "Correct")
    accuracy_prop = correct_count_prop / len(accuracy_results) * 100

    print(f"Accuracy of Reference encrypted system: {accuracy_ref}")
    print(f"Accuracy of Proposed encrypted system: {accuracy_prop}")


def plot_geofence(center_latitude, center_longitude, radius, earth_radius, points_inside, points_outside, points_edge):
    plt.figure(figsize=(8, 8))

    points_geofence = []

    # Generate circular geofence points
    for theta in range(361):
        theta_rad = math.radians(theta)
        offset_lat = radius / earth_radius
        offset_lon = offset_lat / math.cos(center_latitude)
        lat = center_latitude + offset_lat * math.sin(theta_rad)
        lon = center_longitude + offset_lon * math.cos(theta_rad)
        points_geofence.append((lat, lon))

    # Plot circular geofence
    plt.plot(*zip(*[(math.degrees(lon), math.degrees(lat)) for lat, lon in points_geofence]), color="blue", label="Geofence Boundary")

    # Plot user points
    plt.scatter(*zip(*[(math.degrees(lon), math.degrees(lat)) for lat, lon in points_inside]), color="green", label="Inside Points")
    plt.scatter(*zip(*[(math.degrees(lon), math.degrees(lat)) for lat, lon in points_outside]), color="red", label="Outside Points")
    plt.scatter(*zip(*[(math.degrees(lon), math.degrees(lat)) for lat, lon in points_edge]), color="orange", label="Edge Points")

    # Add labels and legend
    plt.title("Geofence Visualisation")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend()
    plt.grid()
    plt.show()

def sanitise_geofence_center(center_latitude, center_longitude):
    # Convert to string to check the last decimal digit
    lon_str = f"{center_longitude:.{6}f}"
    lat_str = f"{center_latitude:.{6}f}"
    if lon_str[-1] == "0" and lat_str[-1] == "0":
    # Add a tiny offset to lat_rounded to make last digit a '1' 
        center_latitude += 10**-6  # 0.000001
        center_latitude = round(center_latitude, 6)  # Round again just in case

    return center_latitude, center_longitude


def save_results(table_data, headers, filename):
    df = pd.DataFrame(table_data, columns=headers)
    df.to_csv(filename, index=False, encoding="utf-8-sig")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run experimental tests on geofencing system"
    )

    parser.add_argument(
        "-m", "--mode",
        choices=["security", "accuracy"],
        default="accuracy",
        help="Run mode: security overhead, accuracy"
    )

    parser.add_argument(
        "-r", "--repetitions",
        type=int,
        default=30,
        help="Number of repetitions for security overhead experiment to calculate mean"
    )

    return parser.parse_args()


def main():

    args = parse_arguments()

    # Parameters
    public_key, private_key = initialize_keys()
    radius = 1000           # radius in meters
    earth_radius = 6371000  # Earth's radius in meters

    # User's location in radians
    user_latitude, user_longitude = math.radians(round(51.573037, 5)), math.radians(round(-9.724087, 5))

    # Sanitise geofence centre to prevent math domain errors
    center_latitude, center_longitude = sanitise_geofence_center(
        round(51.651050, 6), round(-9.910680, 6)
    )
    # Geofence center in radians
    center_latitude, center_longitude = math.radians(center_latitude), math.radians(center_longitude)

    # Generate user points inside, outside and on edge of the geofence
    points_inside, points_outside, points_edge = generate_user_points(center_latitude, center_longitude, radius, earth_radius)
    user_points = points_inside + points_outside + points_edge + [((math.radians(round(51.651050, 5)), math.radians(round(-9.910680, 5))))] # Last point to test sanatising works

    # Handle selected mode
    if args.mode == "security":
        # Quantify the additional runtime overhead introduced by encryption
        security_overhead_exeperiment(user_latitude, user_longitude, center_latitude, center_longitude, radius, earth_radius, public_key, private_key, num_repitions_mean=args.repitions)

    elif args.mode == "accuracy":
        # Evaluate the correctness of the geofencing system in determining whether a point is inside or outside the geofence
        accuracy_experiment(center_latitude, center_longitude, radius, earth_radius, user_points, public_key, private_key)
        # Plot points for visualisation
        # plot_geofence(center_latitude, center_longitude, radius, earth_radius, points_inside, points_outside, points_edge)



if __name__ == "__main__":
    main()