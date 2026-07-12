import sys
import os

# Add the project directories to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset.generate_dataset import generate_flood_dataset
from notebooks.train_models import main as train_models_main

if __name__ == '__main__':
    print("==================================================")
    print("STEP 1: Generating Sample Meteorological Dataset...")
    print("==================================================")
    generate_flood_dataset('E:/sb project/dataset/sample_flood_data.csv')
    
    print("\n==================================================")
    print("STEP 2: Running ML Training and Evaluation...")
    print("==================================================")
    train_models_main()
    
    print("\n==================================================")
    print("ML Pipeline Execution Completed Successfully!")
    print("==================================================")
