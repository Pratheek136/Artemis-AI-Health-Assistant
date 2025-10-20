#!/bin/bash

# AI Health Assistant Deployment Script
# This script deploys the complete AI Health Assistant infrastructure to AWS

set -e  # Exit on any error

# Configuration
REGION="us-east-1"
STACK_NAME="ai-health-assistant"
ENVIRONMENT="prod"
NOTIFICATION_EMAIL=""
PROFILE="default"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command_exists aws; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity --profile $PROFILE >/dev/null 2>&1; then
        print_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check if notification email is provided
    if [ -z "$NOTIFICATION_EMAIL" ]; then
        print_error "Notification email is required. Please set NOTIFICATION_EMAIL environment variable or pass it as an argument."
        print_status "Usage: ./deploy.sh <notification-email> [environment] [aws-profile]"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to validate email format
validate_email() {
    local email=$1
    if [[ $email =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to create S3 bucket for deployment artifacts
create_deployment_bucket() {
    local bucket_name="ai-health-assistant-deployment-$(date +%s)"
    print_status "Creating S3 bucket for deployment artifacts: $bucket_name"
    
    aws s3 mb s3://$bucket_name --region $REGION --profile $PROFILE
    echo $bucket_name
}

# Function to package and upload Lambda functions
package_lambda_functions() {
    local bucket_name=$1
    print_status "Packaging and uploading Lambda functions..."
    
    # Create temporary directory for packaging
    local temp_dir=$(mktemp -d)
    
    # Package health monitoring Lambda
    print_status "Packaging health monitoring Lambda..."
    cp health_monitoring_lambda.py $temp_dir/
    cd $temp_dir
    zip health_monitoring.zip health_monitoring_lambda.py
    aws s3 cp health_monitoring.zip s3://$bucket_name/lambda/ --profile $PROFILE
    cd - > /dev/null
    
    # Package medication management Lambda
    print_status "Packaging medication management Lambda..."
    cp medication_management_lambda.py $temp_dir/
    cd $temp_dir
    zip medication_management.zip medication_management_lambda.py
    aws s3 cp medication_management.zip s3://$bucket_name/lambda/ --profile $PROFILE
    cd - > /dev/null
    
    # Package health insights Lambda
    print_status "Packaging health insights Lambda..."
    cp health_insights_lambda.py $temp_dir/
    cd $temp_dir
    zip health_insights.zip health_insights_lambda.py
    aws s3 cp health_insights.zip s3://$bucket_name/lambda/ --profile $PROFILE
    cd - > /dev/null
    
    # Package emergency alerts Lambda
    print_status "Packaging emergency alerts Lambda..."
    cp emergency_alerts_lambda.py $temp_dir/
    cd $temp_dir
    zip emergency_alerts.zip emergency_alerts_lambda.py
    aws s3 cp emergency_alerts.zip s3://$bucket_name/lambda/ --profile $PROFILE
    cd - > /dev/null
    
    # Package Bedrock Agent Lambda
    print_status "Packaging Bedrock Agent Lambda..."
    cp bedrock_agent_lambda.py $temp_dir/
    cd $temp_dir
    zip bedrock_agent.zip bedrock_agent_lambda.py
    aws s3 cp bedrock_agent.zip s3://$bucket_name/lambda/ --profile $PROFILE
    cd - > /dev/null
    
    # Clean up
    rm -rf $temp_dir
    
    print_success "Lambda functions packaged and uploaded"
}

# Function to deploy CloudFormation stack
deploy_cloudformation() {
    local bucket_name=$1
    print_status "Deploying CloudFormation stack..."
    
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name $STACK_NAME --profile $PROFILE >/dev/null 2>&1; then
        print_status "Stack exists, updating..."
        aws cloudformation update-stack \
            --stack-name $STACK_NAME \
            --template-body file://infrastructure.yaml \
            --parameters ParameterKey=NotificationEmail,ParameterValue=$NOTIFICATION_EMAIL \
                        ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
            --capabilities CAPABILITY_NAMED_IAM \
            --region $REGION \
            --profile $PROFILE
    else
        print_status "Creating new stack..."
        aws cloudformation create-stack \
            --stack-name $STACK_NAME \
            --template-body file://infrastructure.yaml \
            --parameters ParameterKey=NotificationEmail,ParameterValue=$NOTIFICATION_EMAIL \
                        ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
            --capabilities CAPABILITY_NAMED_IAM \
            --region $REGION \
            --profile $PROFILE
    fi
    
    # Wait for stack to complete
    print_status "Waiting for stack deployment to complete..."
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --profile $PROFILE 2>/dev/null || \
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --profile $PROFILE
    
    print_success "CloudFormation stack deployed successfully"
}

# Function to update Lambda function code
update_lambda_functions() {
    local bucket_name=$1
    print_status "Updating Lambda function code..."
    
    # Get stack outputs
    local stack_outputs=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --profile $PROFILE --query 'Stacks[0].Outputs')
    
    # Update health monitoring function
    local health_monitoring_function=$(echo $stack_outputs | jq -r '.[] | select(.OutputKey=="HealthMonitoringFunctionArn") | .OutputValue')
    if [ "$health_monitoring_function" != "null" ]; then
        print_status "Updating health monitoring function..."
        aws lambda update-function-code \
            --function-name $health_monitoring_function \
            --s3-bucket $bucket_name \
            --s3-key lambda/health_monitoring.zip \
            --profile $PROFILE
    fi
    
    # Update medication management function
    local medication_management_function=$(echo $stack_outputs | jq -r '.[] | select(.OutputKey=="MedicationManagementFunctionArn") | .OutputValue')
    if [ "$medication_management_function" != "null" ]; then
        print_status "Updating medication management function..."
        aws lambda update-function-code \
            --function-name $medication_management_function \
            --s3-bucket $bucket_name \
            --s3-key lambda/medication_management.zip \
            --profile $PROFILE
    fi
    
    # Update health insights function
    local health_insights_function=$(echo $stack_outputs | jq -r '.[] | select(.OutputKey=="HealthInsightsFunctionArn") | .OutputValue')
    if [ "$health_insights_function" != "null" ]; then
        print_status "Updating health insights function..."
        aws lambda update-function-code \
            --function-name $health_insights_function \
            --s3-bucket $bucket_name \
            --s3-key lambda/health_insights.zip \
            --profile $PROFILE
    fi
    
    # Update emergency alerts function
    local emergency_alerts_function=$(echo $stack_outputs | jq -r '.[] | select(.OutputKey=="EmergencyAlertsFunctionArn") | .OutputValue')
    if [ "$emergency_alerts_function" != "null" ]; then
        print_status "Updating emergency alerts function..."
        aws lambda update-function-code \
            --function-name $emergency_alerts_function \
            --s3-bucket $bucket_name \
            --s3-key lambda/emergency_alerts.zip \
            --profile $PROFILE
    fi
    
    # Update Bedrock Agent function
    local bedrock_agent_function=$(echo $stack_outputs | jq -r '.[] | select(.OutputKey=="BedrockAgentFunctionArn") | .OutputValue')
    if [ "$bedrock_agent_function" != "null" ]; then
        print_status "Updating Bedrock Agent function..."
        aws lambda update-function-code \
            --function-name $bedrock_agent_function \
            --s3-bucket $bucket_name \
            --s3-key lambda/bedrock_agent.zip \
            --profile $PROFILE
    fi
    
    print_success "Lambda functions updated successfully"
}

# Function to create Bedrock Agent
create_bedrock_agent() {
    print_status "Creating Bedrock Agent..."
    
    # Get stack outputs
    local stack_outputs=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --profile $PROFILE --query 'Stacks[0].Outputs')
    local bedrock_agent_function=$(echo $stack_outputs | jq -r '.[] | select(.OutputKey=="BedrockAgentFunctionArn") | .OutputValue')
    
    if [ "$bedrock_agent_function" != "null" ]; then
        # Create agent
        local agent_id=$(aws bedrock-agent create-agent \
            --agent-name "AI-Health-Assistant" \
            --description "AI Health Assistant powered by Amazon Titan" \
            --foundation-model "amazon.titan-text-express-v1:0:8k" \
            --profile $PROFILE \
            --query 'agent.agentId' \
            --output text)
        
        print_status "Created Bedrock Agent with ID: $agent_id"
        
        # Create agent action group
        aws bedrock-agent create-agent-action-group \
            --agent-id $agent_id \
            --agent-version "DRAFT" \
            --action-group-name "HealthMonitoring" \
            --description "Health monitoring and vitals management" \
            --action-group-executor lambda=$bedrock_agent_function \
            --api-schema file://health_monitoring_schema.json \
            --profile $PROFILE
        
        aws bedrock-agent create-agent-action-group \
            --agent-id $agent_id \
            --agent-version "DRAFT" \
            --action-group-name "MedicationManagement" \
            --description "Medication management and reminders" \
            --action-group-executor lambda=$bedrock_agent_function \
            --api-schema file://medication_management_schema.json \
            --profile $PROFILE
        
        aws bedrock-agent create-agent-action-group \
            --agent-id $agent_id \
            --agent-version "DRAFT" \
            --action-group-name "HealthInsights" \
            --description "Health insights and recommendations" \
            --action-group-executor lambda=$bedrock_agent_function \
            --api-schema file://health_insights_schema.json \
            --profile $PROFILE
        
        # Prepare agent
        aws bedrock-agent prepare-agent \
            --agent-id $agent_id \
            --profile $PROFILE
        
        print_success "Bedrock Agent created and configured"
    else
        print_warning "Bedrock Agent function not found, skipping agent creation"
    fi
}

# Function to deploy web application
deploy_web_app() {
    print_status "Deploying web application..."
    
    # Create S3 bucket for web hosting
    local web_bucket_name="ai-health-assistant-web-ARTEMIS-20251019"
    aws s3 mb s3://$web_bucket_name --region $REGION --profile $PROFILE
    
    # Upload web files
    aws s3 sync index.html s3://$web_bucket_name/ --profile $PROFILE
    aws s3 sync style.css s3://$web_bucket_name/ --profile $PROFILE
    aws s3 sync app.js s3://$web_bucket_name/ --profile $PROFILE

    # Configure bucket for static website hosting
    aws s3 website s3://$web_bucket_name \
        --index-document index.html \
        --error-document index.html \
        --profile $PROFILE
    
    # Set bucket policy for public read access
    cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$web_bucket_name/*"
        }
    ]
}
EOF
    
    aws s3api put-bucket-policy \
        --bucket $web_bucket_name \
        --policy file://bucket-policy.json \
        --profile $PROFILE
    
    # Clean up
    rm bucket-policy.json
    
    print_success "Web application deployed to: http://$web_bucket_name.s3-website-$REGION.amazonaws.com"
}

# Function to run tests
run_tests() {
    print_status "Running deployment tests..."
    
    if [ -f "test_agent.py" ]; then
        python3 test_agent.py
        print_success "Tests completed successfully"
    else
        print_warning "Test file not found, skipping tests"
    fi
}

# Function to display deployment summary
display_summary() {
    print_status "Deployment Summary"
    echo "=================="
    
    # Get stack outputs
    local stack_outputs=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --profile $PROFILE --query 'Stacks[0].Outputs')
    
    echo "Stack Name: $STACK_NAME"
    echo "Region: $REGION"
    echo "Environment: $ENVIRONMENT"
    echo "Notification Email: $NOTIFICATION_EMAIL"
    echo ""
    
    # Display key outputs
    local api_endpoint=$(echo $stack_outputs | jq -r '.[] | select(.OutputKey=="HealthAPIEndpoint") | .OutputValue')
    if [ "$api_endpoint" != "null" ]; then
        echo "API Endpoint: $api_endpoint"
    fi
    
    local vitals_table=$(echo $stack_outputs | jq -r '.[] | select(.OutputKey=="VitalsTableName") | .OutputValue')
    if [ "$vitals_table" != "null" ]; then
        echo "Vitals Table: $vitals_table"
    fi
    
    local medications_table=$(echo $stack_outputs | jq -r '.[] | select(.OutputKey=="MedicationsTableName") | .OutputValue')
    if [ "$medications_table" != "null" ]; then
        echo "Medications Table: $medications_table"
    fi
    
    local profiles_table=$(echo $stack_outputs | jq -r '.[] | select(.OutputKey=="UserProfilesTableName") | .OutputValue')
    if [ "$profiles_table" != "null" ]; then
        echo "User Profiles Table: $profiles_table"
    fi
    
    echo ""
    print_success "Deployment completed successfully!"
    print_status "Next steps:"
    echo "1. Configure your IoT devices to send data to the API endpoint"
    echo "2. Set up your health monitoring devices"
    echo "3. Test the system with the provided test suite"
    echo "4. Monitor the CloudWatch logs for any issues"
}

# Function to cleanup on error
cleanup_on_error() {
    print_error "Deployment failed. Cleaning up..."
    
    # Delete CloudFormation stack if it exists
    if aws cloudformation describe-stacks --stack-name $STACK_NAME --profile $PROFILE >/dev/null 2>&1; then
        print_status "Deleting CloudFormation stack..."
        aws cloudformation delete-stack --stack-name $STACK_NAME --profile $PROFILE
    fi
    
    exit 1
}

# Main deployment function
main() {
    # Parse command line arguments
    if [ $# -lt 1 ]; then
        print_error "Usage: $0 <notification-email> [environment] [aws-profile]"
        print_status "Example: $0 admin@example.com prod default"
        exit 1
    fi
    
    NOTIFICATION_EMAIL=$1
    ENVIRONMENT=${2:-prod}
    PROFILE=${3:-default}
    
    # Validate email
    if ! validate_email "$NOTIFICATION_EMAIL"; then
        print_error "Invalid email format: $NOTIFICATION_EMAIL"
        exit 1
    fi
    
    # Set trap for error handling
    trap cleanup_on_error ERR
    
    print_status "Starting AI Health Assistant deployment..."
    print_status "Notification Email: $NOTIFICATION_EMAIL"
    print_status "Environment: $ENVIRONMENT"
    print_status "AWS Profile: $PROFILE"
    print_status "Region: $REGION"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Create deployment bucket
    local deployment_bucket=$(create_deployment_bucket)
    
    # Package and upload Lambda functions
    package_lambda_functions $deployment_bucket
    
    # Deploy CloudFormation stack
    deploy_cloudformation $deployment_bucket
    
    # Update Lambda function code
    update_lambda_functions $deployment_bucket
    
    # Create Bedrock Agent
    create_bedrock_agent
    
    # Deploy web application
    deploy_web_app
    
    # Run tests
    run_tests
    
    # Display summary
    display_summary
    
    # Clean up deployment bucket
    print_status "Cleaning up deployment artifacts..."
    aws s3 rb s3://$deployment_bucket --force --profile $PROFILE
    
    print_success "Deployment completed successfully!"
}

# Run main function with all arguments
main "$@"
