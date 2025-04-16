from fitparse import FitFile
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

def get_hr_zone(hr):
    """Convert heart rate to training zone"""
    if hr < 123:
        return 1
    elif hr < 153:
        return 2
    elif hr < 169:
        return 3
    elif hr < 184:
        return 4
    else:
        return 5

def get_power_zone(power):
    """Convert power to training zone"""
    if power < 201:
        return 0  # Below Z1
    elif power < 247:
        return 1
    elif power < 278:
        return 2
    elif power < 309:
        return 3
    elif power < 355:
        return 4
    elif power <= 402:
        return 5
    else:
        return 6  # Above Z5

def analyze_hr_data(fit_file_path, run_type="easy"):
    """Analyze heart rate data from FIT file for anomalies."""
    
    fitfile = FitFile(fit_file_path)
    
    records = []
    for record in fitfile.get_messages('record'):
        data = {}
        for field in record:
            data[field.name] = field.value
        records.append(data)
    
    df = pd.DataFrame(records)
    
    # Add zone classifications
    df['hr_zone'] = df['heart_rate'].apply(get_hr_zone)
    df['power_zone'] = df['power'].apply(get_power_zone)
    
    # Calculate zone mismatches
    df['zone_mismatch'] = abs(df['hr_zone'] - df['power_zone'])
    
    # Basic statistics
    hr_stats = {
        'min': df['heart_rate'].min(),
        'max': df['heart_rate'].max(),
        'mean': df['heart_rate'].mean(),
        'std': df['heart_rate'].std(),
        'median': df['heart_rate'].median()
    }
    
    power_stats = {
        'min': df['power'].min(),
        'max': df['power'].max(),
        'mean': df['power'].mean(),
        'std': df['power'].std(),
        'median': df['power'].median()
    }
    
    # Zone distribution analysis
    hr_zone_dist = df['hr_zone'].value_counts().sort_index()
    power_zone_dist = df['power_zone'].value_counts().sort_index()
    
    # Identify potential anomalies
    df['hr_change'] = df['heart_rate'].diff()
    
    anomalies = {
        'missing_values': df['heart_rate'].isnull().sum(),
        'zero_values': (df['heart_rate'] == 0).sum(),
        'physiological_impossible': (df['heart_rate'] > 220).sum(),
        'sudden_changes': (abs(df['hr_change']) > 20).sum(),
        'zone_mismatches': (df['zone_mismatch'] >= 2).sum()  # Count when HR and Power zones differ by 2 or more
    }
    
    # Zone correlation analysis
    zone_correlation = pd.crosstab(df['hr_zone'], df['power_zone'])
    
    # Time analysis
    total_time = len(df)  # assuming 1-second intervals
    time_in_zones = {
        'hr_zones': {f"Z{i}": (df['hr_zone'] == i).sum() / total_time * 100 for i in range(1, 6)},
        'power_zones': {f"Z{i}": (df['power_zone'] == i).sum() / total_time * 100 for i in range(1, 6)}
    }
    
    # Create visualizations
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Heart Rate and Power Zones Over Time
    plt.subplot(2, 1, 1)
    plt.plot(df['heart_rate'], label='Heart Rate', alpha=0.7)
    plt.plot(df['power'], label='Power', alpha=0.7)
    plt.axhline(y=123, color='g', linestyle='--', label='Z1/Z2 HR')
    plt.axhline(y=153, color='y', linestyle='--', label='Z2/Z3 HR')
    plt.axhline(y=169, color='orange', linestyle='--', label='Z3/Z4 HR')
    plt.axhline(y=184, color='r', linestyle='--', label='Z4/Z5 HR')
    plt.title('Heart Rate and Power Over Time')
    plt.legend()
    
    # Plot 2: Zone Mismatch Analysis
    plt.subplot(2, 1, 2)
    plt.hist(df['zone_mismatch'], bins=range(7), alpha=0.7)
    plt.title('Distribution of Zone Mismatches')
    plt.xlabel('Zone Difference (HR Zone - Power Zone)')
    plt.ylabel('Count')
    
    plt.tight_layout()
    plt.savefig('hr_power_analysis.png')
    
    return {
        'hr_stats': hr_stats,
        'power_stats': power_stats,
        'anomalies': anomalies,
        'time_in_zones': time_in_zones,
        'zone_correlation': zone_correlation,
        'raw_data': df
    }

def print_available_fields(fit_file_path):
    """Print all available fields in the FIT file"""
    fitfile = FitFile(fit_file_path)
    
    # Get the first record to see available fields
    for record in fitfile.get_messages('record'):
        print("\nAvailable fields in the FIT file:")
        for field in record:
            print(f"- {field.name}: {field.value} ({type(field.value)})")
        break

# First, let's see what fields we have
print_available_fields('18643172789_ACTIVITY.fit')

# Run analysis
results = analyze_hr_data('18643172789_ACTIVITY.fit')

# Print analysis results
print("\nHeart Rate Statistics:")
for key, value in results['hr_stats'].items():
    print(f"{key}: {value:.1f}")

print("\nPower Statistics:")
for key, value in results['power_stats'].items():
    print(f"{key}: {value:.1f}")

print("\nPotential Anomalies:")
for key, value in results['anomalies'].items():
    print(f"{key}: {value}")

print("\nTime in Heart Rate Zones (%):")
for zone, percentage in results['time_in_zones']['hr_zones'].items():
    print(f"{zone}: {percentage:.1f}%")

print("\nTime in Power Zones (%):")
for zone, percentage in results['time_in_zones']['power_zones'].items():
    print(f"{zone}: {percentage:.1f}%")

print("\nZone Correlation Matrix:")
print(results['zone_correlation'])

# Save detailed data for review
results['raw_data'][['timestamp', 'heart_rate', 'power', 'hr_zone', 'power_zone', 'zone_mismatch']].to_csv('hr_power_analysis.csv', index=False)