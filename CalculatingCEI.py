# -*- coding: utf-8 -*-
"""
Created on Wed Aug 27 09:05:36 2025

@author: Decheng Zhou(Hainan University)
"""


import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.decomposition import PCA
import os

# Constants configuration
INVALID_VALUES = [-9999, 65535]  # Invalid value markers
INPUT_FILE = "CEI_input.csv"
OUTPUT_FILE = "CEI_output.csv"

def process_data():
    """Main function to process CEI calculation"""
    try:
        # Check if input file exists
        if not os.path.exists(INPUT_FILE):
            print(f"Error: Input file '{INPUT_FILE}' not found")
            return False
        
        # Load and validate data
        df = pd.read_csv(INPUT_FILE)
        if df.empty or df.shape[1] < 14:
            print("Error: Empty dataset or insufficient columns")
            return False
        
        # Extract data columns
        point_id = df.iloc[:, 0].values.reshape(-1, 1)    # Column 1: pointID
        X = df.iloc[:, 1:13].values                       # Columns 2-14: Environmental factors
        
        # Remove records containing invalid values
        valid_mask = ~np.isin(X, INVALID_VALUES).any(axis=1)
        if not np.any(valid_mask):
            print("Error: No valid records after filtering")
            return False
            
        X_clean = X[valid_mask]
        point_id_clean = point_id[valid_mask]
        removed_count = len(X) - len(X_clean)
        
        print(f"Removed {removed_count} invalid records")
        print(f"Remaining {len(X_clean)} valid records")
        
        # Data standardization using RobustScaler (robust to outliers)
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X_clean)
        
        # Validate standardization results
        mean_deviation = np.abs(X_scaled.mean()).max()
        std_deviation = np.abs(X_scaled.std() - 1).max()
        if mean_deviation > 1e-3 or std_deviation > 1e-3:
            print(f"Warning: Standardization deviation detected - Mean: {mean_deviation:.4f}, STD: {std_deviation:.4f}")
        
        # PCA analysis (retaining 85% variance)
        pca = PCA(n_components=0.85, svd_solver='full')
        pca.fit(X_scaled)
        
        # Weight normalization (ensuring sum=1)
        weights = pca.explained_variance_ratio_
        weights /= weights.sum()
        
        # Calculate composite index
        principal_components = pca.transform(X_scaled)
        cindex = np.sum(principal_components * weights.reshape(1, -1), axis=1)
        
        # Normalize Cindex to 0-1 range
        cindex_min = cindex.min()
        cindex_max = cindex.max()
        if cindex_max != cindex_min:  # Avoid division by zero
            cindex_normalized = (cindex - cindex_min) / (cindex_max - cindex_min)
        else:
            cindex_normalized = np.zeros_like(cindex)  # Set to 0 if all values are identical
        
        # Validate normalization results
        if np.any(cindex_normalized < 0) or np.any(cindex_normalized > 1):
            print(f"Warning: Normalization anomaly detected [{cindex_normalized.min():.4f}, {cindex_normalized.max():.4f}]")
            cindex_normalized = np.clip(cindex_normalized, 0, 1)  # Force clipping to [0,1]
        
        # Save results with normalized Cindex
        result_df = pd.DataFrame({
            'pointID': point_id_clean.flatten(),
            'CEI': cindex_normalized,
        })
        
        result_df.to_csv(OUTPUT_FILE, index=False)
        
        # Print PCA information
        print(f"PCA components retained: {len(weights)}")
        print(f"Explained variance ratio: {pca.explained_variance_ratio_.sum():.4f}")
        print(f"CEI range: [{cindex_normalized.min():.4f}, {cindex_normalized.max():.4f}]")
        print(f"Results successfully saved to '{OUTPUT_FILE}'")
        
        return True
        
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== CEI Calculation Process ===")
    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print("Processing data...")
    
    success = process_data()
    
    if success:
        print("Process completed successfully")
    else:
        print("Process failed")