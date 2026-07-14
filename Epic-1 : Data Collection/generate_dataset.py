import os
import pandas as pd
import numpy as np

def generate_flood_dataset(output_path, num_samples=5000, random_state=42):
    np.random.seed(random_state)
    
    # 1. Geographic Features
    # Low elevation regions are more prone to flooding
    elevation = np.random.uniform(5, 1200, num_samples) # in meters
    # High drainage density is related to faster runoff
    drainage_density = np.random.uniform(0.5, 5.0, num_samples) # km/km^2
    
    # 2. Historical features
    previous_flood_history = np.random.choice([0, 1], size=num_samples, p=[0.75, 0.25])
    
    # 3. Meteorological Features (varying by region type)
    # Annual Rainfall (mm)
    annual_rainfall = np.random.uniform(800, 4500, num_samples)
    # Seasonal breakdown (Monsoon represents the bulk)
    monsoon_rainfall = annual_rainfall * np.random.uniform(0.6, 0.75, num_samples)
    winter_rainfall = annual_rainfall * np.random.uniform(0.05, 0.15, num_samples)
    summer_rainfall = annual_rainfall - (monsoon_rainfall + winter_rainfall)
    
    # Other atmospheric variables
    temperature = np.random.uniform(18, 42, num_samples) # °C
    # High rainfall correlates with high humidity
    humidity = np.clip(np.random.normal(70, 15, num_samples) + (monsoon_rainfall / 100), 30, 100) # %
    cloud_cover = np.clip(np.random.uniform(1, 10, num_samples) * (humidity / 70), 0, 10) # 0-10 octas
    cloud_visibility = np.clip(np.random.uniform(2, 15, num_samples) - (humidity / 30), 0.5, 15) # km
    wind_speed = np.random.uniform(5, 55, num_samples) # km/h
    pressure = np.random.uniform(980, 1025, num_samples) # hPa
    
    # 4. Soil and Water Variables (strongly correlated with rain and geography)
    soil_moisture = np.clip(np.random.uniform(10, 85, num_samples) + (monsoon_rainfall / 100) * 10 - (elevation / 100), 5, 95) # %
    river_water_level = np.clip(np.random.uniform(1, 4, num_samples) + (monsoon_rainfall / 500) * 2 - (elevation / 300), 0.5, 15) # m
    
    # 5. Flood target generation (using a logistic relation)
    # Linear combination representing physical conditions leading to flood
    z = (
        (monsoon_rainfall / 3000.0) * 4.5 +
        (river_water_level / 8.0) * 5.0 +
        (soil_moisture / 80.0) * 3.0 +
        (humidity / 80.0) * 1.5 +
        previous_flood_history * 2.0 +
        (annual_rainfall / 4000.0) * 1.5 +
        (drainage_density / 3.0) * 1.0 -
        (elevation / 500.0) * 2.5 - 7.5  # Bias term
    )
    
    # Probability using sigmoid
    probability = 1 / (1 + np.exp(-z))
    
    # Target variable (0 = No Flood, 1 = Flood)
    # Add a tiny bit of random noise to make accuracy around 96%
    flood_occurrence = (probability > 0.5).astype(int)
    
    # Tweak slightly with random noise to simulate real-world noise (target accuracy limit)
    noise_mask = np.random.rand(num_samples) < 0.035
    flood_occurrence[noise_mask] = 1 - flood_occurrence[noise_mask] # Flip 3.5% of labels
    
    # Construct DataFrame
    df = pd.DataFrame({
        'Annual_Rainfall': annual_rainfall,
        'Monsoon_Rainfall': monsoon_rainfall,
        'Winter_Rainfall': winter_rainfall,
        'Summer_Rainfall': summer_rainfall,
        'Cloud_Cover': cloud_cover,
        'Cloud_Visibility': cloud_visibility,
        'Relative_Humidity': humidity,
        'Temperature': temperature,
        'River_Water_Level': river_water_level,
        'Wind_Speed': wind_speed,
        'Atmospheric_Pressure': pressure,
        'Soil_Moisture': soil_moisture,
        'Drainage_Density': drainage_density,
        'Elevation': elevation,
        'Previous_Flood_History': previous_flood_history,
        'Flood': flood_occurrence
    })
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Dataset generated at: {output_path}")
    print(f"Shape: {df.shape}")
    print(f"Flood occurrence distribution:\n{df['Flood'].value_counts(normalize=True)}")

if __name__ == '__main__':
    generate_flood_dataset('E:/sb project/dataset/sample_flood_data.csv')
