import os
import joblib
import numpy as np

def load_best_model(model_path):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. Please train the model first.")
    return joblib.load(model_path)

def get_risk_classification(probability):
    """
    Classifies risk based on flood probability:
    - Low: < 30% (Green)
    - Medium: 30% <= Probability < 60% (Yellow)
    - High: 60% <= Probability < 85% (Orange)
    - Very High: Probability >= 85% (Red)
    """
    prob_percentage = probability * 100
    
    if prob_percentage < 30.0:
        return {
            'level': 'Low',
            'color': '#28a745',      # Green
            'alert_class': 'success',
            'recommendation': 'Conditions are currently stable. Normal observation recommended.'
        }
    elif prob_percentage < 60.0:
        return {
            'level': 'Medium',
            'color': '#ffc107',      # Yellow
            'alert_class': 'warning',
            'recommendation': 'Elevated water/moisture levels detected. Local monitoring advised.'
        }
    elif prob_percentage < 85.0:
        return {
            'level': 'High',
            'color': '#fd7e14',      # Orange
            'alert_class': 'orange', # Custom orange in CSS
            'recommendation': 'Highly critical conditions. Activate regional preparedness and review drainage channels.'
        }
    else:
        return {
            'level': 'Very High',
            'color': '#dc3545',      # Red
            'alert_class': 'danger',
            'recommendation': 'Severe flood threat imminent. Evacuate low-elevation areas and deploy emergency services immediately.'
        }

def make_prediction(scaled_features, model):
    """
    Predicts class and probability.
    """
    prediction = int(model.predict(scaled_features)[0])
    
    # Get probability if model supports predict_proba
    if hasattr(model, 'predict_proba'):
        probability = float(model.predict_proba(scaled_features)[0][1])
    else:
        # Fallback for models without predict_proba (some custom classifiers, but DT/RF/KNN/XGB do)
        probability = 1.0 if prediction == 1 else 0.0
        
    risk_info = get_risk_classification(probability)
    
    return {
        'prediction': prediction,
        'probability': probability,
        'risk_level': risk_info['level'],
        'color': risk_info['color'],
        'alert_class': risk_info['alert_class'],
        'recommendation': risk_info['recommendation']
    }
