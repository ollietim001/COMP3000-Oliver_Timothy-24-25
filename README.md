# PrivGeo: Privacy-Preserving Geofencing using Paillier Encryption

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

   - Run `User-Device.py`

---

## 🧪 Running Experiments

Both `User-Device.py` and `CircularGeofencing.py` support command-line arguments for running different types of performance experiments.

### ⚙️ General Usage

```
python <script_name>.py --mode <experiment_type> [--repetitions N] [--geofence-count N]
```

- `--mode`: Type of experiment to run
- `--repetitions`: Number of times to repeat the experiment for averaging (default: `30`)
- `--geofence-count`: Only used in `basic` mode to set the number of geofences (default: `10`)

> ⚠️ **Note:**  
> Running with **fewer than 20 repetitions** may trigger:
>```
>RuntimeWarning: invalid value encountered in multiply
>```
>This occurs during confidence interval calculations due to insufficient data or zero variance. The script will still run, but results may be inaccurate. Recommended: Use ≥20 repetitions for reliable stats.

### Available Modes

| Script                  | Mode         | Description                                                                 |
|-------------------------|--------------|-----------------------------------------------------------------------------|
| `User-Device.py`        | `basic`      | No experiments — just sends encrypted location with given geofence count   |
| `User-Device.py`        | `runtime`    | Measures system runtime incl. communication   |
| `User-Device.py`        | `scalability`| Evaluates system scalability under varying concurrent request loads        |
| `CircularGeofencing.py` | `accuracy`   | Evaluates correctness of geofence classification (inside/outside detection)|
| `CircularGeofencing.py` | `security`   | Quantifies runtime overhead introduced by encryption                       |


### Example Commands

Run a basic encrypted location submission with 15 geofences:
```
python User-Device.py --mode basic --geofence-count 15
```

Run runtime performance test with fewer repetitions:
```
python User-Device.py --mode runtime --repetitions 5
```

Run the geofence accuracy test:
```
python CircularGeofencing.py --mode accuracy
```

> ⚠️ **Note:**  
> Experiments: can take several hours to complete due to a default repetition count of **30**. Lower `--repetitions` for faster exploratory runs.

---