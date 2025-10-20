# AI Health Assistant

A comprehensive, HIPAA-compliant AI-powered health monitoring and management system built on AWS with Amazon Bedrock Nova models for intelligent health insights and decision-making.

##  Overview

The AI Health Assistant is an autonomous health monitoring system that provides real-time health monitoring, intelligent medication management, personalized health insights, and emergency detection capabilities. It leverages Amazon Nova models through AWS Bedrock AgentCore for natural language health consultations and decision-making.

### Key Features

- **Real-time Health Monitoring**: Continuous monitoring of vital signs with anomaly detection
- **Intelligent Medication Management**: Automated reminders, adherence tracking, and dosage management
- **AI-Powered Health Insights**: Personalized recommendations using Amazon Nova models
- **Emergency Detection**: Automated alerts for critical health conditions
- **Natural Language Interface**: Chat with AI assistant for health consultations
- **HIPAA Compliance**: End-to-end encryption and audit logging
- **Responsive Web Dashboard**: Modern, mobile-friendly interface

## Architecture

### Core Components

1. **LLM & Reasoning Engine**
   - Amazon Titan models hosted on AWS Bedrock
   - Bedrock AgentCore for workflow orchestration
   - Natural language processing for health consultations

2. **AWS Services Integration**
   - **AWS Lambda**: 4 serverless functions for health processing
   - **Amazon DynamoDB**: HIPAA-compliant encrypted data storage (3 tables)
   - **Amazon SNS**: Notifications and medication reminders
   - **AWS IoT Core**: Real-time health data ingestion
   - **Amazon CloudWatch**: Monitoring, logging, and alerts

3. **Autonomous Features**
   - Real-time health monitoring and anomaly detection
   - Intelligent medication management with reminders
   - Personalized health insights and recommendations
   - Emergency detection and automated alerts

4. **Web Dashboard**
   - Responsive React/Next.js interface
   - Real-time vitals display
   - AI chat interface
   - Settings and profile management

## Prerequisites

Before deploying the AI Health Assistant, ensure you have:

- **AWS Account** with appropriate permissions
- **AWS CLI** installed and configured
- **Python 3.11+** for testing
- **Node.js 18+** (optional, for local development)
- **Valid email address** for notifications

### Required AWS Permissions

Your AWS user/role needs permissions for:
- CloudFormation (full access)
- Lambda (full access)
- DynamoDB (full access)
- SNS (full access)
- Bedrock (full access)
- IoT Core (full access)
- CloudWatch (full access)
- S3 (full access)
- IAM (create roles and policies)
- KMS (create and manage keys)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-health-assistant
chmod +x deploy.sh
chmod +x test_agent.py
```

### 2. Deploy Infrastructure

```bash
# Deploy with your notification email
./deploy.sh admin@yourdomain.com

# Or specify environment and AWS profile
./deploy.sh admin@yourdomain.com prod my-aws-profile
```

The deployment script will:
- Create all AWS resources via CloudFormation
- Package and deploy Lambda functions
- Set up Bedrock Agent with Nova models
- Deploy the web dashboard
- Run comprehensive tests

### 3. Access the System

After deployment, you'll receive:
- **Web Dashboard URL**: S3-hosted static website
- **API Endpoint**: For health data ingestion
- **CloudFormation Outputs**: All resource details

### 4. Test the System

```bash
# Run comprehensive test suite
python3 test_agent.py

# Test with specific stack name
python3 test_agent.py my-stack-name
```

##  Project Structure

```
ai-health-assistant/
├── README.md                           # This file
├── infrastructure.yaml                 # CloudFormation template
├── deploy.sh                          # Automated deployment script
├── test_agent.py                      # Comprehensive test suite
├── bedrock_agent_lambda.py            # Bedrock Agent orchestrator
├── health_monitoring_lambda.py        # Health monitoring function
├── medication_management_lambda.py    # Medication management function
├── health_insights_lambda.py          # Health insights function
├── emergency_alerts_lambda.py         # Emergency alerts function
├── health_monitoring_schema.json      # OpenAPI schema for health monitoring
├── medication_management_schema.json  # OpenAPI schema for medications
├── health_insights_schema.json        # OpenAPI schema for insights
├── index.html                         # Web dashboard HTML
├── style.css                          # Web dashboard styles
└── app.js                             # Web dashboard JavaScript
```

## Configuration

### Environment Variables

The system uses the following configurable parameters:

- `NOTIFICATION_EMAIL`: Email for health alerts and reminders
- `ENVIRONMENT`: Deployment environment (dev/staging/prod)
- `AWS_REGION`: AWS region (default: us-east-1)

### Customization

#### 1. Health Thresholds

Modify anomaly detection thresholds in `health_monitoring_lambda.py`:

```python
# Heart rate thresholds
if heart_rate < 40 or heart_rate > 200:
    # Critical alert
elif heart_rate < 50 or heart_rate > 150:
    # Warning alert
```

#### 2. Medication Reminders

Customize reminder logic in `medication_management_lambda.py`:

```python
# Reminder timing
reminder_time = next_dose - timedelta(minutes=15)
```

#### 3. AI Responses

Enhance AI responses in `bedrock_agent_lambda.py`:

```python
def generate_health_insight(user_context, vitals_data):
    # Custom insight generation logic
    pass
```

## Data Models

### Vitals Data Structure

```json
{
  "userId": "user123",
  "timestamp": "2024-01-15T10:30:00Z",
  "vitals": {
    "heartRate": 72,
    "systolicBP": 120,
    "diastolicBP": 80,
    "temperature": 98.6,
    "oxygenSaturation": 98,
    "respiratoryRate": 16,
    "bloodGlucose": 95,
    "weight": 150,
    "height": 68
  },
  "deviceId": "device001",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  }
}
```

### Medication Data Structure

```json
{
  "userId": "user123",
  "medicationId": "med001",
  "medicationName": "Metformin",
  "dosage": "500mg",
  "frequency": "twice daily",
  "startDate": "2024-01-01",
  "endDate": "2024-12-31",
  "instructions": "Take with food",
  "status": "active",
  "adherenceRate": 0.95,
  "totalDoses": 60,
  "missedDoses": 3
}
```

## API Endpoints

### Health Monitoring

```bash
# Store vitals data
POST /vitals
{
  "userId": "user123",
  "vitals": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}

# Get recent vitals
GET /vitals?userId=user123&hours=24

# Check for anomalies
POST /anomalies
{
  "userId": "user123",
  "vitals": { ... }
}
```

### Medication Management

```bash
# Add medication
POST /medications
{
  "userId": "user123",
  "medicationName": "Metformin",
  "dosage": "500mg",
  "frequency": "twice daily"
}

# Get medications
GET /medications?userId=user123

# Log dose
POST /medications/{medicationId}/dose
{
  "userId": "user123",
  "doseTime": "2024-01-15T10:30:00Z"
}
```

### Health Insights

```bash
# Generate insights
POST /insights
{
  "userId": "user123",
  "days": 30
}

# Get recommendations
POST /recommendations
{
  "userId": "user123",
  "focusAreas": ["cardiovascular", "metabolic"]
}
```

### AI Chat

```bash
# Chat with AI assistant
POST /chat
{
  "userId": "user123",
  "message": "What's my current heart rate?",
  "sessionId": "session123"
}
```

## Testing

### Automated Tests

The test suite (`test_agent.py`) validates:

- **Infrastructure Deployment**: CloudFormation stack creation
- **Lambda Functions**: All 5 Lambda functions
- **DynamoDB Tables**: Data persistence and retrieval
- **SNS Notifications**: Alert and reminder delivery
- **Bedrock Agent**: AI conversation capabilities
- **Web Application**: Dashboard functionality
- **Performance**: Response times and throughput

### Manual Testing

#### 1. Health Data Simulation

```python
# Simulate health data
import requests
import json
from datetime import datetime

vitals_data = {
    "userId": "test-user",
    "vitals": {
        "heartRate": 75,
        "systolicBP": 125,
        "diastolicBP": 82,
        "temperature": 98.4,
        "oxygenSaturation": 97
    },
    "timestamp": datetime.utcnow().isoformat()
}

response = requests.post(f"{API_ENDPOINT}/vitals", json=vitals_data)
print(response.json())
```

#### 2. AI Chat Testing

```python
# Test AI chat
chat_data = {
    "userId": "test-user",
    "message": "How are my vitals looking today?",
    "sessionId": "test-session"
}

response = requests.post(f"{API_ENDPOINT}/chat", json=chat_data)
print(response.json())
```

#### 3. Emergency Simulation

```python
# Simulate emergency condition
emergency_vitals = {
    "userId": "test-user",
    "vitals": {
        "heartRate": 200,  # Critical
        "systolicBP": 250,  # Critical
        "diastolicBP": 150,
        "temperature": 107.0,  # Critical
        "oxygenSaturation": 75,  # Critical
        "panicButton": True
    },
    "timestamp": datetime.utcnow().isoformat()
}

response = requests.post(f"{API_ENDPOINT}/emergency", json=emergency_vitals)
print(response.json())
```

## Security & Compliance

### HIPAA Compliance

- **Encryption at Rest**: All DynamoDB tables encrypted with KMS
- **Encryption in Transit**: HTTPS/TLS for all communications
- **Access Control**: IAM roles with least privilege
- **Audit Logging**: CloudWatch logs for all operations
- **Data Retention**: Configurable retention policies

### Security Best Practices

- **Network Security**: VPC endpoints for AWS services
- **Identity Management**: MFA-enabled IAM users
- **Secrets Management**: AWS Secrets Manager for sensitive data
- **Monitoring**: CloudWatch alarms for security events
- **Backup**: Automated backups with point-in-time recovery

## Monitoring & Observability

### CloudWatch Metrics

- **Lambda Metrics**: Invocations, errors, duration
- **DynamoDB Metrics**: Read/write capacity, throttling
- **SNS Metrics**: Message delivery, failures
- **Custom Metrics**: Health scores, anomaly counts

### CloudWatch Alarms

- **High Error Rate**: Lambda function errors
- **Performance Issues**: High latency
- **Resource Utilization**: DynamoDB capacity
- **Security Events**: Unusual access patterns

### Logging

- **Application Logs**: Structured JSON logging
- **Access Logs**: API Gateway request logs
- **Audit Logs**: HIPAA compliance logging
- **Error Logs**: Exception tracking and debugging


## Troubleshooting

### Common Issues

#### 1. Deployment Failures

```bash
# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name ai-health-assistant

# View stack events
aws cloudformation describe-stack-events --stack-name ai-health-assistant
```

#### 2. Lambda Function Errors

```bash
# Check Lambda function logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/ai-health-assistant"

# View recent logs
aws logs tail /aws/lambda/ai-health-assistant-health-monitoring --follow
```

#### 3. DynamoDB Issues

```bash
# Check table status
aws dynamodb describe-table --table-name prod-health-vitals

# View table metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=prod-health-vitals
```

#### 4. SNS Delivery Issues

```bash
# Check SNS topic
aws sns get-topic-attributes --topic-arn arn:aws:sns:us-east-1:123456789012:prod-health-alerts

# Test message delivery
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:123456789012:prod-health-alerts \
  --message "Test message"
```

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## Updates & Maintenance

### Updating the System

1. **Code Updates**: Modify Lambda functions and redeploy
2. **Infrastructure Changes**: Update CloudFormation template
3. **Configuration Changes**: Update environment variables
4. **Database Migrations**: Use DynamoDB streams for data migration

### Backup & Recovery

- **Automated Backups**: DynamoDB point-in-time recovery
- **Cross-Region Replication**: For disaster recovery
- **Infrastructure as Code**: CloudFormation for quick recovery
- **Data Export**: Regular data exports for compliance

### Scaling

- **Horizontal Scaling**: Lambda functions scale automatically
- **Vertical Scaling**: Increase DynamoDB capacity
- **Regional Scaling**: Deploy to multiple regions
- **Performance Tuning**: Optimize Lambda memory and timeout

## Contributing

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Run tests**: `python3 test_agent.py`
5. **Submit a pull request**

### Code Standards

- **Python**: PEP 8 style guide
- **JavaScript**: ESLint configuration
- **Documentation**: Comprehensive docstrings
- **Testing**: Unit and integration tests
- **Security**: Security best practices

## Support

### Documentation

- **API Documentation**: OpenAPI schemas included
- **Architecture Diagrams**: Available in `/docs`
- **User Guides**: Step-by-step tutorials
- **FAQ**: Common questions and answers

### Community

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community support and ideas
- **Wiki**: Additional documentation and examples
- **Releases**: Version history and changelog

### Professional Support



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Amazon Web Services** for the cloud infrastructure
- **Amazon Bedrock** for the AI capabilities
- **Open Source Community** for the tools and libraries
- **Healthcare Professionals** for domain expertise
- **Beta Testers** for feedback and improvements

---



*Last updated: January 2024*
