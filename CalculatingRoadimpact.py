# -*- coding: utf-8 -*-
"""
Created on Wed Aug 27 09:05:36 2025

@author: Decheng Zhou(Hainan University)
"""

import os
import pandas as pd
import numpy as np

# Constants definition
THRESHOLD_DISTANCE = 50000  # 50km distance threshold
TOP_PERCENTILE = 0.2        # Top 20% records
MIN_REF_POINTS = 3          # Minimum reference points required
IDW_POWER = 2.0             # Inverse distance weighting power
INVALID_VALUES = [-9999, np.nan, None]

# File paths
PCA_FILE = "CEI_output.csv"
INDICATORS_FILE = "ForestMetrics_input.csv"
OUTPUT_FILE = "ForestMetrics_output.csv"
SKIPPED_FILE = "Skipped_Records.csv"

def euclidean_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two coordinates (in meters)"""
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def is_valid_value(value):
    """Check if value is valid"""
    return value not in INVALID_VALUES and not pd.isna(value)

def inverse_distance_weighting(values, distances, power=IDW_POWER):
    """
    Calculate inverse distance weighted average
    :param values: Array of values to be weighted
    :param distances: Corresponding distance array
    :param power: Distance decay exponent
    :return: Weighted average value
    """
    values = np.array(values)
    distances = np.array(distances)
    
    valid_mask = [is_valid_value(v) for v in values]
    valid_values = values[valid_mask]
    valid_distances = distances[valid_mask]
    
    if len(valid_values) == 0:
        return np.nan
    
    with np.errstate(divide='ignore', invalid='ignore'):
        weights = 1.0 / (valid_distances ** power)
        weights[np.isinf(weights)] = 0
        total_weight = np.sum(weights)
        
        if total_weight > 0:
            return np.sum(valid_values * weights) / total_weight
        return np.mean(valid_values)

def calculate_temporal_trends(row, target_vars):
    """Calculate temporal trends between 2000 and 2020 based on AC results"""
    trends = {}
    for var in target_vars:
        # Extract base variable name (remove year suffix)
        base_var = var[:-4] if var.endswith('2000') or var.endswith('2020') else var
        var2000 = f"{base_var}2000_AC"
        var2020 = f"{base_var}2020_AC"
        
        # Absolute change trend (difference between AC results)
        if is_valid_value(row[var2020]) and is_valid_value(row[var2000]):
            trends[f"{base_var}_AC_trend"] = row[var2020] - row[var2000]
            
            # Relative change trend (symmetric percentage)
            denominator = abs(row[var2000]) + abs(row[var2020])
            if denominator > 0:
                trends[f"{base_var}_RC_trend"] = ((row[var2020] - row[var2000]) / denominator) * 100
            else:
                trends[f"{base_var}_RC_trend"] = np.nan
        else:
            trends[f"{base_var}_AC_trend"] = np.nan
            trends[f"{base_var}_RC_trend"] = np.nan
    
    return trends

def process_forest_metrics():
    """Main function to process forest metrics data"""
    try:
        # Check if input files exist
        if not os.path.exists(PCA_FILE):
            print(f"Error: PCA file '{PCA_FILE}' not found")
            return False
        if not os.path.exists(INDICATORS_FILE):
            print(f"Error: Indicators file '{INDICATORS_FILE}' not found")
            return False
        
        # Load data
        pca_df = pd.read_csv(PCA_FILE)
        indicators_df = pd.read_csv(INDICATORS_FILE)
        
        # Merge data on pointID
        merged_df = pd.merge(pca_df, indicators_df, on='pointID')
        
        # Create two subtables
        table1 = merged_df[(merged_df['Windowflag'] == 1) & (merged_df['Buffer_type'] > 1)].copy()
        table2 = merged_df[(merged_df['Buffer_type'] <= 1) & 
                         (merged_df['NTL2000'] < 1) & 
                         (merged_df['NTL2020'] < 1) & 
                         (abs(merged_df['ForestChange']) < 10) & 
                         (abs(merged_df['Plantations']) < 10)].copy()
        
        if table1.empty or table2.empty:
            print("Warning: One or both subtables are empty")
            return False
        
        # Initialize result containers
        result_rows = []
        skipped_rows = []
        target_columns = ["Area2000", "Area2020", "H2000", "H2020", "PD2000", "PD2020", 
                         "NPP2000", "NPP2020"]
        trend_vars = ["Area", "H", "PD", "NPP"]  # Variables for temporal trends
        
        # Precompute table2 coordinates and Cindex for faster processing
        table2_coords = table2[['X', 'Y']].values
        table2_cindex = table2['CEI'].values
        
        # Process each record in table1
        for _, row in table1.iterrows():
            # Vectorized distance calculation
            distances = np.sqrt(
                (table2_coords[:, 0] - row['X'])**2 + 
                (table2_coords[:, 1] - row['Y'])**2
            )
            cindex_diffs = np.abs(table2_cindex - row['CEI'])
            
            # Filter records within distance threshold
            valid_mask = distances < THRESHOLD_DISTANCE
            filtered_distances = distances[valid_mask]
            filtered_cindex_diffs = cindex_diffs[valid_mask]
            filtered_table2 = table2.iloc[np.where(valid_mask)[0]].copy()
            
            if len(filtered_table2) < MIN_REF_POINTS:
                skipped_rows.append({
                    'pointID': row['pointID'],
                    'Reason': "Not enough reference points"
                })
                continue
            
            # Sort by Cindex difference and select top similar records
            sorted_indices = np.argsort(filtered_cindex_diffs)
            n_top = max(MIN_REF_POINTS, int(len(filtered_table2) * TOP_PERCENTILE))
            top_indices = sorted_indices[:n_top]
            top_records = filtered_table2.iloc[top_indices]
            top_distances = filtered_distances[top_indices]
            
            # Calculate background Cindex (IDW weighted)
            bg_cindex = inverse_distance_weighting(
                top_records['CEI'].values,
                top_distances
            )
            
            # Calculate Cindex difference
            cindex_diff = row['CEI'] - bg_cindex if not pd.isna(bg_cindex) else np.nan
            
            # Build result row
            result_row = {
                'pointID': row['pointID'],
                'X': row['X'],
                'Y': row['Y'],
                'Buffer_type': row['Buffer_type'],
                'CEI_Diff': cindex_diff,
                'Nearest_Ref_Distance': filtered_distances.min(),
                'Ref_Points_Used': len(top_records)
            }
            
            # Calculate background means and differences for all target variables
            for col in target_columns:
                bg_mean = inverse_distance_weighting(
                    top_records[col].values,
                    top_distances
                )
                
                result_row[f'{col}_road'] = row[col]
                result_row[f'{col}_ref'] = bg_mean
                
                # Calculate absolute and relative changes
                if is_valid_value(row[col]) and is_valid_value(bg_mean):
                    result_row[f'{col}_AC'] = row[col] - bg_mean
                    denominator = abs(bg_mean) + abs(row[col])
                    if denominator != 0:
                        result_row[f'{col}_RC'] = ((row[col] - bg_mean) / denominator) * 100
                    else:
                        result_row[f'{col}_RC'] = np.nan
                else:
                    result_row[f'{col}_AC'] = np.nan
                    result_row[f'{col}_RC'] = np.nan
            
            # Calculate temporal trends (2000 vs 2020) based on AC results
            temporal_trends = calculate_temporal_trends(result_row, trend_vars)
            result_row.update(temporal_trends)
            
            result_rows.append(result_row)
        
        # Save results if any were processed
        if result_rows:
            result_df = pd.DataFrame(result_rows)
            # Define column order for output
            column_order = ['pointID', 'X', 'Y', 'Buffer_type']
            
            # Add target variable columns
            for col in target_columns:
                column_order.extend([
                    f'{col}_road', f'{col}_ref', 
                    f'{col}_AC', f'{col}_RC'
                ])
            
            # Add temporal trend columns (after all variable columns)
            for var in trend_vars:
                column_order.extend([
                    f'{var}_AC_trend', 
                    f'{var}_RC_trend'
                ])
            
            # Add final columns
            column_order.extend([
                'CEI_Diff', 'Nearest_Ref_Distance', 'Ref_Points_Used'
            ])
            
            result_df = result_df[column_order]
            result_df.to_csv(OUTPUT_FILE, index=False, float_format='%.4f')
            print(f"Successfully saved results to {OUTPUT_FILE}")
        
        # Save skipped records if any
        if skipped_rows:
            pd.DataFrame(skipped_rows).to_csv(SKIPPED_FILE, index=False)
            print(f"Skipped records saved to {SKIPPED_FILE}")
        
        return True
        
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        return False

if __name__ == "__main__":
    # Memory optimization settings
    pd.set_option('mode.chained_assignment', None)
    np.seterr(all='ignore')
    
    print("Starting forest metrics processing...")
    if process_forest_metrics():
        print("Processing completed successfully")
    else:
        print("Processing failed")