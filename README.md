# PrivGeo: Privacy-Preserving Geofencing using Paillier Encryption

## 🔒 License

This repository is shared publicly for academic review and transparency only.

🚫 **No license has been granted. All rights reserved.**  
Please do not reuse, modify, or publish any part of this code until the associated paper is formally published.

If you are interested in using this work or collaborating, feel free to contact me.

---

## Project Owner
**Oliver Timothy**

## Supervisor
**Dr Hai-Van Dang**

## Project Vision

PrivGeo is a privacy-preserving geofencing system designed for patient tracking applications, such as monitoring individuals with Alzheimer’s disease. It enables carers to define precise circular geofences while keeping patient locations confidential. Leveraging the Paillier encryption scheme, PrivGeo provides near real-time geofencing without exposing sensitive location data. This makes it especially suitable for healthcare applications that require continuous monitoring while maintaining trust and confidentiality, encouraging broader adoption of location-based services in privacy-sensitive environments.

---

## 🚀 Getting Started

### 📦 Prerequisites

- [Docker](https://www.docker.com/)
- [Visual Studio Code](https://code.visualstudio.com/)

### 🛠️ Installation & Setup

1. **Initialize Files:**

   Open a Git Bash terminal in the project folder and run:
   ```bash
   ./initFiles.sh
   ```
2. **Configure Worker Count (Optional but Recommended):**

   The Docker containers use `gunicorn` with 4 workers (`-w 4` by default).

   - On a 6-core host, this results in a **1.33 worker-to-core ratio** across two containers (8 workers / 6 cores).
   - You can adjust this by modifying the `command` field in the `docker-compose.yml` file.

   **Example:**
   ```yaml
   services:
     geofencing:
       ...
       command: gunicorn -w 4 --timeout 120 --preload -b 0.0.0.0:5001 app:app

     carer:
       ...
       command: gunicorn -w 4 --timeout 120 --preload -b 0.0.0.0:5002 app:app
   ```

   To reduce CPU load, try lowering `-w 4` to `-w 2` (or based on your system’s available cores).

   > ⚠️ **Tip:**  
   > If you encounter `worker timeout` errors during **runtime** or **scalability** tests (check Docker logs), reduce the number of workers to avoid CPU contention.

3. **Start Docker Environment:**

   - Open Docker and ensure it's running.
   - Open the project folder in **Visual Studio Code**.
   - In the terminal, run:
     ```bash
     docker-compose up -d --build
     ```

   - Wait for it to fetch all geofences. ✅ Check the Docker container logs to confirm:
     ```text
     geofencing-1  | Number of processed geofence coordinates: 500
     geofencing-1  | Geofence coordinates fetched successfully.
     ```
    > ❗ **Troubleshooting – Geofence Fetch Errors:**  
    > If you encounter errors during geofence fetching:
    >
    > 1. **First**, check [https://overpass-turbo.eu/s/20Pa](https://overpass-turbo.eu/s/20Pa) to ensure the Overpass API is online and able to process the query.
    >
    > 2. **If the site is up and running**, try reducing the query limit in the geofencing microservice:
    >
    >    - Open `app.py` inside the Geofencing-Microservice folder.
    >    - Locate the Overpass query line that includes:
    >      ```python
    >      out qt 1000;
    >      ```
    >    - Change it to 500:
    >      ```python
    >      out qt 500;
    >      ```
    >
    >    ⚠️ **Important:**  
    >    - Do **not** reduce this below:
    >      ```python
    >      numGeofenceBoundaries = 500
    >      ```
    >    - And make sure `numGeofenceBoundaries` is **not less than** the values used in test cases like:
    >      ```python
    >      geofence_counts = [1, 10, 100, 200, 300]  # found in User-Device.py
    >      ```
    >    - Otherwise, runtime tests may fail or behave unpredictably.
    >    - ✅ You can confirm this in the Docker logs:
    >    ```text
    >    geofencing-1  | Number of processed geofence coordinates: 500
    >    ```
    >    - Ensure this number (fetched geofences) is **greater than or equal to** the largest test count (e.g., 300 in `geofence_counts`).


4. **Run the System:**

   - Open `User-Device.py`
   - Ensure all experiment code in the `main` block is **commented out**
   - Then run the script.

---

## 🧪 Running Tests

Tests should be run individually, depending on what you want to evaluate:

- **Runtime & Scalability:**  
  Run from the `main` block in `User-Device.py`

- **Accuracy & Security Overhead:**  
  Run from the `main` block in `CircularGeofencing.py`

> ⚠️ **Note:**  
> All tests (except the accuracy test) may take several hours to complete due to a default repetition count of **30**.  
> You can reduce this number within the scripts if you're constrained by time or running exploratory tests.
>
> For example, in `User-Device.py`, the runtime experiment is called as:
> ```python
> runtime_experiment(user_latitude, user_longitude, public_key, num_repitions_mean=30)
> ```
> You can lower `num_repitions_mean` (e.g., to 5 or 10) to speed up test runs.
---