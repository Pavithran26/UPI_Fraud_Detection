from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Transaction, FraudAlert
from forms import TransactionForm
from fraud_detector import fraud_detector
from datetime import datetime, timedelta
from sqlalchemy import desc, func
import logging

@app.route('/')
def dashboard():
    """Main dashboard showing fraud statistics and alerts"""
    
    # Get recent transactions
    recent_transactions = Transaction.query.order_by(desc(Transaction.timestamp)).limit(10).all()
    
    # Get fraud statistics
    total_transactions = Transaction.query.count()
    fraud_transactions = Transaction.query.filter_by(is_fraud=True).count()
    fraud_rate = (fraud_transactions / max(total_transactions, 1)) * 100
    
    # Get recent alerts
    recent_alerts = FraudAlert.query.filter_by(is_resolved=False).order_by(desc(FraudAlert.timestamp)).limit(5).all()
    
    # Get high-risk transactions (risk score > 0.8)
    high_risk_transactions = Transaction.query.filter(Transaction.risk_score > 0.8).count()
    
    # Calculate average transaction amount
    avg_amount_result = db.session.query(func.avg(Transaction.amount)).first()
    avg_transaction_amount = avg_amount_result[0] if avg_amount_result[0] else 0
    
    # Get transaction volume by hour for the last 24 hours
    last_24h = datetime.utcnow() - timedelta(hours=24)
    hourly_transactions = db.session.query(
        func.strftime('%H', Transaction.timestamp).label('hour'),
        func.count(Transaction.id).label('count')
    ).filter(Transaction.timestamp >= last_24h).group_by(
        func.strftime('%H', Transaction.timestamp)
    ).all()
    
    # Prepare chart data
    hours = [f"{i:02d}:00" for i in range(24)]
    transaction_counts = [0] * 24
    for hour_data in hourly_transactions:
        hour_index = int(hour_data.hour)
        transaction_counts[hour_index] = hour_data.count
    
    stats = {
        'total_transactions': total_transactions,
        'fraud_transactions': fraud_transactions,
        'fraud_rate': round(fraud_rate, 2),
        'high_risk_transactions': high_risk_transactions,
        'avg_transaction_amount': round(avg_transaction_amount, 2)
    }
    
    chart_data = {
        'hours': hours,
        'transaction_counts': transaction_counts
    }
    
    return render_template('dashboard.html', 
                         stats=stats,
                         recent_transactions=recent_transactions,
                         recent_alerts=recent_alerts,
                         chart_data=chart_data)

@app.route('/test-transaction', methods=['GET', 'POST'])
def test_transaction():
    """Form to test fraud detection on a new transaction"""
    form = TransactionForm()
    
    if form.validate_on_submit():
        # Create transaction data
        transaction_data = {
            'amount': form.amount.data,
            'sender_id': form.sender_id.data,
            'receiver_id': form.receiver_id.data,
            'transaction_type': form.transaction_type.data,
            'location': form.location.data or '',
            'device_id': form.device_id.data or '',
            'merchant_category': form.merchant_category.data or 'OTHER',
            'timestamp': datetime.utcnow()
        }
        
        # Run fraud detection
        try:
            fraud_probability, risk_level = fraud_detector.predict_fraud(transaction_data)
            is_fraud = fraud_probability > 0.5
            
            # Save transaction to database
            transaction = Transaction(
                amount=transaction_data['amount'],
                sender_id=transaction_data['sender_id'],
                receiver_id=transaction_data['receiver_id'],
                transaction_type=transaction_data['transaction_type'],
                location=transaction_data['location'],
                device_id=transaction_data['device_id'],
                merchant_category=transaction_data['merchant_category'],
                is_fraud=is_fraud,
                risk_score=fraud_probability,
                timestamp=transaction_data['timestamp']
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            # Create fraud alert if high risk
            if fraud_probability > 0.7:
                reasons = fraud_detector.get_fraud_reasons(transaction_data, fraud_probability)
                alert_message = f"High-risk transaction detected. Reasons: {', '.join(reasons)}"
                
                alert = FraudAlert(
                    transaction_id=transaction.id,
                    alert_type='HIGH_RISK_TRANSACTION',
                    severity=risk_level,
                    message=alert_message
                )
                
                db.session.add(alert)
                db.session.commit()
                
                flash(f'Transaction flagged as {risk_level} risk! Risk Score: {fraud_probability:.2%}', 'danger')
            elif fraud_probability > 0.3:
                flash(f'Transaction marked as {risk_level} risk. Risk Score: {fraud_probability:.2%}', 'warning')
            else:
                flash(f'Transaction appears legitimate. Risk Score: {fraud_probability:.2%}', 'success')
            
            return redirect(url_for('transaction_result', transaction_id=transaction.id))
            
        except Exception as e:
            logging.error(f"Error processing transaction: {e}")
            flash('Error processing transaction. Please try again.', 'danger')
    
    return render_template('test_transaction.html', form=form)

@app.route('/transaction/<int:transaction_id>')
def transaction_result(transaction_id):
    """Show detailed results for a specific transaction"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Get fraud reasons
    transaction_data = transaction.to_dict()
    reasons = fraud_detector.get_fraud_reasons(transaction_data, transaction.risk_score)
    
    # Get any associated alerts
    alerts = FraudAlert.query.filter_by(transaction_id=transaction_id).all()
    
    return render_template('transaction_result.html', 
                         transaction=transaction, 
                         reasons=reasons,
                         alerts=alerts)

@app.route('/api/alerts')
def api_alerts():
    """API endpoint to get recent fraud alerts"""
    alerts = FraudAlert.query.filter_by(is_resolved=False).order_by(desc(FraudAlert.timestamp)).limit(10).all()
    return jsonify([alert.to_dict() for alert in alerts])

@app.route('/resolve-alert/<int:alert_id>', methods=['POST'])
def resolve_alert(alert_id):
    """Mark an alert as resolved"""
    alert = FraudAlert.query.get_or_404(alert_id)
    alert.is_resolved = True
    db.session.commit()
    flash('Alert marked as resolved.', 'success')
    return redirect(url_for('dashboard'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
