import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import joblib
import os
import logging

class FraudDetector:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = [
            'amount', 'hour', 'day_of_week', 'transaction_type_encoded',
            'amount_percentile', 'merchant_category_encoded'
        ]
        self.is_trained = False
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model with basic training data if no saved model exists"""
        model_path = 'fraud_model.joblib'
        if os.path.exists(model_path):
            try:
                self._load_model()
                logging.info("Loaded existing fraud detection model")
                return
            except Exception as e:
                logging.error(f"Error loading model: {e}")
        
        # Create initial training data for the model
        self._create_initial_training_data()
        self._train_initial_model()
        logging.info("Initialized new fraud detection model")
    
    def _create_initial_training_data(self):
        """Create initial training data to bootstrap the model"""
        np.random.seed(42)
        n_samples = 1000
        
        # Generate synthetic training data
        data = {
            'amount': np.random.lognormal(3, 1.5, n_samples),
            'hour': np.random.randint(0, 24, n_samples),
            'day_of_week': np.random.randint(0, 7, n_samples),
            'transaction_type': np.random.choice(['P2P', 'P2M', 'P2B'], n_samples),
            'merchant_category': np.random.choice([
                'FOOD', 'RETAIL', 'FUEL', 'HEALTHCARE', 'EDUCATION', 
                'ENTERTAINMENT', 'TRAVEL', 'UTILITIES', 'OTHER'
            ], n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Create fraud labels based on suspicious patterns
        fraud_conditions = (
            (df['amount'] > 50000) |  # Very high amounts
            ((df['hour'] < 6) | (df['hour'] > 22)) |  # Unusual hours
            (df['amount'] < 1)  # Very small amounts (potential testing)
        )
        
        # Add some randomness to fraud detection
        random_fraud = np.random.random(n_samples) < 0.05
        df['is_fraud'] = (fraud_conditions | random_fraud).astype(int)
        
        self.training_data = df
    
    def _train_initial_model(self):
        """Train the initial model with bootstrap data"""
        df = self.training_data
        
        # Prepare features
        features = self._prepare_features(df)
        target = df['is_fraud']
        
        # Train the model
        self.model.fit(features, target)
        self.is_trained = True
        
        # Save the model
        self._save_model()
    
    def _prepare_features(self, df):
        """Prepare features for training or prediction"""
        df = df.copy()
        
        # Add derived features
        df['amount_percentile'] = pd.qcut(df['amount'], q=10, labels=False, duplicates='drop')
        
        # Encode categorical variables
        for col in ['transaction_type', 'merchant_category']:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                self.label_encoders[col].fit(df[col])
            
            encoded_col = f"{col}_encoded"
            try:
                df[encoded_col] = self.label_encoders[col].transform(df[col])
            except ValueError:
                # Handle unseen categories
                df[encoded_col] = 0
        
        # Select and scale features
        feature_df = df[self.feature_columns].fillna(0)
        
        if not hasattr(self.scaler, 'scale_'):
            scaled_features = self.scaler.fit_transform(feature_df)
        else:
            scaled_features = self.scaler.transform(feature_df)
        
        return scaled_features
    
    def predict_fraud(self, transaction_data):
        """Predict if a transaction is fraudulent"""
        if not self.is_trained:
            return 0.5, "Model not trained"
        
        try:
            # Convert transaction data to DataFrame
            df = pd.DataFrame([transaction_data])
            
            # Add time-based features
            if 'timestamp' in transaction_data:
                timestamp = pd.to_datetime(transaction_data['timestamp'])
            else:
                timestamp = datetime.now()
            
            df['hour'] = timestamp.hour
            df['day_of_week'] = timestamp.weekday()
            
            # Prepare features
            features = self._prepare_features(df)
            
            # Get prediction probability
            fraud_probability = self.model.predict_proba(features)[0][1]
            
            # Determine risk level
            if fraud_probability > 0.8:
                risk_level = "HIGH"
            elif fraud_probability > 0.5:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            return fraud_probability, risk_level
            
        except Exception as e:
            logging.error(f"Error in fraud prediction: {e}")
            return 0.5, "UNKNOWN"
    
    def get_fraud_reasons(self, transaction_data, fraud_probability):
        """Get reasons why a transaction might be flagged as fraud"""
        reasons = []
        
        amount = transaction_data.get('amount', 0)
        hour = datetime.now().hour if 'timestamp' not in transaction_data else pd.to_datetime(transaction_data['timestamp']).hour
        
        if amount > 50000:
            reasons.append("Very high transaction amount")
        
        if amount < 1:
            reasons.append("Unusually low transaction amount")
        
        if hour < 6 or hour > 22:
            reasons.append("Transaction at unusual hours")
        
        if fraud_probability > 0.8:
            reasons.append("Multiple risk factors detected")
        
        if not reasons:
            reasons.append("Standard risk assessment completed")
        
        return reasons
    
    def _save_model(self):
        """Save the trained model and encoders"""
        model_data = {
            'model': self.model,
            'label_encoders': self.label_encoders,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, 'fraud_model.joblib')
    
    def _load_model(self):
        """Load a saved model and encoders"""
        model_data = joblib.load('fraud_model.joblib')
        self.model = model_data['model']
        self.label_encoders = model_data['label_encoders']
        self.scaler = model_data['scaler']
        self.feature_columns = model_data['feature_columns']
        self.is_trained = model_data['is_trained']

# Global fraud detector instance
fraud_detector = FraudDetector()
