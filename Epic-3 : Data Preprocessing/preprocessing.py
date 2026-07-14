import os
import joblib
import pandas as pd
import numpy as np

# Feature list order that the model was trained on
FEATURES_ORDER = [
    'Annual_Rainfall', 'Monsoon_Rainfall', 'Winter_Rainfall', 'Summer_Rainfall',
    'Cloud_Cover', 'Cloud_Visibility', 'Relative_Humidity', 'Temperature',
    'River_Water_Level', 'Wind_Speed', 'Atmospheric_Pressure', 'Soil_Moisture',
    'Drainage_Density', 'Elevation', 'Previous_Flood_History',
    'Rainfall_Index', 'Seasonal_Rainfall_Average', 'Weather_Severity_Index',
    'Flood_Risk_Score'
]

def load_scaler(scaler_path):
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler file not found at {scaler_path}. Please train the model first.")
    return joblib.load(scaler_path)

def validate_input(form_data):
    """
    Validates form data from user input.
    Returns a dictionary of cleaned float/int values if valid, or raises ValueError.
    """
    cleaned_data = {}
    
    # List of expected numeric inputs and their ranges for basic sanity checks
    fields = {
        'Annual_Rainfall': (0.0, 10000.0),
        'Monsoon_Rainfall': (0.0, 10000.0),
        'Winter_Rainfall': (0.0, 10000.0),
        'Summer_Rainfall': (0.0, 10000.0),
        'Cloud_Cover': (0.0, 10.0),            # Octas (0 to 10)
        'Cloud_Visibility': (0.0, 100.0),      # km
        'Relative_Humidity': (0.0, 100.0),     # %
        'Temperature': (-50.0, 60.0),          # °C
        'River_Water_Level': (0.0, 50.0),      # meters
        'Wind_Speed': (0.0, 200.0),            # km/h
        'Atmospheric_Pressure': (900.0, 1100.0),# hPa
        'Soil_Moisture': (0.0, 100.0),         # %
        'Drainage_Density': (0.0, 15.0),       # km/km^2
        'Elevation': (-100.0, 9000.0),         # meters
        'Previous_Flood_History': (0.0, 1.0)   # 0 or 1
    }
    
    for field, (min_val, max_val) in fields.items():
        val_str = form_data.get(field)
        if val_str is None or val_str.strip() == '':
            raise ValueError(f"Missing required field: {field.replace('_', ' ')}")
        try:
            val = float(val_str)
        except ValueError:
            raise ValueError(f"Field {field.replace('_', ' ')} must be a numeric value")
            
        if field == 'Previous_Flood_History':
            val = int(val)
            if val not in [0, 1]:
                raise ValueError("Previous Flood History must be either Yes (1) or No (0)")
        else:
            if not (min_val <= val <= max_val):
                raise ValueError(f"{field.replace('_', ' ')} must be between {min_val} and {max_val}")
                
        cleaned_data[field] = val
        
    return cleaned_data

def preprocess_features(cleaned_data, scaler):
    """
    Applies feature engineering and scales the input vector using the saved scaler.
    """
    # Create DataFrame with single row
    df = pd.DataFrame([cleaned_data])
    
    # Apply identical Feature Engineering
    df['Rainfall_Index'] = (df['Monsoon_Rainfall'] * 0.70 + 
                            df['Winter_Rainfall'] * 0.10 + 
                            df['Summer_Rainfall'] * 0.20)
    
    df['Seasonal_Rainfall_Average'] = df[['Monsoon_Rainfall', 'Winter_Rainfall', 'Summer_Rainfall']].mean(axis=1)
    
    df['Weather_Severity_Index'] = (df['Relative_Humidity'] * df['Temperature'] * 0.01)
    
    df['Flood_Risk_Score'] = (
        (df['River_Water_Level'] * 2.0) + 
        (df['Soil_Moisture'] / 10.0) + 
        (df['Relative_Humidity'] / 20.0) - 
        (df['Elevation'] / 100.0)
    )
    
    # Reorder columns to match feature training order
    df_ordered = df[FEATURES_ORDER]
    
    # Scale features
    scaled_array = scaler.transform(df_ordered)
    
    return scaled_array
