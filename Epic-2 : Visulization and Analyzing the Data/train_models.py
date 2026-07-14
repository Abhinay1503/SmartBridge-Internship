import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report
)
import joblib

def clean_data(df):
    print("--- Data Cleaning ---")
    # Duplicate checking
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        print(f"Found {duplicates} duplicate rows. Removing them.")
        df = df.drop_duplicates()
    else:
        print("No duplicate rows found.")
        
    # Missing values checking
    missing_vals = df.isnull().sum().sum()
    if missing_vals > 0:
        print(f"Found {missing_vals} missing values. Filling with median/mode.")
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0])
    else:
        print("No missing values found.")
        
    return df

def feature_engineering(df):
    print("--- Feature Engineering ---")
    # 1. Rainfall Index: Weighted rainfall reflecting monsoon severity
    df['Rainfall_Index'] = (df['Monsoon_Rainfall'] * 0.70 + 
                            df['Winter_Rainfall'] * 0.10 + 
                            df['Summer_Rainfall'] * 0.20)
    
    # 2. Seasonal Rainfall Average
    df['Seasonal_Rainfall_Average'] = df[['Monsoon_Rainfall', 'Winter_Rainfall', 'Summer_Rainfall']].mean(axis=1)
    
    # 3. Weather Severity Index: Humidity and Temperature combination
    df['Weather_Severity_Index'] = (df['Relative_Humidity'] * df['Temperature'] * 0.01)
    
    # 4. Flood Risk Score: Heuristic risk combining multiple physical indices
    df['Flood_Risk_Score'] = (
        (df['River_Water_Level'] * 2.0) + 
        (df['Soil_Moisture'] / 10.0) + 
        (df['Relative_Humidity'] / 20.0) - 
        (df['Elevation'] / 100.0)
    )
    
    print(f"Engineered new features. Data shape: {df.shape}")
    return df

def plot_eda(df, output_dir):
    print("--- Generating EDA Visualizations ---")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Correlation Heatmap
    plt.figure(figsize=(14, 10))
    sns.heatmap(df.corr(), annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
    plt.title('Feature Correlation Matrix')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'correlation_matrix.png'))
    plt.close()
    
    # 2. Target Count Plot
    plt.figure(figsize=(6, 4))
    sns.countplot(x='Flood', data=df, palette='Blues')
    plt.title('Flood Occurrence Class Distribution')
    plt.xticks([0, 1], ['No Flood (0)', 'Flood (1)'])
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'flood_distribution.png'))
    plt.close()
    
    # 3. Distribution of River Level by Flood status
    plt.figure(figsize=(8, 5))
    sns.kdeplot(data=df, x='River_Water_Level', hue='Flood', fill=True, common_norm=False, palette='crest')
    plt.title('River Water Level Distribution by Flood Status')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'river_level_distribution.png'))
    plt.close()

def main():
    dataset_path = 'E:/sb project/dataset/sample_flood_data.csv'
    model_dir = 'E:/sb project/model'
    static_img_dir = 'E:/sb project/static/images'
    
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(static_img_dir, exist_ok=True)
    
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}. Please generate it first.")
        return
        
    df = pd.read_csv(dataset_path)
    df = clean_data(df)
    df = feature_engineering(df)
    
    # Plot EDA
    plot_eda(df, static_img_dir)
    
    # Split features and target
    X = df.drop(columns=['Flood'])
    y = df['Flood']
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Feature Scaling
    scaler = StandardScaler()
    scaled_cols = X_train.select_dtypes(include=['float64', 'int64']).columns
    # We want to scale everything except the binary history column, but scaling it is also fine. Let's scale all features.
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)
    
    # Save the scaler
    joblib.dump(scaler, os.path.join(model_dir, 'scaler.pkl'))
    print("Scaler saved successfully.")
    
    # Define models and grids for Hyperparameter Tuning
    models = {
        'Decision Tree': {
            'model': DecisionTreeClassifier(random_state=42),
            'params': {
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10]
            }
        },
        'Random Forest': {
            'model': RandomForestClassifier(random_state=42),
            'params': {
                'n_estimators': [50, 100, 150],
                'max_depth': [8, 12, None],
                'min_samples_split': [2, 5]
            }
        },
        'KNN': {
            'model': KNeighborsClassifier(),
            'params': {
                'n_neighbors': [3, 5, 7, 9],
                'weights': ['uniform', 'distance']
            }
        },
        'XGBoost': {
            'model': xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='logloss'),
            'params': {
                'n_estimators': [50, 100, 150],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.05, 0.1, 0.2]
            }
        }
    }
    
    results = {}
    best_estimators = {}
    
    plt.figure(figsize=(10, 8)) # For combined ROC curves
    
    for name, config in models.items():
        print(f"\nTuning and Training {name}...")
        grid = GridSearchCV(config['model'], config['params'], cv=5, scoring='accuracy', n_jobs=-1)
        grid.fit(X_train_scaled, y_train)
        
        best_model = grid.best_estimator_
        best_estimators[name] = best_model
        print(f"Best parameters for {name}: {grid.best_params_}")
        
        # Predictions
        y_pred = best_model.predict(X_test_scaled)
        y_proba = best_model.predict_proba(X_test_scaled)[:, 1] if hasattr(best_model, 'predict_proba') else y_pred
        
        # Metrics
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_proba)
        
        results[name] = {
            'Accuracy': float(acc),
            'Precision': float(prec),
            'Recall': float(rec),
            'F1-Score': float(f1),
            'ROC-AUC': float(auc)
        }
        
        # Plot ROC curve for this model
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        plt.plot(fpr, tpr, label=f"{name} (AUC = {auc:.4f})")
        
        # Individual Confusion Matrix
        plt.figure(figsize=(5, 4))
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['No Flood', 'Flood'], yticklabels=['No Flood', 'Flood'])
        plt.title(f'{name} Confusion Matrix')
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.tight_layout()
        plt.savefig(os.path.join(static_img_dir, f'confusion_matrix_{name.lower().replace(" ", "_")}.png'))
        plt.close()
        
        print(f"{name} Results - Acc: {acc:.4f}, Prec: {prec:.4f}, Rec: {rec:.4f}, F1: {f1:.4f}, AUC: {auc:.4f}")
        print(classification_report(y_test, y_pred))
        
    # Save ROC curves plot
    plt.plot([0, 1], [0, 1], 'k--', label='Random Guess')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curves')
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(static_img_dir, 'roc_curves.png'))
    plt.close()
    
    # Create Comparison Table DataFrame
    comparison_df = pd.DataFrame(results).T.reset_index().rename(columns={'index': 'Model'})
    comparison_df = comparison_df.round(4)
    print("\n--- Model Comparison ---")
    print(comparison_df)
    
    # Save comparison report JSON
    comparison_json_path = os.path.join(model_dir, 'model_comparison.json')
    with open(comparison_json_path, 'w') as f:
        json.dump(results, f, indent=4)
        
    # Select best model based on F1-Score (or Accuracy)
    best_model_name = comparison_df.loc[comparison_df['Accuracy'].idxmax(), 'Model']
    print(f"\nBest performing model based on accuracy: {best_model_name}")
    
    best_clf = best_estimators[best_model_name]
    joblib.dump(best_clf, os.path.join(model_dir, 'best_model.pkl'))
    print(f"Successfully saved best model ({best_model_name}) to {os.path.join(model_dir, 'best_model.pkl')}")
    
    # Plot feature importance for best model if tree-based (XGBoost/RF)
    if hasattr(best_clf, 'feature_importances_'):
        plt.figure(figsize=(10, 6))
        importances = best_clf.feature_importances_
        indices = np.argsort(importances)[::-1]
        features = X.columns
        
        sns.barplot(x=importances[indices], y=[features[i] for i in indices], palette='viridis')
        plt.title(f'Feature Importances - {best_model_name}')
        plt.xlabel('Importance Value')
        plt.ylabel('Features')
        plt.tight_layout()
        plt.savefig(os.path.join(static_img_dir, 'feature_importance.png'))
        plt.close()
        print("Feature importance plot generated and saved.")

if __name__ == '__main__':
    main()
