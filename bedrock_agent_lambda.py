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
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
lambda_client = boto3.client('lambda')

# Environment variables
VITALS_TABLE = os.environ['VITALS_TABLE']
MEDICATIONS_TABLE = os.environ['MEDICATIONS_TABLE']
PROFILES_TABLE = os.environ['PROFILES_TABLE']
ALERTS_TOPIC = os.environ['ALERTS_TOPIC']
REMINDERS_TOPIC = os.environ['REMINDERS_TOPIC']

# Bedrock model configuration
NOVA_MODEL_ID = "amazon.titan-text-express-v1:0:8k"  # using amazon. titan-lite-v1 as an example


def lambda_handler(event, context):
    """
    Bedrock Agent Lambda function for orchestrating health assistant
    conversations and decision-making using Amazon Nova models
    """
    logger.info(f"Processing Bedrock Agent event: {json.dumps(event)}")

    # This is the new logic to handle the REAL Bedrock Agent event
    api_path = event.get('apiPath')
    http_method = event.get('httpMethod')

    # Extract parameters
    user_id = None
    message = None
    session_id = event.get('sessionId', str(uuid.uuid4()))

    if http_method == 'POST' and 'requestBody' in event:
        try:
            body = json.loads(event['requestBody']['content']['application/json']['body'])
            user_id = body.get('userId')
            message = body.get('message', '')
        except Exception as e:
            logger.error(f"Error parsing POST body: {str(e)}")
    elif http_method == 'GET':
        params = event.get('parameters', [])
        for param in params:
            if param['name'] == 'userId':
                user_id = param['value']

    if not user_id:
        user_id = 'default-user' # Fallback for safety

    user_context = get_user_context(user_id)

    # Map apiPath to your existing functions
    try:
        response_body = {}
        if api_path == '/insights':
            response_body = handle_insights_request(user_id, message, user_context, session_id)
        elif api_path == '/recommendations':
            # You'll need to create a simple handler for this
            response_body = handle_insights_request(user_id, message, user_context, session_id) # Re-using insights
        elif api_path == '/medications' and http_method == 'GET':
            response_body = handle_medication_query(user_id, "Get my medications", user_context, session_id)
        elif api_path == '/vitals' and http_method == 'GET':
            response_body = handle_health_query(user_id, "Get my recent vitals", user_context, session_id)
        else:
            # Fallback to general chat
            response_body = handle_chat_request(user_id, message, user_context, session_id)

        # Format the response for Bedrock Agent
        response = {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', 'default'),
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(response_body['body']) # Pass the body from your original functions
                    }
                }
            }
        }
        return response

    except Exception as e:
        logger.error(f"Error in Bedrock Agent: {str(e)}")
        # ... (return an error response for the agent)

# --- (Keep all your other functions: handle_chat_request, handle_health_query, etc.) ---
def handle_chat_request(user_id, message, user_context, session_id):
    """Handle general chat conversation"""
    try:
        # Prepare context for Nova model
        system_prompt = create_health_assistant_system_prompt(user_context)
        
        # Create conversation history
        conversation_history = get_conversation_history(user_id, session_id)
        
        # Prepare the prompt for Nova
        nova_prompt = f"""
{system_prompt}

User: {message}

Please provide a helpful response as a health assistant. Consider the user's health context and provide appropriate guidance.
"""
        
        # Call Nova model
        response = call_nova_model(nova_prompt)
        
        # Save conversation
        save_conversation(user_id, session_id, message, response)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'userId': user_id,
                'sessionId': session_id,
                'response': response,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling chat request: {str(e)}")
        raise

def handle_health_query(user_id, message, user_context, session_id):
    """Handle health-specific queries"""
    try:
        # Get recent health data
        recent_vitals = get_recent_vitals(user_id, 7)  # Last 7 days
        
        # Prepare health-specific prompt
        health_prompt = f"""
You are a health assistant analyzing user health data. 

User Context:
- Age: {user_context.get('age', 'Unknown')}
- Medical Conditions: {user_context.get('medicalConditions', 'None reported')}
- Medications: {user_context.get('medications', 'None')}

Recent Health Data (last 7 days):
{format_vitals_for_prompt(recent_vitals)}

User Query: {message}

Please analyze the health data and provide insights, recommendations, or answer the user's question about their health.
"""
        
        # Call Nova model
        response = call_nova_model(health_prompt)
        
        # Save conversation
        save_conversation(user_id, session_id, message, response)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'userId': user_id,
                'sessionId': session_id,
                'response': response,
                'healthData': recent_vitals,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling health query: {str(e)}")
        raise

def handle_medication_query(user_id, message, user_context, session_id):
    """Handle medication-specific queries"""
    try:
        # Get user medications
        medications = get_user_medications(user_id)
        
        # Prepare medication-specific prompt
        medication_prompt = f"""
You are a health assistant helping with medication management.

User Context:
- Age: {user_context.get('age', 'Unknown')}
- Medical Conditions: {user_context.get('medicalConditions', 'None reported')}

Current Medications:
{format_medications_for_prompt(medications)}

User Query: {message}

Please help with medication-related questions, provide reminders, or offer guidance about medication management.
"""
        
        # Call Nova model
        response = call_nova_model(medication_prompt)
        
        # Save conversation
        save_conversation(user_id, session_id, message, response)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'userId': user_id,
                'sessionId': session_id,
                'response': response,
                'medications': medications,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling medication query: {str(e)}")
        raise

def handle_emergency_check(user_id, message, user_context, session_id):
    """Handle emergency health checks"""
    try:
        # Get current vitals
        current_vitals = get_current_vitals(user_id)
        
        # Check for emergency conditions
        emergency_conditions = check_emergency_conditions(current_vitals)
        
        # Prepare emergency prompt
        emergency_prompt = f"""
You are a health assistant monitoring for emergency conditions.

User Context:
- Age: {user_context.get('age', 'Unknown')}
- Medical Conditions: {user_context.get('medicalConditions', 'None reported')}
- Emergency Contacts: {user_context.get('emergencyContacts', 'None')}

Current Vitals:
{format_vitals_for_prompt([current_vitals]) if current_vitals else 'No current vitals available'}

Emergency Conditions Detected:
{emergency_conditions}

User Query: {message}

Please assess the situation and provide appropriate emergency guidance. If critical conditions are detected, recommend immediate medical attention.
"""
        
        # Call Nova model
        response = call_nova_model(emergency_prompt)
        
        # If critical conditions detected, trigger emergency alerts
        if emergency_conditions:
            trigger_emergency_alert(user_id, emergency_conditions, current_vitals)
        
        # Save conversation
        save_conversation(user_id, session_id, message, response)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'userId': user_id,
                'sessionId': session_id,
                'response': response,
                'emergencyConditions': emergency_conditions,
                'alertTriggered': len(emergency_conditions) > 0,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling emergency check: {str(e)}")
        raise

def handle_insights_request(user_id, message, user_context, session_id):
    """Handle health insights requests"""
    try:
        # Get health insights
        insights = get_health_insights(user_id)
        
        # Prepare insights prompt
        insights_prompt = f"""
You are a health assistant providing personalized health insights.

User Context:
- Age: {user_context.get('age', 'Unknown')}
- Medical Conditions: {user_context.get('medicalConditions', 'None reported')}
- Health Goals: {user_context.get('healthGoals', 'None specified')}

Health Insights:
{insights}

User Query: {message}

Please provide personalized health insights, recommendations, and guidance based on the user's health data and context.
"""
        
        # Call Nova model
        response = call_nova_model(insights_prompt)
        
        # Save conversation
        save_conversation(user_id, session_id, message, response)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'userId': user_id,
                'sessionId': session_id,
                'response': response,
                'insights': insights,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling insights request: {str(e)}")
        raise

def handle_general_request(user_id, message, user_context, session_id):
    """Handle general requests"""
    try:
        # Prepare general prompt
        general_prompt = f"""
You are a helpful health assistant. 

User Context:
- Age: {user_context.get('age', 'Unknown')}
- Medical Conditions: {user_context.get('medicalConditions', 'None reported')}

User Query: {message}

Please provide helpful information and guidance. If the query is health-related, provide appropriate medical guidance while reminding the user to consult with healthcare professionals for medical advice.
"""
        
        # Call Nova model
        response = call_nova_model(general_prompt)
        
        # Save conversation
        save_conversation(user_id, session_id, message, response)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'userId': user_id,
                'sessionId': session_id,
                'response': response,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling general request: {str(e)}")
        raise

def call_nova_model(prompt):
    """Call Amazon Nova model via Bedrock"""
    try:
        # Prepare the request body for Nova
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=NOVA_MODEL_ID,
            body=json.dumps(request_body),
            contentType="application/json"
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        # Extract the generated text
        if 'content' in response_body and len(response_body['content']) > 0:
            generated_text = response_body['content'][0]['text']
        else:
            generated_text = "I apologize, but I'm having trouble processing your request. Please try again."
        
        logger.info(f"Nova model response generated successfully")
        return generated_text
        
    except Exception as e:
        logger.error(f"Error calling Nova model: {str(e)}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again later."

def create_health_assistant_system_prompt(user_context):
    """Create system prompt for health assistant"""
    return f"""
You are an AI health assistant powered by Amazon Nova. Your role is to provide helpful health information and guidance while maintaining appropriate medical boundaries.

Key Guidelines:
1. Always remind users to consult with healthcare professionals for medical advice
2. Provide general health information and lifestyle recommendations
3. Help users understand their health data and trends
4. Assist with medication reminders and adherence
5. Monitor for emergency conditions and provide appropriate guidance
6. Maintain patient privacy and confidentiality
7. Be empathetic and supportive in your responses

User Context:
- Age: {user_context.get('age', 'Unknown')}
- Medical Conditions: {user_context.get('medicalConditions', 'None reported')}
- Current Medications: {user_context.get('medications', 'None')}
- Health Goals: {user_context.get('healthGoals', 'None specified')}

Remember: You are not a replacement for professional medical care. Always encourage users to seek professional medical advice for serious health concerns.
"""

def get_user_context(user_id):
    """Get user context from profile"""
    try:
        table = dynamodb.Table(PROFILES_TABLE)
        response = table.get_item(Key={'userId': user_id})
        return response.get('Item', {})
    except Exception as e:
        logger.error(f"Error getting user context: {str(e)}")
        return {}

def get_recent_vitals(user_id, days=7):
    """Get recent vitals for a user"""
    try:
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
            ScanIndexForward=False,
            Limit=50
        )
        
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting recent vitals: {str(e)}")
        return []

def get_current_vitals(user_id):
    """Get most recent vitals for a user"""
    try:
        table = dynamodb.Table(VITALS_TABLE)
        
        response = table.query(
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id},
            ScanIndexForward=False,
            Limit=1
        )
        
        items = response.get('Items', [])
        return items[0] if items else None
    except Exception as e:
        logger.error(f"Error getting current vitals: {str(e)}")
        return None

def get_user_medications(user_id):
    """Get user medications"""
    try:
        table = dynamodb.Table(MEDICATIONS_TABLE)
        
        response = table.query(
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id}
        )
        
        medications = response.get('Items', [])
        return [m for m in medications if m.get('status') == 'active']
    except Exception as e:
        logger.error(f"Error getting user medications: {str(e)}")
        return []

def get_health_insights(user_id):
    """Get health insights for a user"""
    try:
        # Call health insights Lambda function
        response = lambda_client.invoke(
            FunctionName=os.environ.get('HEALTH_INSIGHTS_FUNCTION', 'health-insights'),
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'generate_insights',
                'userId': user_id,
                'days': 30
            })
        )
        
        result = json.loads(response['Payload'].read())
        return result.get('body', {})
    except Exception as e:
        logger.error(f"Error getting health insights: {str(e)}")
        return {}

def check_emergency_conditions(vitals):
    """Check for emergency conditions in vitals"""
    if not vitals:
        return []
    
    vitals_data = vitals.get('vitals', {})
    conditions = []
    
    # Heart rate emergency
    heart_rate = vitals_data.get('heartRate')
    if heart_rate and (heart_rate < 40 or heart_rate > 180):
        conditions.append(f"Abnormal heart rate: {heart_rate} bpm")
    
    # Blood pressure emergency
    systolic = vitals_data.get('systolicBP')
    diastolic = vitals_data.get('diastolicBP')
    if systolic and diastolic and (systolic > 180 or diastolic > 110):
        conditions.append(f"High blood pressure: {systolic}/{diastolic} mmHg")
    
    # Temperature emergency
    temperature = vitals_data.get('temperature')
    if temperature and (temperature < 95 or temperature > 104):
        conditions.append(f"Abnormal temperature: {temperature}°F")
    
    # Oxygen saturation emergency
    oxygen_sat = vitals_data.get('oxygenSaturation')
    if oxygen_sat and oxygen_sat < 90:
        conditions.append(f"Low oxygen saturation: {oxygen_sat}%")
    
    return conditions

def trigger_emergency_alert(user_id, conditions, vitals):
    """Trigger emergency alert"""
    try:
        # Call emergency alerts Lambda function
        lambda_client.invoke(
            FunctionName=os.environ.get('EMERGENCY_ALERTS_FUNCTION', 'emergency-alerts'),
            InvocationType='Event',  # Async invocation
            Payload=json.dumps({
                'action': 'send_emergency_alert',
                'userId': user_id,
                'condition': {
                    'type': 'MULTIPLE_EMERGENCY_CONDITIONS',
                    'severity': 'HIGH',
                    'message': f"Multiple emergency conditions detected: {', '.join(conditions)}",
                    'action_required': 'URGENT_MEDICAL_CARE'
                },
                'vitals': vitals,
                'timestamp': datetime.utcnow().isoformat()
            })
        )
        
        logger.warning(f"Emergency alert triggered for user {user_id}")
    except Exception as e:
        logger.error(f"Error triggering emergency alert: {str(e)}")

def format_vitals_for_prompt(vitals_list):
    """Format vitals data for prompt"""
    if not vitals_list:
        return "No recent vitals data available"
    
    formatted = []
    for vitals in vitals_list[-5:]:  # Last 5 readings
        timestamp = vitals.get('timestamp', 'Unknown time')
        vitals_data = vitals.get('vitals', {})
        
        vitals_str = f"Time: {timestamp}\n"
        for key, value in vitals_data.items():
            if isinstance(value, Decimal):
                vitals_str += f"  {key}: {float(value)}\n"
            else:
                vitals_str += f"  {key}: {value}\n"
        
        formatted.append(vitals_str)
    
    return "\n".join(formatted)

def format_medications_for_prompt(medications):
    """Format medications data for prompt"""
    if not medications:
        return "No current medications"
    
    formatted = []
    for med in medications:
        med_str = f"Medication: {med.get('medicationName', 'Unknown')}\n"
        med_str += f"  Dosage: {med.get('dosage', 'Unknown')}\n"
        med_str += f"  Frequency: {med.get('frequency', 'Unknown')}\n"
        med_str += f"  Last Taken: {med.get('lastTaken', 'Never')}\n"
        med_str += f"  Adherence Rate: {med.get('adherenceRate', 0)}%\n"
        formatted.append(med_str)
    
    return "\n".join(formatted)

def get_conversation_history(user_id, session_id):
    """Get conversation history for a session"""
    try:
        # This would typically query a conversations table
        # For now, return empty history
        return []
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        return []

def save_conversation(user_id, session_id, user_message, assistant_response):
    """Save conversation to database"""
    try:
        # This would typically save to a conversations table
        # For now, just log the conversation
        logger.info(f"Conversation saved - User: {user_id}, Session: {session_id}")
        logger.info(f"User: {user_message}")
        logger.info(f"Assistant: {assistant_response}")
    except Exception as e:
        logger.error(f"Error saving conversation: {str(e)}")

def analyze_user_intent(message):
    """Analyze user intent from message"""
    try:
        # Simple intent analysis based on keywords
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['medication', 'medicine', 'pill', 'dose']):
            return 'medication'
        elif any(word in message_lower for word in ['emergency', 'urgent', 'help', 'pain']):
            return 'emergency'
        elif any(word in message_lower for word in ['health', 'vitals', 'blood pressure', 'heart rate']):
            return 'health'
        elif any(word in message_lower for word in ['insights', 'recommendations', 'advice']):
            return 'insights'
        else:
            return 'general'
    except Exception as e:
        logger.error(f"Error analyzing user intent: {str(e)}")
        return 'general'

def validate_health_data(vitals):
    """Validate health data before processing"""
    try:
        if not vitals or 'vitals' not in vitals:
            return False
        
        vitals_data = vitals['vitals']
        
        # Check for required fields
        required_fields = ['heartRate', 'systolicBP', 'diastolicBP', 'temperature']
        for field in required_fields:
            if field not in vitals_data:
                return False
        
        # Validate ranges
        heart_rate = vitals_data.get('heartRate')
        if heart_rate and (heart_rate < 20 or heart_rate > 300):
            return False
        
        systolic = vitals_data.get('systolicBP')
        if systolic and (systolic < 50 or systolic > 300):
            return False
        
        diastolic = vitals_data.get('diastolicBP')
        if diastolic and (diastolic < 30 or diastolic > 200):
            return False
        
        temperature = vitals_data.get('temperature')
        if temperature and (temperature < 80 or temperature > 120):
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating health data: {str(e)}")
        return False
