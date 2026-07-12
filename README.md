# AI-Powered Flood Prediction System

An end-to-end Machine Learning web application designed to predict flood probabilities using historical and real-time meteorological/geographical data. This system incorporates four distinct classification models (Decision Tree, Random Forest, K-Nearest Neighbors, and XGBoost), selects the highest-performing model automatically, provides interactive dashboards, dynamic risk recommendations, prediction history log management, and is fully configured for deployment on IBM Cloud.

---

## Technical Stack
- **Backend**: Python 3.10+, Flask, SQLite, SQLAlchemy, Scikit-Learn, XGBoost, Joblib, ReportLab (PDF reporting).
- **Frontend**: HTML5, CSS3 (Glassmorphism, custom dark/light theme variables), JavaScript, Bootstrap 5, Chart.js, Font Awesome.
- **Testing**: Pytest.
- **Deployment**: Gunicorn, IBM Cloud Foundry configurations (`manifest.yml`, `Procfile`, `runtime.txt`).

---

## File Structure
```
FloodPrediction/
├── app.py                      # Flask backend and route controllers
├── config.py                   # App parameters & SQLite URI configuration
├── requirements.txt            # Python dependencies
├── Procfile                    # IBM Cloud process configuration
├── manifest.yml                # IBM Cloud Foundry deployment manifest
├── runtime.txt                 # IBM Cloud Python version specification
├── database.db                 # SQLite database (auto-generated on startup)
├── model/                      # Serialized assets
│   ├── best_model.pkl          # Saved best model (XGBoost)
│   ├── scaler.pkl              # Saved features scaler
│   └── model_comparison.json   # JSON file with comparison metrics
├── static/
│   ├── css/
│   │   └── style.css           # Modern styles with Dark Mode & Glassmorphic variables
│   └── js/
│       ├── main.js             # Theme toggle & sidebar state controller
│       ├── prediction.js       # AJAX submission, location loader & modal animations
│       └── dashboard.js        # Chart.js analytics layout
├── templates/
│   ├── base.html               # Master layout
│   ├── index.html              # System home and active alerts
│   ├── prediction.html         # Interactive calculator and result panel
│   ├── dashboard.html          # Performance charts and comparison matrix
│   ├── history.html            # Query history with search, CSV & PDF downloads
│   └── admin.html              # Credentials lock screen for deleting records
├── utils/
│   ├── preprocessing.py        # Validations, feature engineering & scaling
│   ├── prediction.py           # Model predictor and risk classification
│   └── report_generator.py     # PDF Report compilation using ReportLab
├── dataset/
│   ├── generate_dataset.py     # Weather/flood synthetic data generator
│   └── sample_flood_data.csv   # Target dataset for ML pipelines
└── tests/
    ├── test_preprocessing.py   # Preprocessing test suite
    └── test_prediction.py      # Prediction test suite
```

---

## Setup & Running Locally

Follow these steps to run the application on your local machine:

### 1. Clone the Project & Navigate
```bash
cd FloodPrediction
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate Sample Dataset
Since historical meteorological datasets can be massive and specific, a simulation generator is provided to create a scientifically balanced dataset of 5,000 observations containing features such as annual/monsoon rainfall, humidity, river levels, soil moisture, elevation, and historical flooding index.
```bash
python dataset/generate_dataset.py
```

### 4. Train the Models
Run the training script to clean data, perform feature engineering, run grid search hyperparameter tuning for Decision Tree, Random Forest, KNN, and XGBoost, compile classification reports, generate plots (correlation heatmaps, ROC curves, feature importances), select the best model, and serialize it to the `model/` folder.
```bash
python notebooks/train_models.py
```

### 5. Launch the Flask Server
```bash
python app.py
```
Open a browser and navigate to `http://127.0.0.1:5000`.

---

## Running Unit Tests
Execute the unit tests to verify input validation, feature engineering shape, and risk level classifications:
```bash
pytest
```

---

## Application Features

### Location-Based Prepopulation
In the Predict panel, select a city from the dropdown (e.g. *Mumbai, India*, *Cherrapunji, India*, *Cairo, Egypt*, *London, UK*, *Denver, USA*) and click **Fetch Weather Data** to pre-populate all form fields based on typical regional meteorological behaviors.

### Risk Level Classifications
Risks are dynamically evaluated based on prediction probabilities:
- **Low Risk** (< 30%): Green indicator. Stable conditions.
- **Medium Risk** (30% - 60%): Yellow indicator. Local monitoring advised.
- **High Risk** (60% - 85%): Orange indicator. Prepare regional drainage channels.
- **Very High Risk** (>= 85%): Red pulsing indicator. Evacuate low elevation zones, dispatch emergency units.

### Administrative Controls
- **Default Username**: `admin`
- **Default Password**: `admin123`
Log in via the **Admin Portal** link on the sidebar. Once logged in:
- A red `Admin Privileges` badge will appear.
- You can delete specific records from the **Prediction History** log.

### Reports & Export
- **CSV Export**: Click `Export CSV` on the History page to download the complete SQLite database of predictions.
- **PDF Export**: Generate a printable, formal PDF report for any prediction record, containing color-coded risk highlights, specific recommendations, and weather metrics.

---

## Deployment to IBM Cloud

This project is fully configured for deployment on IBM Cloud Foundry:

1. Ensure the [IBM Cloud CLI](https://cloud.ibm.com/docs/cli) is installed and you are logged in.
2. Target your Cloud Foundry org and space:
   ```bash
   ibmcloud target --cf
   ```
3. Deploy the application:
   ```bash
   ibmcloud cf push
   ```
The command uses configurations in `manifest.yml`, `Procfile`, and `runtime.txt` to select the Python buildpack, allocate memory (512MB), and run Gunicorn.
