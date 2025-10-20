import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import re

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
MEDICATIONS_TABLE = os.environ['MEDICATIONS_TABLE']
REMINDERS_TOPIC = os.environ['REMINDERS_TOPIC']

def lambda_handler(event, context):
    """
    Medication management Lambda function for tracking medications,
    scheduling reminders, and monitoring adherence
    """
    try:
        logger.info(f"Processing medication management event: {json.dumps(event)}")
        
        # Parse the incoming event
        if 'Records' in event:
            # SQS/EventBridge trigger
            for record in event['Records']:
                process_medication_event(record)
        else:
            # Direct API call
            process_medication_event(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Medication management processed successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in medication management: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Medication management failed',
                'message': str(e)
            })
        }

def process_medication_event(record):
    """Process individual medication event"""
    try:
        # Extract medication data
        if 'body' in record:
            medication_data = json.loads(record['body'])
        else:
            medication_data = record
        
        action = medication_data.get('action')
        user_id = medication_data.get('userId')
        
        if not user_id:
            raise ValueError("userId is required")
        
        if action == 'add_medication':
            add_medication(user_id, medication_data)
        elif action == 'update_medication':
            update_medication(user_id, medication_data)
        elif action == 'remove_medication':
            remove_medication(user_id, medication_data)
        elif action == 'log_dose':
            log_medication_dose(user_id, medication_data)
        elif action == 'check_reminders':
            check_medication_reminders()
        elif action == 'get_medications':
            return get_user_medications(user_id)
        else:
            raise ValueError(f"Unknown action: {action}")
        
        logger.info(f"Processed medication action '{action}' for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing medication event: {str(e)}")
        raise

def add_medication(user_id, medication_data):
    """Add a new medication for a user"""
    table = dynamodb.Table(MEDICATIONS_TABLE)
    
    medication_id = medication_data.get('medicationId', str(uuid.uuid4()))
    medication_name = medication_data.get('medicationName')
    dosage = medication_data.get('dosage')
    frequency = medication_data.get('frequency')
    start_date = medication_data.get('startDate', datetime.utcnow().isoformat())
    end_date = medication_data.get('endDate')
    instructions = medication_data.get('instructions', '')
    
    if not medication_name or not dosage or not frequency:
        raise ValueError("medicationName, dosage, and frequency are required")
    
    # Validate frequency format
    if not validate_frequency(frequency):
        raise ValueError("Invalid frequency format. Use format like '2x daily', 'every 8 hours', etc.")
    
    item = {
        'userId': user_id,
        'medicationId': medication_id,
        'medicationName': medication_name,
        'dosage': dosage,
        'frequency': frequency,
        'startDate': start_date,
        'endDate': end_date,
        'instructions': instructions,
        'status': 'active',
        'createdAt': datetime.utcnow().isoformat(),
        'lastTaken': None,
        'adherenceRate': 0.0,
        'totalDoses': 0,
        'missedDoses': 0
    }
    
    table.put_item(Item=item)
    logger.info(f"Added medication {medication_name} for user {user_id}")
    
    # Update CloudWatch metrics
    update_medication_metrics(user_id, 'medication_added')

def update_medication(user_id, medication_data):
    """Update an existing medication"""
    table = dynamodb.Table(MEDICATIONS_TABLE)
    
    medication_id = medication_data.get('medicationId')
    if not medication_id:
        raise ValueError("medicationId is required for update")
    
    # Get existing medication
    response = table.get_item(
        Key={'userId': user_id, 'medicationId': medication_id}
    )
    
    if 'Item' not in response:
        raise ValueError(f"Medication {medication_id} not found for user {user_id}")
    
    existing_item = response['Item']
    
    # Update fields
    update_expression = "SET updatedAt = :updated_at"
    expression_values = {':updated_at': datetime.utcnow().isoformat()}
    
    updatable_fields = ['medicationName', 'dosage', 'frequency', 'endDate', 'instructions', 'status']
    
    for field in updatable_fields:
        if field in medication_data:
            update_expression += f", {field} = :{field}"
            expression_values[f':{field}'] = medication_data[field]
    
    table.update_item(
        Key={'userId': user_id, 'medicationId': medication_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values
    )
    
    logger.info(f"Updated medication {medication_id} for user {user_id}")

def remove_medication(user_id, medication_data):
    """Remove a medication (soft delete by setting status to inactive)"""
    table = dynamodb.Table(MEDICATIONS_TABLE)
    
    medication_id = medication_data.get('medicationId')
    if not medication_id:
        raise ValueError("medicationId is required for removal")
    
    table.update_item(
        Key={'userId': user_id, 'medicationId': medication_id},
        UpdateExpression="SET #status = :status, updatedAt = :updated_at",
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'inactive',
            ':updated_at': datetime.utcnow().isoformat()
        }
    )
    
    logger.info(f"Removed medication {medication_id} for user {user_id}")
    
    # Update CloudWatch metrics
    update_medication_metrics(user_id, 'medication_removed')

def log_medication_dose(user_id, medication_data):
    """Log a medication dose taken"""
    table = dynamodb.Table(MEDICATIONS_TABLE)
    
    medication_id = medication_data.get('medicationId')
    dose_time = medication_data.get('doseTime', datetime.utcnow().isoformat())
    
    if not medication_id:
        raise ValueError("medicationId is required for logging dose")
    
    # Get existing medication
    response = table.get_item(
        Key={'userId': user_id, 'medicationId': medication_id}
    )
    
    if 'Item' not in response:
        raise ValueError(f"Medication {medication_id} not found for user {user_id}")
    
    medication = response['Item']
    
    # Update medication record
    table.update_item(
        Key={'userId': user_id, 'medicationId': medication_id},
        UpdateExpression="SET lastTaken = :last_taken, totalDoses = totalDoses + :inc, updatedAt = :updated_at",
        ExpressionAttributeValues={
            ':last_taken': dose_time,
            ':inc': 1,
            ':updated_at': datetime.utcnow().isoformat()
        }
    )
    
    # Calculate and update adherence rate
    update_adherence_rate(user_id, medication_id)
    
    logger.info(f"Logged dose for medication {medication_id} for user {user_id}")
    
    # Update CloudWatch metrics
    update_medication_metrics(user_id, 'dose_logged')

def check_medication_reminders():
    """Check for medications that need reminders"""
    table = dynamodb.Table(MEDICATIONS_TABLE)
    
    # Scan for active medications
    response = table.scan(
        FilterExpression='#status = :status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':status': 'active'}
    )
    
    medications = response.get('Items', [])
    current_time = datetime.utcnow()
    
    for medication in medications:
        if should_send_reminder(medication, current_time):
            send_medication_reminder(medication)

def should_send_reminder(medication, current_time):
    """Determine if a reminder should be sent for a medication"""
    frequency = medication.get('frequency', '')
    last_taken = medication.get('lastTaken')
    
    if not last_taken:
        # First reminder if never taken
        return True
    
    last_taken_dt = datetime.fromisoformat(last_taken.replace('Z', '+00:00'))
    
    # Parse frequency and calculate next dose time
    if 'daily' in frequency.lower():
        # Daily medication
        if '2x' in frequency or 'twice' in frequency:
            # Twice daily - every 12 hours
            next_dose = last_taken_dt + timedelta(hours=12)
        elif '3x' in frequency or 'three' in frequency:
            # Three times daily - every 8 hours
            next_dose = last_taken_dt + timedelta(hours=8)
        else:
            # Once daily - every 24 hours
            next_dose = last_taken_dt + timedelta(hours=24)
    elif 'hour' in frequency.lower():
        # Hourly medication
        hours_match = re.search(r'(\d+)', frequency)
        if hours_match:
            hours = int(hours_match.group(1))
            next_dose = last_taken_dt + timedelta(hours=hours)
        else:
            return False
    else:
        # Default to daily
        next_dose = last_taken_dt + timedelta(hours=24)
    
    # Send reminder 15 minutes before next dose
    reminder_time = next_dose - timedelta(minutes=15)
    
    return current_time >= reminder_time and current_time <= next_dose

def send_medication_reminder(medication):
    """Send medication reminder via SNS"""
    try:
        user_id = medication['userId']
        medication_name = medication['medicationName']
        dosage = medication['dosage']
        frequency = medication['frequency']
        
        reminder_message = {
            'userId': user_id,
            'medicationId': medication['medicationId'],
            'medicationName': medication_name,
            'dosage': dosage,
            'frequency': frequency,
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'Time to take {medication_name} ({dosage}) - {frequency}'
        }
        
        sns.publish(
            TopicArn=REMINDERS_TOPIC,
            Message=json.dumps(reminder_message),
            Subject=f'Medication Reminder: {medication_name}'
        )
        
        logger.info(f"Sent medication reminder for {medication_name} to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending medication reminder: {str(e)}")

def get_user_medications(user_id):
    """Get all medications for a user"""
    table = dynamodb.Table(MEDICATIONS_TABLE)
    
    response = table.query(
        KeyConditionExpression='userId = :userId',
        ExpressionAttributeValues={':userId': user_id}
    )
    
    medications = response.get('Items', [])
    
    # Filter out inactive medications
    active_medications = [m for m in medications if m.get('status') == 'active']
    
    return active_medications

def update_adherence_rate(user_id, medication_id):
    """Calculate and update medication adherence rate"""
    table = dynamodb.Table(MEDICATIONS_TABLE)
    
    # Get medication
    response = table.get_item(
        Key={'userId': user_id, 'medicationId': medication_id}
    )
    
    if 'Item' not in response:
        return
    
    medication = response['Item']
    total_doses = medication.get('totalDoses', 0)
    missed_doses = medication.get('missedDoses', 0)
    
    if total_doses + missed_doses > 0:
        adherence_rate = total_doses / (total_doses + missed_doses)
    else:
        adherence_rate = 0.0
    
    table.update_item(
        Key={'userId': user_id, 'medicationId': medication_id},
        UpdateExpression="SET adherenceRate = :adherence_rate",
        ExpressionAttributeValues={':adherence_rate': Decimal(str(adherence_rate))}
    )

def validate_frequency(frequency):
    """Validate medication frequency format"""
    if not frequency:
        return False
    
    # Common frequency patterns
    patterns = [
        r'\d+x\s+daily',
        r'\d+\s+times\s+daily',
        r'every\s+\d+\s+hours',
        r'once\s+daily',
        r'twice\s+daily',
        r'three\s+times\s+daily',
        r'as\s+needed',
        r'prn'
    ]
    
    frequency_lower = frequency.lower()
    return any(re.search(pattern, frequency_lower) for pattern in patterns)

def update_medication_metrics(user_id, action):
    """Update CloudWatch metrics for medication management"""
    try:
        cloudwatch.put_metric_data(
            Namespace='HealthAssistant/Medications',
            MetricData=[{
                'MetricName': action.title().replace('_', ''),
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': user_id}
                ]
            }]
        )
        
    except Exception as e:
        logger.error(f"Error updating medication metrics: {str(e)}")

def get_medication_adherence_report(user_id, days=30):
    """Generate medication adherence report for a user"""
    table = dynamodb.Table(MEDICATIONS_TABLE)
    
    response = table.query(
        KeyConditionExpression='userId = :userId',
        ExpressionAttributeValues={':userId': user_id}
    )
    
    medications = response.get('Items', [])
    active_medications = [m for m in medications if m.get('status') == 'active']
    
    report = {
        'userId': user_id,
        'reportDate': datetime.utcnow().isoformat(),
        'periodDays': days,
        'totalMedications': len(active_medications),
        'medications': []
    }
    
    for medication in active_medications:
        med_report = {
            'medicationId': medication['medicationId'],
            'medicationName': medication['medicationName'],
            'adherenceRate': float(medication.get('adherenceRate', 0.0)),
            'totalDoses': medication.get('totalDoses', 0),
            'missedDoses': medication.get('missedDoses', 0),
            'lastTaken': medication.get('lastTaken'),
            'status': medication.get('status')
        }
        report['medications'].append(med_report)
    
    return report
