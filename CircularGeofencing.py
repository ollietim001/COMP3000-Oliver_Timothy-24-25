from phe import paillier
import math
import time
import random
import matplotlib.pyplot as plt
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


def precompute_user_terms(user_latitude, user_longitude, public_key):
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


def calculate_intermediate_haversine_value(user_precomputed, center_latitude, center_longitude):
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


def evaluate_geofence_encrypted(encrypted_result, radius, earth_radius, private_key):
    haversine_intermediate = private_key.decrypt(encrypted_result)

    central_angle = 2 * math.atan2(math.sqrt(haversine_intermediate), math.sqrt(1 - haversine_intermediate))

    distance = earth_radius * central_angle 
    # print(f"Distance from geofence centre: {round(distance, 2)} meters")

    # Return 1 if distance is within the radius, else 0
    return 1 if distance <= radius else 0


def security_overhead_exeperiment(user_latitude, user_longitude, center_latitude, center_longitude, radius, earth_radius, public_key, private_key):
    geofence_counts = [10, 100, 1000]
    runtime_results = []
    
    for num_geofences in geofence_counts:
        runtimes = []
        for j in range(10000):  # Repeat for average runtime, as rapid execution may yield a result of 0 seconds
            start = time.time()
            for i in range(num_geofences):
                # Check if inside geofence
                evaluate_geofence(user_latitude, user_longitude, center_latitude, center_longitude, radius, earth_radius)

            end = time.time()
            runtime = (end-start)
            runtimes.append(runtime)

        average_runtime = sum(runtimes) / len(runtimes)

        start_encrypted_system = time.time()
        # Precompute user terms
        user_precomputed = precompute_user_terms(user_latitude, user_longitude, public_key)

        for i in range(num_geofences):
            # Calculate haversine intermediate value
            encrypted_result = calculate_intermediate_haversine_value(user_precomputed, center_latitude, center_longitude)

            # Check if inside geofence
            evaluate_geofence_encrypted(encrypted_result, radius, earth_radius, private_key)

        end_encrypted_system = time.time()
        runtime_encrypted_system = (end_encrypted_system - start_encrypted_system)

        overhead = ((runtime_encrypted_system - average_runtime) / average_runtime) * 100
        runtime_results.append((num_geofences, average_runtime, runtime_encrypted_system, overhead))

    
    head = ["Number of Geofences", "Baseline Runtime (s)", "Encrypted Runtime (s)", "Overhead (%)"]
    print(tabulate(runtime_results, headers=head, tablefmt="grid"))

def accuracy_experiment(center_latitude, center_longitude, radius, earth_radius, user_points, public_key, private_key):
    accuracy_results = []
    for user_latitude, user_longitude in user_points:
        # Establish ground truth
        ground_truth = "Inside" if evaluate_geofence(user_latitude, user_longitude, center_latitude, center_longitude, radius, earth_radius) else "Outside"

        # Encrypted system
        user_precomputed = precompute_user_terms(user_latitude, user_longitude, public_key)
        encrypted_result = calculate_intermediate_haversine_value(user_precomputed, center_latitude, center_longitude)
        system_result = "Inside" if evaluate_geofence_encrypted(encrypted_result, radius, earth_radius, private_key) else "Outside"

        # Check if encrypted system is correctly identifying if a point is inside/outside
        final_result = "Correct" if ground_truth == system_result else "Incorrect"

        accuracy_results.append((user_latitude, user_longitude, ground_truth, system_result, final_result))

    head = ["Latitude", "Longitude", "Ground Truth (Inside/Outside)", "System Result (Inside/Outside)", "Correct/Incorrect"]
    print(tabulate(accuracy_results, headers=head, tablefmt="grid"))
    
    correct_count = sum(1 for test_point in accuracy_results if test_point[4] == "Correct")
    accuracy = correct_count / len(accuracy_results) * 100
    print(f"Accuracy of encrypted system: {accuracy}")


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


def main():
    # Parameters
    public_key, private_key = initialize_keys()
    radius = 1000           # radius in meters
    earth_radius = 6371000  # Earth's radius in meters

    # User's location in radians
    user_latitude, user_longitude = math.radians(round(50.7333, 5)), math.radians(round(-3.4800, 5))
    # Geofence center in radians
    center_latitude, center_longitude = math.radians(round(50.7333, 5)), math.radians(round(-3.4800, 5))

    # Quantify the additional runtime and resource overhead introduced by encryption 
    security_overhead_exeperiment(user_latitude, user_longitude, center_latitude, center_longitude, radius, earth_radius, public_key, private_key)

    # Generate user points inside, outside and on edge of the geofence
    points_inside, points_outside, points_edge = generate_user_points(center_latitude, center_longitude, radius, earth_radius)
    user_points = points_inside + points_outside + points_edge

    # Evaluate the correctness of the geofencing system in determining whether a point is inside or outside the geofence
    accuracy_experiment(center_latitude, center_longitude, radius, earth_radius, user_points, public_key, private_key)

    # Plot points for visualisation
    plot_geofence(center_latitude, center_longitude, radius, earth_radius, points_inside, points_outside, points_edge)



if __name__ == "__main__":
    main()