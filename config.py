import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'flood_prediction_secret_key_129481')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mocking credentials or keys for external APIs
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'mock_api_key_for_testing')
    
    # Model directories
    MODEL_PATH = os.path.join(BASE_DIR, 'model', 'best_model.pkl')
    SCALER_PATH = os.path.join(BASE_DIR, 'model', 'scaler.pkl')
    COMPARISON_JSON_PATH = os.path.join(BASE_DIR, 'model', 'model_comparison.json')
