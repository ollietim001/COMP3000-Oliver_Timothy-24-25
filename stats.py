import numpy as np
import scipy.stats as st

def compute_statistics(data):
    
    # Computes the Mean, Standard Deviation, and 95% Confidence Interval for a given dataset

    n = len(data)
    mean_value = np.mean(data)  # Mean
    std_dev = np.std(data, ddof=1)  # Sample standard deviation
    confidence_interval = st.t.interval(0.95, df=n-1, loc=mean_value, scale=std_dev/np.sqrt(n))  # 95% CI
    
    return {
        "Mean": round(mean_value, 3),
        "Standard Deviation": round(std_dev, 3),
        "95% Confidence Interval": (round(confidence_interval[0], 3), round(confidence_interval[1], 3))
    }

def main(files):
    allResults = []
    for file in files:
        data = np.loadtxt(file, dtype=float)
        
        results = compute_statistics(data)
        allResults.append(results)

    return allResults

if __name__ == "__main__":
    main()