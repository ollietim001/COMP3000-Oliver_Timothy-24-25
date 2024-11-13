from phe import paillier
import math

def initialize_keys():
    public_key, private_key = paillier.generate_paillier_keypair()
    return public_key, private_key

def calculate_intermediate_haversine_value(user_latitude, user_longitude, public_key, center_latitude, center_longitude):
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

def evaluate_geofence(encrypted_result, radius, earth_radius, private_key):
    # Computed at the key authority
    haversine_intermediate = private_key.decrypt(encrypted_result)

    central_angle = 2 * math.atan2(math.sqrt(haversine_intermediate), math.sqrt(1 - haversine_intermediate))

    distance = earth_radius * central_angle 
    print(f"Distance from geofence boundry: {round(distance, 2)} meters")

    # Return 1 if distance is within the radius, else 0
    return 1 if distance <= radius else 0


public_key, private_key = initialize_keys()

radius = 100            # radius in meters
earth_radius = 6371000  # Earth's radius in meters

# User's location in radians
user_latitude, user_longitude = math.radians(50.7333), math.radians(-3.4800061)
# Geofence center in radians
center_latitude, center_longitude = math.radians(50.7333), math.radians(-3.4800)

# Calculate haversine intermediate value
encrypted_result = calculate_intermediate_haversine_value(user_latitude, user_longitude, public_key, center_latitude, center_longitude)

# Check if inside geofence
inside_geofence = evaluate_geofence(encrypted_result, radius, earth_radius, private_key)
print("Inside geofence" if inside_geofence else "Outside geofence")
