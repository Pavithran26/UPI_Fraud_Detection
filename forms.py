from flask_wtf import FlaskForm
from wtforms import FloatField, StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class TransactionForm(FlaskForm):
    amount = FloatField('Transaction Amount', 
                       validators=[DataRequired(), NumberRange(min=0.01, max=1000000)],
                       render_kw={"placeholder": "Enter amount (₹)"})
    
    sender_id = StringField('Sender ID', 
                           validators=[DataRequired(), Length(min=5, max=50)],
                           render_kw={"placeholder": "Enter sender UPI ID"})
    
    receiver_id = StringField('Receiver ID', 
                             validators=[DataRequired(), Length(min=5, max=50)],
                             render_kw={"placeholder": "Enter receiver UPI ID"})
    
    transaction_type = SelectField('Transaction Type',
                                  choices=[('P2P', 'Person to Person'),
                                          ('P2M', 'Person to Merchant'),
                                          ('P2B', 'Person to Business')],
                                  validators=[DataRequired()])
    
    location = StringField('Location', 
                          validators=[Length(max=100)],
                          render_kw={"placeholder": "City, State (optional)"})
    
    device_id = StringField('Device ID', 
                           validators=[Length(max=100)],
                           render_kw={"placeholder": "Device identifier (optional)"})
    
    merchant_category = SelectField('Merchant Category',
                                   choices=[('', 'Select Category'),
                                           ('FOOD', 'Food & Dining'),
                                           ('RETAIL', 'Retail Shopping'),
                                           ('FUEL', 'Fuel & Gas'),
                                           ('HEALTHCARE', 'Healthcare'),
                                           ('EDUCATION', 'Education'),
                                           ('ENTERTAINMENT', 'Entertainment'),
                                           ('TRAVEL', 'Travel & Transport'),
                                           ('UTILITIES', 'Utilities'),
                                           ('OTHER', 'Other')])
    
    submit = SubmitField('Analyze Transaction')
