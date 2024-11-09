from flask import Flask, jsonify, request
from phe import paillier
import math


app = Flask(__name__)

# Generate Paillier public and private keys
public_key, private_key = paillier.generate_paillier_keypair()

@app.route("/get-public-key", methods=['GET'])
def get_public_key():
    public_key_data = {
        "n": public_key.n  # 'n' is the serialized representation of the Paillier public key
    }
    return jsonify(public_key_data)

@app.route("/submit-geofence-result", methods=['POST'])
def submit_geofence_result():
    # Retrieve JSON payload
    data = request.get_json()

    # Check if the encrypted data and public key are provided in the payload
    if not data or 'encrypted_result' not in data or 'public_key_n' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'encrypted_result' or 'public_key_n' in request data"
        }), 400

    # Verify the provided public key matches the server's public key
    if data['public_key_n'] != public_key.n:
        return jsonify({
            "status": "error",
            "message": "Public key mismatch. Encryption was not done with the correct public key."
        }), 400

    try: 
        ciphertext_value, exponent = data['encrypted_result']                                # Parse the encrypted Paillier result
        encrypted_result = paillier.EncryptedNumber(public_key, ciphertext_value, exponent)  # Reconstruct the EncryptedNumber object
        decrypted_result = private_key.decrypt(encrypted_result)                             # Decrypt the result using the private key

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Decryption failed",
        }), 500

    # Determine if Mobile Node is inside or outside the geofence based on result
    result = evaluate_geofence_result(decrypted_result)
    if result == 1:
        print("Mobile Node is inside the geofence.")
    elif result == 0:
        print("Mobile Node is outside the geofence.")
    else:
        print("Evaluation failed.")
        return jsonify({
            "status": "error",
            "message": "Evaluation failed. Unable to determine geofence status."
        }), 500

    # Return a success response
    return jsonify({
        "status": "success",
        "message": "Geofence result processed successfully"
    }), 200


def evaluate_geofence_result(decrypted_result):
    b = 1000      # Scaling factor since Paillier encryption does not support floating points
    r = 200       # Geofence radius in meters
    R = 6371000   # Approximate Earth radius in meters

    try:
        # Step 1: Scale the decrypted result
        a = decrypted_result / b

        # Step 2: Calculate the distance 'd'
        d = 2 * R * math.asin(math.sqrt(1 - a / 2))

        # Step 3: Return 1 if 'd' is within the radius 'r', else 0
        return 1 if d <= r else 0

    except Exception as e:
        print(f"Unexpected error in evaluate_geofence_result: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)