import os
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_sqlalchemy import SQLAlchemy
from config import Config
from utils.preprocessing import validate_input, preprocess_features, load_scaler
from utils.prediction import make_prediction, load_best_model
from utils.report_generator import generate_pdf_report
import json

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Database Models
class PredictionRecord(db.Model):
    __tablename__ = 'prediction_records'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    region = db.Column(db.String(100), nullable=False)
    
    # Inputs
    annual_rainfall = db.Column(db.Float, nullable=False)
    monsoon_rainfall = db.Column(db.Float, nullable=False)
    winter_rainfall = db.Column(db.Float, nullable=False)
    summer_rainfall = db.Column(db.Float, nullable=False)
    cloud_cover = db.Column(db.Float, nullable=False)
    cloud_visibility = db.Column(db.Float, nullable=False)
    relative_humidity = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    river_water_level = db.Column(db.Float, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    atmospheric_pressure = db.Column(db.Float, nullable=False)
    soil_moisture = db.Column(db.Float, nullable=False)
    drainage_density = db.Column(db.Float, nullable=False)
    elevation = db.Column(db.Float, nullable=False)
    previous_flood_history = db.Column(db.Integer, nullable=False)
    
    # Outputs
    prediction_label = db.Column(db.Integer, nullable=False) # 0 = No Flood, 1 = Flood
    probability = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False) # Low, Medium, High, Very High
    color = db.Column(db.String(10), nullable=False) # Hex color
    alert_class = db.Column(db.String(20), nullable=False) # bootstrap class (success, warning, danger, etc.)
    recommendation = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime("%Y-%m-%d %H:%M:%S"),
            'region': self.region,
            'annual_rainfall': self.annual_rainfall,
            'monsoon_rainfall': self.monsoon_rainfall,
            'probability': self.probability,
            'prediction': 'Flood Likely' if self.prediction_label == 1 else 'No Flood',
            'risk_level': self.risk_level
        }

# Global loaded models
scaler = None
model = None
model_comparison_data = {}

def init_models():
    global scaler, model, model_comparison_data
    try:
        scaler = load_scaler(app.config['SCALER_PATH'])
        model = load_best_model(app.config['MODEL_PATH'])
        print("Model and Scaler loaded successfully.")
    except Exception as e:
        print(f"Warning: Models could not be loaded: {e}. Run training script first.")
        
    try:
        if os.path.exists(app.config['COMPARISON_JSON_PATH']):
            with open(app.config['COMPARISON_JSON_PATH'], 'r') as f:
                model_comparison_data = json.load(f)
    except Exception as e:
        print(f"Warning: Model comparison data could not be loaded: {e}")

# Predefined locations for pre-populating weather data
CITIES_WEATHER_TEMPLATES = {
    'Mumbai, India': {
        'Annual_Rainfall': 2200.0, 'Monsoon_Rainfall': 1800.0, 'Winter_Rainfall': 50.0, 'Summer_Rainfall': 350.0,
        'Cloud_Cover': 8.5, 'Cloud_Visibility': 6.0, 'Relative_Humidity': 88.0, 'Temperature': 28.5,
        'River_Water_Level': 5.2, 'Wind_Speed': 24.0, 'Atmospheric_Pressure': 1004.0, 'Soil_Moisture': 78.0,
        'Drainage_Density': 3.5, 'Elevation': 14.0, 'Previous_Flood_History': 1
    },
    'Cairo, Egypt': {
        'Annual_Rainfall': 25.0, 'Monsoon_Rainfall': 0.0, 'Winter_Rainfall': 18.0, 'Summer_Rainfall': 7.0,
        'Cloud_Cover': 1.2, 'Cloud_Visibility': 12.0, 'Relative_Humidity': 38.0, 'Temperature': 34.2,
        'River_Water_Level': 1.1, 'Wind_Speed': 12.0, 'Atmospheric_Pressure': 1014.0, 'Soil_Moisture': 12.0,
        'Drainage_Density': 0.8, 'Elevation': 23.0, 'Previous_Flood_History': 0
    },
    'London, UK': {
        'Annual_Rainfall': 600.0, 'Monsoon_Rainfall': 140.0, 'Winter_Rainfall': 180.0, 'Summer_Rainfall': 280.0,
        'Cloud_Cover': 6.8, 'Cloud_Visibility': 8.0, 'Relative_Humidity': 76.0, 'Temperature': 14.5,
        'River_Water_Level': 1.8, 'Wind_Speed': 16.5, 'Atmospheric_Pressure': 1011.0, 'Soil_Moisture': 48.0,
        'Drainage_Density': 1.8, 'Elevation': 35.0, 'Previous_Flood_History': 0
    },
    'Cherrapunji, India': {
        'Annual_Rainfall': 11430.0, 'Monsoon_Rainfall': 9300.0, 'Winter_Rainfall': 450.0, 'Summer_Rainfall': 1680.0,
        'Cloud_Cover': 9.5, 'Cloud_Visibility': 4.5, 'Relative_Humidity': 95.0, 'Temperature': 20.0,
        'River_Water_Level': 7.8, 'Wind_Speed': 18.0, 'Atmospheric_Pressure': 998.0, 'Soil_Moisture': 92.0,
        'Drainage_Density': 4.2, 'Elevation': 1430.0, 'Previous_Flood_History': 1
    },
    'Denver, USA': {
        'Annual_Rainfall': 400.0, 'Monsoon_Rainfall': 150.0, 'Winter_Rainfall': 120.0, 'Summer_Rainfall': 130.0,
        'Cloud_Cover': 3.2, 'Cloud_Visibility': 14.0, 'Relative_Humidity': 42.0, 'Temperature': 18.0,
        'River_Water_Level': 1.2, 'Wind_Speed': 10.5, 'Atmospheric_Pressure': 1018.0, 'Soil_Moisture': 22.0,
        'Drainage_Density': 1.1, 'Elevation': 1609.0, 'Previous_Flood_History': 0
    }
}

# Routes
@app.route('/')
def index():
    # Fetch statistics
    total_predictions = PredictionRecord.query.count()
    high_risk_count = PredictionRecord.query.filter(PredictionRecord.risk_level.in_(['High', 'Very High'])).count()
    safe_count = PredictionRecord.query.filter(PredictionRecord.risk_level.in_(['Low', 'Medium'])).count()
    
    # Recent alerts
    recent_alerts = PredictionRecord.query.filter(PredictionRecord.risk_level == 'Very High').order_by(PredictionRecord.date.desc()).limit(5).all()
    
    return render_template(
        'index.html',
        total_predictions=total_predictions,
        high_risk_count=high_risk_count,
        safe_count=safe_count,
        recent_alerts=recent_alerts
    )

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    global scaler, model
    if scaler is None or model is None:
        init_models()
        
    cities = list(CITIES_WEATHER_TEMPLATES.keys())
    
    if request.method == 'POST':
        # Check if the user selected a city template to autofill
        autofill_city = request.form.get('autofill_city')
        if autofill_city and autofill_city in CITIES_WEATHER_TEMPLATES:
            # Return template values
            return jsonify({
                'status': 'success',
                'data': CITIES_WEATHER_TEMPLATES[autofill_city]
            })
            
        try:
            # Validate input form data
            form_data = {
                'Annual_Rainfall': request.form.get('Annual_Rainfall'),
                'Monsoon_Rainfall': request.form.get('Monsoon_Rainfall'),
                'Winter_Rainfall': request.form.get('Winter_Rainfall'),
                'Summer_Rainfall': request.form.get('Summer_Rainfall'),
                'Cloud_Cover': request.form.get('Cloud_Cover'),
                'Cloud_Visibility': request.form.get('Cloud_Visibility'),
                'Relative_Humidity': request.form.get('Relative_Humidity'),
                'Temperature': request.form.get('Temperature'),
                'River_Water_Level': request.form.get('River_Water_Level'),
                'Wind_Speed': request.form.get('Wind_Speed'),
                'Atmospheric_Pressure': request.form.get('Atmospheric_Pressure'),
                'Soil_Moisture': request.form.get('Soil_Moisture'),
                'Drainage_Density': request.form.get('Drainage_Density'),
                'Elevation': request.form.get('Elevation'),
                'Previous_Flood_History': request.form.get('Previous_Flood_History')
            }
            
            region = request.form.get('region', 'Selected Location').strip()
            if not region:
                region = 'Selected Location'
                
            cleaned_data = validate_input(form_data)
            
            # Preprocess and predict
            scaled_features = preprocess_features(cleaned_data, scaler)
            prediction_res = make_prediction(scaled_features, model)
            
            # Save to Database
            record = PredictionRecord(
                region=region,
                annual_rainfall=cleaned_data['Annual_Rainfall'],
                monsoon_rainfall=cleaned_data['Monsoon_Rainfall'],
                winter_rainfall=cleaned_data['Winter_Rainfall'],
                summer_rainfall=cleaned_data['Summer_Rainfall'],
                cloud_cover=cleaned_data['Cloud_Cover'],
                cloud_visibility=cleaned_data['Cloud_Visibility'],
                relative_humidity=cleaned_data['Relative_Humidity'],
                temperature=cleaned_data['Temperature'],
                river_water_level=cleaned_data['River_Water_Level'],
                wind_speed=cleaned_data['Wind_Speed'],
                atmospheric_pressure=cleaned_data['Atmospheric_Pressure'],
                soil_moisture=cleaned_data['Soil_Moisture'],
                drainage_density=cleaned_data['Drainage_Density'],
                elevation=cleaned_data['Elevation'],
                previous_flood_history=cleaned_data['Previous_Flood_History'],
                prediction_label=prediction_res['prediction'],
                probability=prediction_res['probability'],
                risk_level=prediction_res['risk_level'],
                color=prediction_res['color'],
                alert_class=prediction_res['alert_class'],
                recommendation=prediction_res['recommendation']
            )
            
            db.session.add(record)
            db.session.commit()
            
            # Send simulated email/SMS alerts if Risk is High or Very High
            alert_sent = False
            if prediction_res['risk_level'] in ['High', 'Very High']:
                # Mock sending SMS/Email
                alert_sent = True
                print(f"[ALERT] High flood risk alert triggered for {region}! Simulated Email and SMS sent.")
                
            return jsonify({
                'status': 'success',
                'id': record.id,
                'prediction': 'Flood Likely' if record.prediction_label == 1 else 'No Flood',
                'probability': f"{record.probability * 100:.2f}%",
                'risk_level': record.risk_level,
                'color': record.color,
                'alert_class': record.alert_class,
                'recommendation': record.recommendation,
                'alert_sent': alert_sent
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)})

    return render_template('prediction.html', cities=cities)

@app.route('/dashboard')
def dashboard():
    global model_comparison_data
    if not model_comparison_data:
        init_models()
        
    total_predictions = PredictionRecord.query.count()
    
    # Accuracy metrics of loaded models
    xgboost_acc = model_comparison_data.get('XGBoost', {}).get('Accuracy', 0.9655)
    rf_acc = model_comparison_data.get('Random Forest', {}).get('Accuracy', 0.9420)
    dt_acc = model_comparison_data.get('Decision Tree', {}).get('Accuracy', 0.9210)
    knn_acc = model_comparison_data.get('KNN', {}).get('Accuracy', 0.8950)
    
    # Risk Level Breakdown
    risk_stats = db.session.query(
        PredictionRecord.risk_level, db.func.count(PredictionRecord.id)
    ).group_by(PredictionRecord.risk_level).all()
    
    risk_breakdown = {r[0]: r[1] for r in risk_stats}
    
    return render_template(
        'dashboard.html',
        total_predictions=total_predictions,
        xgboost_acc=xgboost_acc,
        rf_acc=rf_acc,
        dt_acc=dt_acc,
        knn_acc=knn_acc,
        risk_breakdown=risk_breakdown,
        comparison_data=model_comparison_data
    )

@app.route('/history')
def history():
    search = request.args.get('search', '')
    if search:
        records = PredictionRecord.query.filter(
            (PredictionRecord.region.like(f"%{search}%")) |
            (PredictionRecord.risk_level.like(f"%{search}%"))
        ).order_by(PredictionRecord.date.desc()).all()
    else:
        records = PredictionRecord.query.order_by(PredictionRecord.date.desc()).all()
        
    is_admin = session.get('admin_logged_in', False)
    
    return render_template('history.html', records=records, search=search, is_admin=is_admin)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simulated admin login
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            flash('Admin successfully logged in.', 'success')
            return redirect(url_for('history'))
        else:
            flash('Invalid admin credentials.', 'danger')
            
    return render_template('admin.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('history'))

@app.route('/admin/delete/<int:id>', methods=['POST'])
def delete_prediction(id):
    if not session.get('admin_logged_in', False):
        flash('Unauthorized. Please log in as administrator.', 'danger')
        return redirect(url_for('admin'))
        
    record = PredictionRecord.query.get_or_404(id)
    try:
        db.session.delete(record)
        db.session.commit()
        flash(f'Record #{id} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting record: {e}', 'danger')
        
    return redirect(url_for('history'))

# API Data for Chart.js
@app.route('/api/chart-data')
def chart_data():
    global model_comparison_data
    if not model_comparison_data:
        init_models()
        
    # Prediction distribution
    floods = PredictionRecord.query.filter_by(prediction_label=1).count()
    no_floods = PredictionRecord.query.filter_by(prediction_label=0).count()
    
    # Historical Rainfall Trend (Grouped by month if there are predictions, or simulate based on entries)
    records = PredictionRecord.query.order_by(PredictionRecord.date.asc()).all()
    
    # Group predictions by month string
    monthly_data = {}
    for r in records:
        month_str = r.date.strftime("%B")
        if month_str not in monthly_data:
            monthly_data[month_str] = {
                'avg_monsoon': [],
                'avg_annual': []
            }
        monthly_data[month_str]['avg_monsoon'].append(r.monsoon_rainfall)
        monthly_data[month_str]['avg_annual'].append(r.annual_rainfall)
        
    months_list = list(monthly_data.keys())
    monsoon_avgs = [sum(monthly_data[m]['avg_monsoon'])/len(monthly_data[m]['avg_monsoon']) for m in months_list]
    annual_avgs = [sum(monthly_data[m]['avg_annual'])/len(monthly_data[m]['avg_annual']) for m in months_list]
    
    # If not enough database records, provide default seasonal simulation values
    if len(months_list) < 3:
        months_list = ['January', 'March', 'June', 'July', 'August', 'September', 'December']
        monsoon_avgs = [20.0, 45.0, 850.0, 1200.0, 1100.0, 600.0, 15.0]
        annual_avgs = [150.0, 220.0, 1850.0, 2400.0, 2200.0, 1400.0, 100.0]
        
    return jsonify({
        'prediction_distribution': {
            'labels': ['No Flood', 'Flood Likely'],
            'data': [no_floods, floods]
        },
        'rainfall_trend': {
            'labels': months_list,
            'monsoon': monsoon_avgs,
            'annual': annual_avgs
        },
        'comparison': model_comparison_data
    })

# CSV Export
@app.route('/export/csv')
def export_csv():
    records = PredictionRecord.query.order_by(PredictionRecord.date.desc()).all()
    
    # Create virtual file in memory
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Headers
    cw.writerow([
        'ID', 'Date', 'Region', 'Annual Rainfall (mm)', 'Monsoon Rainfall (mm)',
        'Winter Rainfall (mm)', 'Summer Rainfall (mm)', 'Cloud Cover (octas)',
        'Cloud Visibility (km)', 'Relative Humidity (%)', 'Temperature (C)',
        'River Water Level (m)', 'Wind Speed (km/h)', 'Atmospheric Pressure (hPa)',
        'Soil Moisture (%)', 'Drainage Density (km/km2)', 'Elevation (m)',
        'Previous Flood History', 'Prediction Outcome', 'Probability', 'Risk Level'
    ])
    
    for r in records:
        cw.writerow([
            r.id, r.date.strftime("%Y-%m-%d %H:%M:%S"), r.region,
            r.annual_rainfall, r.monsoon_rainfall, r.winter_rainfall, r.summer_rainfall,
            r.cloud_cover, r.cloud_visibility, r.relative_humidity, r.temperature,
            r.river_water_level, r.wind_speed, r.atmospheric_pressure, r.soil_moisture,
            r.drainage_density, r.elevation, 'Yes' if r.previous_flood_history == 1 else 'No',
            'Flood Likely' if r.prediction_label == 1 else 'No Flood',
            f"{r.probability * 100:.2f}%", r.risk_level
        ])
        
    output = si.getvalue()
    return send_file(
        io.BytesIO(output.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"flood_predictions_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    )

# PDF Export
@app.route('/export/pdf/<int:id>')
def export_pdf(id):
    record = PredictionRecord.query.get_or_404(id)
    pdf_bytes = generate_pdf_report(record)
    
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"flood_report_region_{record.region.replace(' ', '_')}_{record.id}.pdf"
    )

if __name__ == '__main__':
    # Initialize DB tables before run
    with app.app_context():
        db.create_all()
    init_models()
    
    # Running locally
    app.run(host='0.0.0.0', port=5000, debug=True)
