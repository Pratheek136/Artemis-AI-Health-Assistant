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
VITALS_TABLE = os.environ['VITALS_TABLE']
ALERTS_TOPIC = os.environ['ALERTS_TOPIC']

def lambda_handler(event, context):
    """
    Health monitoring Lambda function for real-time vitals processing
    and anomaly detection
    """
    try:
        logger.info(f"Processing health monitoring event: {json.dumps(event)}")
        
        # Parse the incoming event
        if 'Records' in event:
            # SQS/EventBridge trigger
            for record in event['Records']:
                process_health_data(record)
        else:
            # Direct API call
            process_health_data(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Health monitoring processed successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in health monitoring: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Health monitoring failed',
                'message': str(e)
            })
        }

def process_health_data(record):
    """Process individual health data record"""
    try:
        # Extract health data
        if 'body' in record:
            health_data = json.loads(record['body'])
        else:
            health_data = record
        
        user_id = health_data.get('userId')
        vitals = health_data.get('vitals', {})
        timestamp = health_data.get('timestamp', datetime.utcnow().isoformat())
        
        if not user_id:
            raise ValueError("userId is required")
        
        # Store vitals in DynamoDB
        store_vitals(user_id, vitals, timestamp)
        
        # Check for anomalies
        anomalies = detect_anomalies(vitals)
        
        if anomalies:
            # Send alert for critical anomalies
            send_health_alert(user_id, anomalies, vitals)
        
        # Update CloudWatch metrics
        update_cloudwatch_metrics(user_id, vitals)
        
        logger.info(f"Processed health data for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing health data: {str(e)}")
        raise

def store_vitals(user_id, vitals, timestamp):
    """Store vitals data in DynamoDB"""
    table = dynamodb.Table(VITALS_TABLE)
    
    # Convert float values to Decimal for DynamoDB
    vitals_decimal = {}
    for key, value in vitals.items():
        if isinstance(value, (int, float)):
            vitals_decimal[key] = Decimal(str(value))
        else:
            vitals_decimal[key] = value
    
    item = {
        'userId': user_id,
        'timestamp': timestamp,
        'vitals': vitals_decimal,
        'processedAt': datetime.utcnow().isoformat()
    }
    
    table.put_item(Item=item)
    logger.info(f"Stored vitals for user {user_id} at {timestamp}")

def detect_anomalies(vitals):
    """Detect health anomalies based on vitals"""
    anomalies = []
    
    # Heart rate anomalies
    heart_rate = vitals.get('heartRate')
    if heart_rate:
        if heart_rate < 40 or heart_rate > 200:
            anomalies.append({
                'type': 'CRITICAL_HEART_RATE',
                'value': heart_rate,
                'message': f'Critical heart rate detected: {heart_rate} bpm'
            })
        elif heart_rate < 50 or heart_rate > 150:
            anomalies.append({
                'type': 'WARNING_HEART_RATE',
                'value': heart_rate,
                'message': f'Abnormal heart rate: {heart_rate} bpm'
            })
    
    # Blood pressure anomalies
    systolic = vitals.get('systolicBP')
    diastolic = vitals.get('diastolicBP')
    if systolic and diastolic:
        if systolic > 180 or diastolic > 110:
            anomalies.append({
                'type': 'CRITICAL_BLOOD_PRESSURE',
                'value': f'{systolic}/{diastolic}',
                'message': f'Critical blood pressure: {systolic}/{diastolic} mmHg'
            })
        elif systolic > 140 or diastolic > 90:
            anomalies.append({
                'type': 'WARNING_BLOOD_PRESSURE',
                'value': f'{systolic}/{diastolic}',
                'message': f'High blood pressure: {systolic}/{diastolic} mmHg'
            })
    
    # Temperature anomalies
    temperature = vitals.get('temperature')
    if temperature:
        if temperature < 95 or temperature > 104:
            anomalies.append({
                'type': 'CRITICAL_TEMPERATURE',
                'value': temperature,
                'message': f'Critical temperature: {temperature}°F'
            })
        elif temperature < 97 or temperature > 100.4:
            anomalies.append({
                'type': 'WARNING_TEMPERATURE',
                'value': temperature,
                'message': f'Abnormal temperature: {temperature}°F'
            })
    
    # Oxygen saturation anomalies
    oxygen_sat = vitals.get('oxygenSaturation')
    if oxygen_sat:
        if oxygen_sat < 90:
            anomalies.append({
                'type': 'CRITICAL_OXYGEN_SATURATION',
                'value': oxygen_sat,
                'message': f'Critical oxygen saturation: {oxygen_sat}%'
            })
        elif oxygen_sat < 95:
            anomalies.append({
                'type': 'WARNING_OXYGEN_SATURATION',
                'value': oxygen_sat,
                'message': f'Low oxygen saturation: {oxygen_sat}%'
            })
    
    return anomalies

def send_health_alert(user_id, anomalies, vitals):
    """Send health alert via SNS"""
    try:
        critical_anomalies = [a for a in anomalies if a['type'].startswith('CRITICAL')]
        
        if critical_anomalies:
            alert_message = {
                'userId': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'CRITICAL',
                'anomalies': critical_anomalies,
                'vitals': vitals,
                'message': f'Critical health anomalies detected for user {user_id}'
            }
            
            sns.publish(
                TopicArn=ALERTS_TOPIC,
                Message=json.dumps(alert_message),
                Subject=f'CRITICAL: Health Alert for User {user_id}'
            )
            
            logger.warning(f"Sent critical health alert for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending health alert: {str(e)}")

def update_cloudwatch_metrics(user_id, vitals):
    """Update CloudWatch metrics for monitoring"""
    try:
        metrics = []
        
        # Heart rate metric
        if 'heartRate' in vitals:
            metrics.append({
                'MetricName': 'HeartRate',
                'Value': vitals['heartRate'],
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': user_id}
                ]
            })
        
        # Blood pressure metrics
        if 'systolicBP' in vitals:
            metrics.append({
                'MetricName': 'SystolicBP',
                'Value': vitals['systolicBP'],
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': user_id}
                ]
            })
        
        if 'diastolicBP' in vitals:
            metrics.append({
                'MetricName': 'DiastolicBP',
                'Value': vitals['diastolicBP'],
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': user_id}
                ]
            })
        
        # Temperature metric
        if 'temperature' in vitals:
            metrics.append({
                'MetricName': 'Temperature',
                'Value': vitals['temperature'],
                'Unit': 'None',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': user_id}
                ]
            })
        
        # Oxygen saturation metric
        if 'oxygenSaturation' in vitals:
            metrics.append({
                'MetricName': 'OxygenSaturation',
                'Value': vitals['oxygenSaturation'],
                'Unit': 'Percent',
                'Dimensions': [
                    {'Name': 'UserId', 'Value': user_id}
                ]
            })
        
        # Send metrics to CloudWatch
        for metric in metrics:
            cloudwatch.put_metric_data(
                Namespace='HealthAssistant/Vitals',
                MetricData=[metric]
            )
        
        logger.info(f"Updated CloudWatch metrics for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error updating CloudWatch metrics: {str(e)}")

def get_recent_vitals(user_id, hours=24):
    """Get recent vitals for a user"""
    table = dynamodb.Table(VITALS_TABLE)
    
    # Calculate time threshold
    threshold = datetime.utcnow() - timedelta(hours=hours)
    threshold_str = threshold.isoformat()
    
    response = table.query(
        KeyConditionExpression='userId = :userId AND #ts >= :threshold',
        ExpressionAttributeNames={'#ts': 'timestamp'},
        ExpressionAttributeValues={
            ':userId': user_id,
            ':threshold': threshold_str
        },
        ScanIndexForward=False,  # Most recent first
        Limit=100
    )
    
    return response.get('Items', [])

def calculate_health_trends(user_id, days=7):
    """Calculate health trends over specified days"""
    table = dynamodb.Table(VITALS_TABLE)
    
    # Calculate time threshold
    threshold = datetime.utcnow() - timedelta(days=days)
    threshold_str = threshold.isoformat()
    
    response = table.query(
        KeyConditionExpression='userId = :userId AND #ts >= :threshold',
        ExpressionAttributeNames={'#ts': 'timestamp'},
        ExpressionAttributeValues={
            ':userId': user_id,
            ':threshold': threshold_str
        },
        ScanIndexForward=True
    )
    
    vitals_list = response.get('Items', [])
    
    if not vitals_list:
        return {}
    
    # Calculate averages and trends
    trends = {}
    vitals_by_type = {}
    
    for item in vitals_list:
        vitals = item.get('vitals', {})
        for key, value in vitals.items():
            if key not in vitals_by_type:
                vitals_by_type[key] = []
            if isinstance(value, Decimal):
                vitals_by_type[key].append(float(value))
            else:
                vitals_by_type[key].append(value)
    
    for key, values in vitals_by_type.items():
        if values:
            trends[key] = {
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values),
                'trend': 'stable'  # Could implement trend calculation
            }
    
    return trends
