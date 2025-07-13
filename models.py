from app import db
from datetime import datetime
from sqlalchemy import func

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    sender_id = db.Column(db.String(50), nullable=False)
    receiver_id = db.Column(db.String(50), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_fraud = db.Column(db.Boolean, default=False)
    risk_score = db.Column(db.Float, default=0.0)
    location = db.Column(db.String(100))
    device_id = db.Column(db.String(100))
    merchant_category = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'transaction_type': self.transaction_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_fraud': self.is_fraud,
            'risk_score': self.risk_score,
            'location': self.location,
            'device_id': self.device_id,
            'merchant_category': self.merchant_category
        }

class FraudAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # HIGH, MEDIUM, LOW
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)
    
    transaction = db.relationship('Transaction', backref=db.backref('alerts', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'is_resolved': self.is_resolved,
            'transaction': self.transaction.to_dict() if self.transaction else None
        }
