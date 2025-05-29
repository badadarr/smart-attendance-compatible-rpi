import pickle
import numpy as np
import os

# Cek file data
print("Checking data files:")
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
print(f"Data directory: {data_dir}")
print(f"Files in data directory: {os.listdir(data_dir)}")

faces_file = os.path.join(data_dir, "faces_data.pkl")
names_file = os.path.join(data_dir, "names.pkl")

print(f"Faces file exists: {os.path.exists(faces_file)}")
print(f"Names file exists: {os.path.exists(names_file)}")
print(f"Faces file size: {os.path.getsize(faces_file)} bytes")
print(f"Names file size: {os.path.getsize(names_file)} bytes")

# Load data
try:
    with open(faces_file, "rb") as f:
        faces = pickle.load(f)

    with open(names_file, "rb") as f:
        names = pickle.load(f)

    print("\nData Analysis:")
    print(f"Faces data type: {type(faces)}")
    print(f"Faces shape: {faces.shape}")
    print(f"Number of samples: {faces.shape[0]}")
    print(f"Features per sample: {faces.shape[1]}")
    print(
        f"Expected image size: ~{int(np.sqrt(faces.shape[1]))}x{int(np.sqrt(faces.shape[1]))}"
    )
    print(f"Names count: {len(names)}")
    print(f"Unique names: {set(names)}")
    print(f"Names sample: {names[:5]}")
except Exception as e:
    print(f"Error loading data: {e}")
