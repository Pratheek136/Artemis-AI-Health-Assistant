import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import statistics
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

# Environment variables
VITALS_TABLE = os.environ['VITALS_TABLE']
PROFILES_TABLE = os.environ['PROFILES_TABLE']

def lambda_handler(event, context):
    """
    Health insights Lambda function for generating personalized
    health recommendations and insights
    """
    try:
        logger.info(f"Processing health insights event: {json.dumps(event)}")
        
        # Parse the incoming event
        if 'Records' in event:
            # SQS/EventBridge trigger
            for record in event['Records']:
                process_insights_request(record)
        else:
            # Direct API call
            return process_insights_request(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Health insights processed successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in health insights: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Health insights failed',
                'message': str(e)
            })
        }

def process_insights_request(record):
    """Process individual insights request"""
    try:
        # Extract request data
        if 'body' in record:
            request_data = json.loads(record['body'])
        else:
            request_data = record
        
        action = request_data.get('action')
        user_id = request_data.get('userId')
        
        if not user_id:
            raise ValueError("userId is required")
        
        if action == 'generate_insights':
            return generate_health_insights(user_id, request_data)
        elif action == 'get_recommendations':
            return get_health_recommendations(user_id, request_data)
        elif action == 'analyze_trends':
            return analyze_health_trends(user_id, request_data)
        elif action == 'get_health_summary':
            return get_health_summary(user_id, request_data)
        else:
            raise ValueError(f"Unknown action: {action}")
        
    except Exception as e:
        logger.error(f"Error processing insights request: {str(e)}")
        raise

def generate_health_insights(user_id, request_data):
    """Generate comprehensive health insights for a user"""
    try:
        # Get user profile
        user_profile = get_user_profile(user_id)
        
        # Get recent vitals data
        days = request_data.get('days', 30)
        vitals_data = get_recent_vitals(user_id, days)
        
        if not vitals_data:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No health data available for insights',
                    'userId': user_id
                })
            }
        
        # Analyze vitals trends
        trends = analyze_vitals_trends(vitals_data)
        
        # Generate insights based on trends and profile
        insights = []
        
        # Heart rate insights
        if 'heartRate' in trends:
            hr_insight = generate_heart_rate_insight(trends['heartRate'], user_profile)
            if hr_insight:
                insights.append(hr_insight)
        
        # Blood pressure insights
        if 'systolicBP' in trends and 'diastolicBP' in trends:
            bp_insight = generate_blood_pressure_insight(trends, user_profile)
            if bp_insight:
                insights.append(bp_insight)
        
        # Temperature insights
        if 'temperature' in trends:
            temp_insight = generate_temperature_insight(trends['temperature'], user_profile)
            if temp_insight:
                insights.append(temp_insight)
        
        # Oxygen saturation insights
        if 'oxygenSaturation' in trends:
            o2_insight = generate_oxygen_insight(trends['oxygenSaturation'], user_profile)
            if o2_insight:
                insights.append(o2_insight)
        
        # Overall health score
        health_score = calculate_health_score(trends, user_profile)
        
        # Generate recommendations
        recommendations = generate_recommendations(trends, user_profile, health_score)
        
        result = {
            'userId': user_id,
            'analysisDate': datetime.utcnow().isoformat(),
            'periodDays': days,
            'healthScore': health_score,
            'insights': insights,
            'recommendations': recommendations,
            'trends': trends
        }
        
        # Store insights in user profile
        store_insights(user_id, result)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error generating health insights: {str(e)}")
        raise

def get_health_recommendations(user_id, request_data):
    """Get personalized health recommendations"""
    try:
        user_profile = get_user_profile(user_id)
        days = request_data.get('days', 30)
        vitals_data = get_recent_vitals(user_id, days)
        
        if not vitals_data:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No health data available for recommendations',
                    'userId': user_id
                })
            }
        
        trends = analyze_vitals_trends(vitals_data)
        health_score = calculate_health_score(trends, user_profile)
        recommendations = generate_recommendations(trends, user_profile, health_score)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'userId': user_id,
                'recommendations': recommendations,
                'healthScore': health_score,
                'generatedAt': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error getting health recommendations: {str(e)}")
        raise

def analyze_health_trends(user_id, request_data):
    """Analyze health trends over time"""
    try:
        days = request_data.get('days', 30)
        vitals_data = get_recent_vitals(user_id, days)
        
        if not vitals_data:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No health data available for trend analysis',
                    'userId': user_id
                })
            }
        
        trends = analyze_vitals_trends(vitals_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'userId': user_id,
                'trends': trends,
                'analysisDate': datetime.utcnow().isoformat(),
                'periodDays': days
            })
        }
        
    except Exception as e:
        logger.error(f"Error analyzing health trends: {str(e)}")
        raise

def get_health_summary(user_id, request_data):
    """Get comprehensive health summary"""
    try:
        user_profile = get_user_profile(user_id)
        days = request_data.get('days', 30)
        vitals_data = get_recent_vitals(user_id, days)
        
        if not vitals_data:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No health data available for summary',
                    'userId': user_id
                })
            }
        
        trends = analyze_vitals_trends(vitals_data)
        health_score = calculate_health_score(trends, user_profile)
        
        # Get recent insights
        recent_insights = get_recent_insights(user_id, 7)
        
        summary = {
            'userId': user_id,
            'summaryDate': datetime.utcnow().isoformat(),
            'periodDays': days,
            'healthScore': health_score,
            'keyMetrics': {
                'heartRate': trends.get('heartRate', {}),
                'bloodPressure': {
                    'systolic': trends.get('systolicBP', {}),
                    'diastolic': trends.get('diastolicBP', {})
                },
                'temperature': trends.get('temperature', {}),
                'oxygenSaturation': trends.get('oxygenSaturation', {})
            },
            'recentInsights': recent_insights,
            'overallStatus': get_overall_health_status(health_score, trends)
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(summary)
        }
        
    except Exception as e:
        logger.error(f"Error getting health summary: {str(e)}")
        raise

def get_user_profile(user_id):
    """Get user profile from DynamoDB"""
    table = dynamodb.Table(PROFILES_TABLE)
    
    response = table.get_item(Key={'userId': user_id})
    return response.get('Item', {})

def get_recent_vitals(user_id, days):
    """Get recent vitals data for a user"""
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
    
    return response.get('Items', [])

def analyze_vitals_trends(vitals_data):
    """Analyze trends in vitals data"""
    trends = {}
    
    # Group vitals by type
    vitals_by_type = {}
    for item in vitals_data:
        vitals = item.get('vitals', {})
        for key, value in vitals.items():
            if key not in vitals_by_type:
                vitals_by_type[key] = []
            if isinstance(value, Decimal):
                vitals_by_type[key].append(float(value))
            else:
                vitals_by_type[key].append(value)
    
    # Calculate statistics for each vital type
    for key, values in vitals_by_type.items():
        if values:
            trends[key] = {
                'average': statistics.mean(values),
                'median': statistics.median(values),
                'min': min(values),
                'max': max(values),
                'count': len(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                'trend': calculate_trend_direction(values)
            }
    
    return trends

def calculate_trend_direction(values):
    """Calculate trend direction (increasing, decreasing, stable)"""
    if len(values) < 2:
        return 'stable'
    
    # Simple linear trend calculation
    n = len(values)
    x = list(range(n))
    y = values
    
    # Calculate slope
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return 'stable'
    
    slope = numerator / denominator
    
    if slope > 0.1:
        return 'increasing'
    elif slope < -0.1:
        return 'decreasing'
    else:
        return 'stable'

def generate_heart_rate_insight(hr_trend, user_profile):
    """Generate heart rate insight"""
    age = user_profile.get('age', 30)
    avg_hr = hr_trend.get('average', 0)
    
    if avg_hr == 0:
        return None
    
    # Normal heart rate ranges by age
    if age < 20:
        normal_range = (60, 100)
    elif age < 40:
        normal_range = (60, 95)
    elif age < 60:
        normal_range = (60, 90)
    else:
        normal_range = (60, 85)
    
    if avg_hr < normal_range[0]:
        return {
            'type': 'heart_rate',
            'severity': 'warning',
            'message': f'Your average heart rate ({avg_hr:.1f} bpm) is below the normal range for your age ({normal_range[0]}-{normal_range[1]} bpm).',
            'recommendation': 'Consider consulting with your healthcare provider about your low heart rate.'
        }
    elif avg_hr > normal_range[1]:
        return {
            'type': 'heart_rate',
            'severity': 'warning',
            'message': f'Your average heart rate ({avg_hr:.1f} bpm) is above the normal range for your age ({normal_range[0]}-{normal_range[1]} bpm).',
            'recommendation': 'Consider lifestyle changes like regular exercise, stress management, and consulting with your healthcare provider.'
        }
    else:
        return {
            'type': 'heart_rate',
            'severity': 'info',
            'message': f'Your average heart rate ({avg_hr:.1f} bpm) is within the normal range for your age.',
            'recommendation': 'Continue maintaining your current lifestyle habits.'
        }

def generate_blood_pressure_insight(bp_trends, user_profile):
    """Generate blood pressure insight"""
    systolic_avg = bp_trends.get('systolicBP', {}).get('average', 0)
    diastolic_avg = bp_trends.get('diastolicBP', {}).get('average', 0)
    
    if systolic_avg == 0 or diastolic_avg == 0:
        return None
    
    # Blood pressure categories
    if systolic_avg < 120 and diastolic_avg < 80:
        category = 'Normal'
        severity = 'info'
        recommendation = 'Your blood pressure is in the normal range. Continue maintaining a healthy lifestyle.'
    elif systolic_avg < 130 and diastolic_avg < 80:
        category = 'Elevated'
        severity = 'warning'
        recommendation = 'Your blood pressure is elevated. Consider lifestyle changes like reducing sodium intake and increasing physical activity.'
    elif systolic_avg < 140 or diastolic_avg < 90:
        category = 'High Blood Pressure Stage 1'
        severity = 'warning'
        recommendation = 'You have Stage 1 high blood pressure. Consult with your healthcare provider about lifestyle changes and possible medication.'
    else:
        category = 'High Blood Pressure Stage 2'
        severity = 'critical'
        recommendation = 'You have Stage 2 high blood pressure. Immediate consultation with your healthcare provider is recommended.'
    
    return {
        'type': 'blood_pressure',
        'severity': severity,
        'message': f'Your average blood pressure is {systolic_avg:.1f}/{diastolic_avg:.1f} mmHg ({category}).',
        'recommendation': recommendation
    }

def generate_temperature_insight(temp_trend, user_profile):
    """Generate temperature insight"""
    avg_temp = temp_trend.get('average', 0)
    
    if avg_temp == 0:
        return None
    
    if avg_temp < 97.0:
        return {
            'type': 'temperature',
            'severity': 'warning',
            'message': f'Your average temperature ({avg_temp:.1f}°F) is below normal (97-99°F).',
            'recommendation': 'Monitor for symptoms of hypothermia or other conditions. Consult with your healthcare provider if this persists.'
        }
    elif avg_temp > 100.4:
        return {
            'type': 'temperature',
            'severity': 'warning',
            'message': f'Your average temperature ({avg_temp:.1f}°F) is above normal (97-99°F).',
            'recommendation': 'Monitor for fever symptoms. Rest, stay hydrated, and consult with your healthcare provider if symptoms worsen.'
        }
    else:
        return {
            'type': 'temperature',
            'severity': 'info',
            'message': f'Your average temperature ({avg_temp:.1f}°F) is within the normal range.',
            'recommendation': 'Your body temperature is normal. Continue monitoring for any changes.'
        }

def generate_oxygen_insight(o2_trend, user_profile):
    """Generate oxygen saturation insight"""
    avg_o2 = o2_trend.get('average', 0)
    
    if avg_o2 == 0:
        return None
    
    if avg_o2 < 90:
        return {
            'type': 'oxygen_saturation',
            'severity': 'critical',
            'message': f'Your average oxygen saturation ({avg_o2:.1f}%) is critically low (normal: 95-100%).',
            'recommendation': 'Seek immediate medical attention. Low oxygen saturation can be life-threatening.'
        }
    elif avg_o2 < 95:
        return {
            'type': 'oxygen_saturation',
            'severity': 'warning',
            'message': f'Your average oxygen saturation ({avg_o2:.1f}%) is below normal (95-100%).',
            'recommendation': 'Monitor your breathing and consult with your healthcare provider. Consider factors like altitude or respiratory conditions.'
        }
    else:
        return {
            'type': 'oxygen_saturation',
            'severity': 'info',
            'message': f'Your average oxygen saturation ({avg_o2:.1f}%) is within the normal range.',
            'recommendation': 'Your oxygen levels are healthy. Continue monitoring for any changes.'
        }

def calculate_health_score(trends, user_profile):
    """Calculate overall health score (0-100)"""
    score = 100.0
    
    # Heart rate score
    if 'heartRate' in trends:
        hr_avg = trends['heartRate']['average']
        age = user_profile.get('age', 30)
        
        if age < 20:
            normal_range = (60, 100)
        elif age < 40:
            normal_range = (60, 95)
        elif age < 60:
            normal_range = (60, 90)
        else:
            normal_range = (60, 85)
        
        if hr_avg < normal_range[0] or hr_avg > normal_range[1]:
            score -= 15
    
    # Blood pressure score
    if 'systolicBP' in trends and 'diastolicBP' in trends:
        systolic = trends['systolicBP']['average']
        diastolic = trends['diastolicBP']['average']
        
        if systolic >= 140 or diastolic >= 90:
            score -= 20
        elif systolic >= 130 or diastolic >= 80:
            score -= 10
    
    # Temperature score
    if 'temperature' in trends:
        temp = trends['temperature']['average']
        if temp < 97.0 or temp > 100.4:
            score -= 10
    
    # Oxygen saturation score
    if 'oxygenSaturation' in trends:
        o2 = trends['oxygenSaturation']['average']
        if o2 < 90:
            score -= 25
        elif o2 < 95:
            score -= 15
    
    return max(0, min(100, score))

def generate_recommendations(trends, user_profile, health_score):
    """Generate personalized health recommendations"""
    recommendations = []
    
    # General recommendations based on health score
    if health_score < 70:
        recommendations.append({
            'type': 'general',
            'priority': 'high',
            'title': 'Overall Health Improvement',
            'description': 'Your health metrics indicate areas for improvement. Consider consulting with your healthcare provider for a comprehensive health assessment.'
        })
    
    # Heart rate recommendations
    if 'heartRate' in trends:
        hr_avg = trends['heartRate']['average']
        if hr_avg > 100:
            recommendations.append({
                'type': 'cardiovascular',
                'priority': 'medium',
                'title': 'Heart Rate Management',
                'description': 'Your heart rate is elevated. Consider regular cardiovascular exercise, stress reduction techniques, and maintaining a healthy weight.'
            })
    
    # Blood pressure recommendations
    if 'systolicBP' in trends and 'diastolicBP' in trends:
        systolic = trends['systolicBP']['average']
        diastolic = trends['diastolicBP']['average']
        
        if systolic >= 130 or diastolic >= 80:
            recommendations.append({
                'type': 'cardiovascular',
                'priority': 'high',
                'title': 'Blood Pressure Management',
                'description': 'Your blood pressure is elevated. Focus on reducing sodium intake, regular exercise, weight management, and stress reduction.'
            })
    
    # Temperature recommendations
    if 'temperature' in trends:
        temp = trends['temperature']['average']
        if temp > 100.4:
            recommendations.append({
                'type': 'general',
                'priority': 'medium',
                'title': 'Fever Management',
                'description': 'You may have a fever. Rest, stay hydrated, and monitor your symptoms. Consult with your healthcare provider if symptoms persist.'
            })
    
    # Oxygen saturation recommendations
    if 'oxygenSaturation' in trends:
        o2 = trends['oxygenSaturation']['average']
        if o2 < 95:
            recommendations.append({
                'type': 'respiratory',
                'priority': 'high',
                'title': 'Oxygen Level Monitoring',
                'description': 'Your oxygen saturation is below normal. Monitor your breathing, avoid smoking, and consult with your healthcare provider.'
            })
    
    return recommendations

def store_insights(user_id, insights_data):
    """Store insights in user profile"""
    table = dynamodb.Table(PROFILES_TABLE)
    
    # Get existing profile
    response = table.get_item(Key={'userId': user_id})
    profile = response.get('Item', {})
    
    # Update with new insights
    profile['userId'] = user_id
    profile['lastInsights'] = insights_data
    profile['lastInsightsDate'] = datetime.utcnow().isoformat()
    
    # Store updated profile
    table.put_item(Item=profile)

def get_recent_insights(user_id, days):
    """Get recent insights for a user"""
    profile = get_user_profile(user_id)
    last_insights = profile.get('lastInsights', {})
    
    if not last_insights:
        return []
    
    # Check if insights are recent enough
    insights_date = last_insights.get('analysisDate')
    if insights_date:
        insights_dt = datetime.fromisoformat(insights_date.replace('Z', '+00:00'))
        if datetime.utcnow() - insights_dt <= timedelta(days=days):
            return last_insights.get('insights', [])
    
    return []

def get_overall_health_status(health_score, trends):
    """Get overall health status based on score and trends"""
    if health_score >= 90:
        return 'Excellent'
    elif health_score >= 80:
        return 'Good'
    elif health_score >= 70:
        return 'Fair'
    elif health_score >= 60:
        return 'Poor'
    else:
        return 'Critical'
