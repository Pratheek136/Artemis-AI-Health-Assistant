import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
ALERTS_TOPIC = os.environ['ALERTS_TOPIC']
NOTIFICATION_EMAIL = os.environ['NOTIFICATION_EMAIL']

def lambda_handler(event, context):
    """
    Emergency alerts Lambda function for detecting critical health
    emergencies and sending immediate notifications
    """
    try:
        logger.info(f"Processing emergency alerts event: {json.dumps(event)}")
        
        # Parse the incoming event
        if 'Records' in event:
            # SQS/EventBridge trigger
            for record in event['Records']:
                process_emergency_event(record)
        else:
            # Direct API call
            process_emergency_event(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Emergency alerts processed successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in emergency alerts: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Emergency alerts failed',
                'message': str(e)
            })
        }

def process_emergency_event(record):
    """Process individual emergency event"""
    try:
        # Extract emergency data
        if 'body' in record:
            emergency_data = json.loads(record['body'])
        else:
            emergency_data = record
        
        action = emergency_data.get('action')
        user_id = emergency_data.get('userId')
        
        if not user_id:
            raise ValueError("userId is required")
        
        if action == 'check_emergency':
            return check_emergency_conditions(user_id, emergency_data)
        elif action == 'send_emergency_alert':
            return send_emergency_alert(user_id, emergency_data)
        elif action == 'log_emergency':
            return log_emergency_event(user_id, emergency_data)
        elif action == 'get_emergency_history':
            return get_emergency_history(user_id, emergency_data)
        else:
            raise ValueError(f"Unknown action: {action}")
        
    except Exception as e:
        logger.error(f"Error processing emergency event: {str(e)}")
        raise

def check_emergency_conditions(user_id, emergency_data):
    """Check for emergency health conditions"""
    try:
        vitals = emergency_data.get('vitals', {})
        timestamp = emergency_data.get('timestamp', datetime.utcnow().isoformat())
        
        # Check for critical conditions
        critical_conditions = []
        
        # Heart rate emergency
        heart_rate = vitals.get('heartRate')
        if heart_rate:
            if heart_rate < 30 or heart_rate > 220:
                critical_conditions.append({
                    'type': 'CRITICAL_HEART_RATE',
                    'severity': 'CRITICAL',
                    'value': heart_rate,
                    'message': f'CRITICAL: Heart rate {heart_rate} bpm is life-threatening',
                    'action_required': 'IMMEDIATE_MEDICAL_ATTENTION'
                })
            elif heart_rate < 40 or heart_rate > 180:
                critical_conditions.append({
                    'type': 'EMERGENCY_HEART_RATE',
                    'severity': 'HIGH',
                    'value': heart_rate,
                    'message': f'EMERGENCY: Heart rate {heart_rate} bpm requires immediate attention',
                    'action_required': 'URGENT_MEDICAL_CARE'
                })
        
        # Blood pressure emergency
        systolic = vitals.get('systolicBP')
        diastolic = vitals.get('diastolicBP')
        if systolic and diastolic:
            if systolic > 200 or diastolic > 120:
                critical_conditions.append({
                    'type': 'CRITICAL_BLOOD_PRESSURE',
                    'severity': 'CRITICAL',
                    'value': f'{systolic}/{diastolic}',
                    'message': f'CRITICAL: Blood pressure {systolic}/{diastolic} mmHg is life-threatening',
                    'action_required': 'IMMEDIATE_MEDICAL_ATTENTION'
                })
            elif systolic > 180 or diastolic > 110:
                critical_conditions.append({
                    'type': 'EMERGENCY_BLOOD_PRESSURE',
                    'severity': 'HIGH',
                    'value': f'{systolic}/{diastolic}',
                    'message': f'EMERGENCY: Blood pressure {systolic}/{diastolic} mmHg requires immediate attention',
                    'action_required': 'URGENT_MEDICAL_CARE'
                })
        
        # Temperature emergency
        temperature = vitals.get('temperature')
        if temperature:
            if temperature < 90 or temperature > 107:
                critical_conditions.append({
                    'type': 'CRITICAL_TEMPERATURE',
                    'severity': 'CRITICAL',
                    'value': temperature,
                    'message': f'CRITICAL: Temperature {temperature}°F is life-threatening',
                    'action_required': 'IMMEDIATE_MEDICAL_ATTENTION'
                })
            elif temperature < 95 or temperature > 105:
                critical_conditions.append({
                    'type': 'EMERGENCY_TEMPERATURE',
                    'severity': 'HIGH',
                    'value': temperature,
                    'message': f'EMERGENCY: Temperature {temperature}°F requires immediate attention',
                    'action_required': 'URGENT_MEDICAL_CARE'
                })
        
        # Oxygen saturation emergency
        oxygen_sat = vitals.get('oxygenSaturation')
        if oxygen_sat:
            if oxygen_sat < 80:
                critical_conditions.append({
                    'type': 'CRITICAL_OXYGEN_SATURATION',
                    'severity': 'CRITICAL',
                    'value': oxygen_sat,
                    'message': f'CRITICAL: Oxygen saturation {oxygen_sat}% is life-threatening',
                    'action_required': 'IMMEDIATE_MEDICAL_ATTENTION'
                })
            elif oxygen_sat < 90:
                critical_conditions.append({
                    'type': 'EMERGENCY_OXYGEN_SATURATION',
                    'severity': 'HIGH',
                    'value': oxygen_sat,
                    'message': f'EMERGENCY: Oxygen saturation {oxygen_sat}% requires immediate attention',
                    'action_required': 'URGENT_MEDICAL_CARE'
                })
        
        # Check for fall detection
        if 'fallDetected' in vitals and vitals['fallDetected']:
            critical_conditions.append({
                'type': 'FALL_DETECTED',
                'severity': 'HIGH',
                'value': 'true',
                'message': 'EMERGENCY: Fall detected - immediate assistance may be needed',
                'action_required': 'CHECK_PATIENT_CONDITION'
            })
        
        # Check for panic button
        if 'panicButton' in vitals and vitals['panicButton']:
            critical_conditions.append({
                'type': 'PANIC_BUTTON_ACTIVATED',
                'severity': 'CRITICAL',
                'value': 'true',
                'message': 'CRITICAL: Panic button activated - immediate assistance required',
                'action_required': 'IMMEDIATE_EMERGENCY_RESPONSE'
            })
        
        # If critical conditions found, send alerts
        if critical_conditions:
            for condition in critical_conditions:
                send_emergency_alert(user_id, {
                    'condition': condition,
                    'vitals': vitals,
                    'timestamp': timestamp
                })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'userId': user_id,
                'timestamp': timestamp,
                'criticalConditions': critical_conditions,
                'emergencyDetected': len(critical_conditions) > 0
            })
        }
        
    except Exception as e:
        logger.error(f"Error checking emergency conditions: {str(e)}")
        raise

def send_emergency_alert(user_id, alert_data):
    """Send emergency alert via SNS"""
    try:
        condition = alert_data.get('condition', {})
        vitals = alert_data.get('vitals', {})
        timestamp = alert_data.get('timestamp', datetime.utcnow().isoformat())
        
        # Create emergency alert message
        alert_message = {
            'userId': user_id,
            'timestamp': timestamp,
            'condition': condition,
            'vitals': vitals,
            'alertType': 'EMERGENCY_HEALTH_ALERT',
            'severity': condition.get('severity', 'HIGH'),
            'actionRequired': condition.get('action_required', 'URGENT_MEDICAL_CARE'),
            'message': condition.get('message', 'Emergency health condition detected'),
            'location': alert_data.get('location', 'Unknown'),
            'contactInfo': alert_data.get('contactInfo', {})
        }
        
        # Send to SNS topic
        sns.publish(
            TopicArn=ALERTS_TOPIC,
            Message=json.dumps(alert_message),
            Subject=f'🚨 EMERGENCY: {condition.get("type", "Health Alert")} - User {user_id}'
        )
        
        # Send direct email notification
        send_direct_email_notification(user_id, alert_message)
        
        # Log emergency event
        log_emergency_event(user_id, {
            'action': 'log_emergency',
            'condition': condition,
            'vitals': vitals,
            'timestamp': timestamp,
            'alertSent': True
        })
        
        # Update CloudWatch metrics
        update_emergency_metrics(user_id, condition.get('type', 'UNKNOWN'))
        
        logger.critical(f"Emergency alert sent for user {user_id}: {condition.get('type')}")
        
    except Exception as e:
        logger.error(f"Error sending emergency alert: {str(e)}")
        raise

def send_direct_email_notification(user_id, alert_message):
    """Send direct email notification for critical emergencies"""
    try:
        condition = alert_message.get('condition', {})
        severity = condition.get('severity', 'HIGH')
        
        # Only send direct email for critical emergencies
        if severity == 'CRITICAL':
            email_subject = f"🚨 CRITICAL EMERGENCY - User {user_id}"
            email_body = f"""
CRITICAL HEALTH EMERGENCY DETECTED

User ID: {user_id}
Timestamp: {alert_message.get('timestamp')}
Condition: {condition.get('type')}
Severity: {severity}
Action Required: {condition.get('action_required')}

Message: {condition.get('message')}

Vitals Data:
{json.dumps(alert_message.get('vitals', {}), indent=2)}

IMMEDIATE ACTION REQUIRED:
- Contact emergency services if necessary
- Check on the patient immediately
- Follow emergency protocols

This is an automated alert from the Health Assistant System.
"""
            
            sns.publish(
                TopicArn=ALERTS_TOPIC,
                Message=email_body,
                Subject=email_subject
            )
            
            logger.critical(f"Direct email notification sent for critical emergency - User {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending direct email notification: {str(e)}")

def log_emergency_event(user_id, event_data):
    """Log emergency event for tracking and analysis"""
    try:
        # This would typically store in a DynamoDB table for emergency events
        # For now, we'll log to CloudWatch
        condition = event_data.get('condition', {})
        
        log_entry = {
            'userId': user_id,
            'timestamp': event_data.get('timestamp', datetime.utcnow().isoformat()),
            'conditionType': condition.get('type'),
            'severity': condition.get('severity'),
            'message': condition.get('message'),
            'vitals': event_data.get('vitals', {}),
            'alertSent': event_data.get('alertSent', False)
        }
        
        logger.info(f"Emergency event logged: {json.dumps(log_entry)}")
        
        # Update CloudWatch metrics
        update_emergency_metrics(user_id, condition.get('type', 'UNKNOWN'))
        
    except Exception as e:
        logger.error(f"Error logging emergency event: {str(e)}")

def get_emergency_history(user_id, request_data):
    """Get emergency history for a user"""
    try:
        days = request_data.get('days', 30)
        
        # This would typically query a DynamoDB table
        # For now, we'll return a placeholder response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'userId': user_id,
                'message': 'Emergency history retrieval not implemented',
                'note': 'This would typically query a DynamoDB table for emergency events'
            })
        }
        
    except Exception as e:
        logger.error(f"Error getting emergency history: {str(e)}")
        raise

def update_emergency_metrics(user_id, condition_type):
    """Update CloudWatch metrics for emergency events"""
    try:
        cloudwatch.put_metric_data(
            Namespace='HealthAssistant/Emergencies',
            MetricData=[{
                'MetricName': 'EmergencyEvent',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': user_id},
                    {'Name': 'ConditionType', 'Value': condition_type}
                ]
            }]
        )
        
        # Also update overall emergency count
        cloudwatch.put_metric_data(
            Namespace='HealthAssistant/Emergencies',
            MetricData=[{
                'MetricName': 'TotalEmergencies',
                'Value': 1,
                'Unit': 'Count'
            }]
        )
        
    except Exception as e:
        logger.error(f"Error updating emergency metrics: {str(e)}")

def check_continuous_monitoring(user_id, vitals_data):
    """Check for continuous monitoring alerts"""
    try:
        # Check for sustained abnormal values
        sustained_alerts = []
        
        # Heart rate sustained high/low
        if 'heartRate' in vitals_data:
            hr = vitals_data['heartRate']
            if hr > 120:  # Sustained high heart rate
                sustained_alerts.append({
                    'type': 'SUSTAINED_HIGH_HEART_RATE',
                    'severity': 'MEDIUM',
                    'message': f'Sustained high heart rate: {hr} bpm',
                    'action_required': 'MONITOR_CLOSELY'
                })
            elif hr < 50:  # Sustained low heart rate
                sustained_alerts.append({
                    'type': 'SUSTAINED_LOW_HEART_RATE',
                    'severity': 'MEDIUM',
                    'message': f'Sustained low heart rate: {hr} bpm',
                    'action_required': 'MONITOR_CLOSELY'
                })
        
        # Blood pressure sustained high
        if 'systolicBP' in vitals_data and 'diastolicBP' in vitals_data:
            systolic = vitals_data['systolicBP']
            diastolic = vitals_data['diastolicBP']
            
            if systolic > 140 or diastolic > 90:
                sustained_alerts.append({
                    'type': 'SUSTAINED_HIGH_BLOOD_PRESSURE',
                    'severity': 'MEDIUM',
                    'message': f'Sustained high blood pressure: {systolic}/{diastolic} mmHg',
                    'action_required': 'MONITOR_CLOSELY'
                })
        
        return sustained_alerts
        
    except Exception as e:
        logger.error(f"Error checking continuous monitoring: {str(e)}")
        return []

def create_emergency_contact_list(user_id):
    """Create emergency contact list for a user"""
    try:
        # This would typically retrieve from user profile
        # For now, return default contacts
        return {
            'primaryContact': {
                'name': 'Emergency Contact',
                'phone': '+1234567890',
                'email': NOTIFICATION_EMAIL,
                'relationship': 'Primary Emergency Contact'
            },
            'healthcareProvider': {
                'name': 'Primary Care Physician',
                'phone': '+1234567891',
                'email': 'doctor@example.com',
                'relationship': 'Healthcare Provider'
            },
            'emergencyServices': {
                'name': 'Emergency Services',
                'phone': '911',
                'email': None,
                'relationship': 'Emergency Services'
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating emergency contact list: {str(e)}")
        return {}

def validate_emergency_thresholds(vitals):
    """Validate emergency thresholds for vitals"""
    try:
        thresholds = {
            'heartRate': {'min': 30, 'max': 220, 'critical_min': 20, 'critical_max': 250},
            'systolicBP': {'min': 70, 'max': 250, 'critical_min': 50, 'critical_max': 300},
            'diastolicBP': {'min': 40, 'max': 150, 'critical_min': 30, 'critical_max': 200},
            'temperature': {'min': 90, 'max': 110, 'critical_min': 85, 'critical_max': 115},
            'oxygenSaturation': {'min': 70, 'max': 100, 'critical_min': 60, 'critical_max': 100}
        }
        
        violations = []
        
        for vital, value in vitals.items():
            if vital in thresholds and isinstance(value, (int, float)):
                threshold = thresholds[vital]
                
                if value < threshold['critical_min'] or value > threshold['critical_max']:
                    violations.append({
                        'vital': vital,
                        'value': value,
                        'severity': 'CRITICAL',
                        'message': f'{vital} value {value} is outside critical range'
                    })
                elif value < threshold['min'] or value > threshold['max']:
                    violations.append({
                        'vital': vital,
                        'value': value,
                        'severity': 'HIGH',
                        'message': f'{vital} value {value} is outside normal range'
                    })
        
        return violations
        
    except Exception as e:
        logger.error(f"Error validating emergency thresholds: {str(e)}")
        return []
