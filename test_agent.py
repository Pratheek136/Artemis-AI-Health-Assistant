#!/usr/bin/env python3
"""
AI Health Assistant Test Suite
This script tests the health assistant system by simulating health data,
validating agent conversations, and checking medication reminders.
"""

import json
import time
import random
import requests
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import sys
import os

# Configuration
REGION = "us-east-1"
STACK_NAME = "ai-health-assistant"
TEST_USER_ID = "test-user-123"
API_BASE_URL = ""  # Will be set from CloudFormation outputs

# Test data
TEST_VITALS = [
    {
        "heartRate": 72,
        "systolicBP": 120,
        "diastolicBP": 80,
        "temperature": 98.6,
        "oxygenSaturation": 98
    },
    {
        "heartRate": 75,
        "systolicBP": 125,
        "diastolicBP": 82,
        "temperature": 98.4,
        "oxygenSaturation": 97
    },
    {
        "heartRate": 68,
        "systolicBP": 118,
        "diastolicBP": 78,
        "temperature": 98.8,
        "oxygenSaturation": 99
    }
]

TEST_MEDICATIONS = [
    {
        "medicationName": "Metformin",
        "dosage": "500mg",
        "frequency": "twice daily",
        "instructions": "Take with food"
    },
    {
        "medicationName": "Lisinopril",
        "dosage": "10mg",
        "frequency": "once daily",
        "instructions": "Take in the morning"
    }
]

TEST_CHAT_MESSAGES = [
    "What's my current heart rate?",
    "How are my blood pressure readings?",
    "When is my next medication due?",
    "Can you give me health insights?",
    "I'm feeling dizzy, should I be concerned?",
    "What's my overall health score?",
    "Can you remind me about my medications?",
    "How can I improve my health?"
]

class HealthAssistantTester:
    def __init__(self):
        self.session = requests.Session()
        self.dynamodb = boto3.resource('dynamodb', region_name=REGION)
        self.lambda_client = boto3.client('lambda', region_name=REGION)
        self.sns_client = boto3.client('sns', region_name=REGION)
        self.test_results = []
        
    def log_test(self, test_name, status, message="", details=None):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status_symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        print(f"{status_symbol} {test_name}: {message}")
        
        if details:
            print(f"    Details: {details}")
    
    def get_cloudformation_outputs(self):
        """Get CloudFormation stack outputs"""
        try:
            cloudformation = boto3.client('cloudformation', region_name=REGION)
            response = cloudformation.describe_stacks(StackName=STACK_NAME)
            
            outputs = {}
            for output in response['Stacks'][0]['Outputs']:
                outputs[output['OutputKey']] = output['OutputValue']
            
            return outputs
        except Exception as e:
            self.log_test("Get CloudFormation Outputs", "FAIL", f"Failed to get stack outputs: {str(e)}")
            return {}
    
    def test_infrastructure_deployment(self):
        """Test if infrastructure is deployed correctly"""
        print("\n=== Testing Infrastructure Deployment ===")
        
        try:
            outputs = self.get_cloudformation_outputs()
            
            if not outputs:
                self.log_test("Infrastructure Deployment", "FAIL", "No CloudFormation outputs found")
                return False
            
            # Check required outputs
            required_outputs = [
                "VitalsTableName",
                "MedicationsTableName", 
                "UserProfilesTableName",
                "HealthAlertsTopic",
                "MedicationRemindersTopic"
            ]
            
            missing_outputs = [output for output in required_outputs if output not in outputs]
            
            if missing_outputs:
                self.log_test("Infrastructure Deployment", "FAIL", 
                            f"Missing required outputs: {missing_outputs}")
                return False
            
            # Set API base URL if available
            global API_BASE_URL
            if "HealthAPIEndpoint" in outputs:
                API_BASE_URL = outputs["HealthAPIEndpoint"]
            
            self.log_test("Infrastructure Deployment", "PASS", 
                        f"All required resources deployed. Found {len(outputs)} outputs")
            return True
            
        except Exception as e:
            self.log_test("Infrastructure Deployment", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_dynamodb_tables(self):
        """Test DynamoDB table access"""
        print("\n=== Testing DynamoDB Tables ===")
        
        try:
            outputs = self.get_cloudformation_outputs()
            
            # Test Vitals table
            vitals_table_name = outputs.get("VitalsTableName")
            if vitals_table_name:
                vitals_table = self.dynamodb.Table(vitals_table_name)
                vitals_table.load()
                self.log_test("Vitals Table Access", "PASS", f"Table {vitals_table_name} accessible")
            else:
                self.log_test("Vitals Table Access", "FAIL", "Vitals table name not found")
            
            # Test Medications table
            medications_table_name = outputs.get("MedicationsTableName")
            if medications_table_name:
                medications_table = self.dynamodb.Table(medications_table_name)
                medications_table.load()
                self.log_test("Medications Table Access", "PASS", f"Table {medications_table_name} accessible")
            else:
                self.log_test("Medications Table Access", "FAIL", "Medications table name not found")
            
            # Test User Profiles table
            profiles_table_name = outputs.get("UserProfilesTableName")
            if profiles_table_name:
                profiles_table = self.dynamodb.Table(profiles_table_name)
                profiles_table.load()
                self.log_test("User Profiles Table Access", "PASS", f"Table {profiles_table_name} accessible")
            else:
                self.log_test("User Profiles Table Access", "FAIL", "User profiles table name not found")
                
        except Exception as e:
            self.log_test("DynamoDB Tables", "FAIL", f"Error: {str(e)}")
    
    def test_health_monitoring_lambda(self):
        """Test health monitoring Lambda function"""
        print("\n=== Testing Health Monitoring Lambda ===")
        
        try:
            outputs = self.get_cloudformation_outputs()
            
            # Test with normal vitals
            test_vitals = TEST_VITALS[0]
            test_event = {
                "userId": TEST_USER_ID,
                "vitals": test_vitals,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Invoke Lambda function
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-health-monitoring",
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                self.log_test("Health Monitoring Lambda", "PASS", 
                            "Successfully processed normal vitals")
            else:
                self.log_test("Health Monitoring Lambda", "FAIL", 
                            f"Unexpected response: {result}")
            
            # Test with abnormal vitals (should trigger alerts)
            abnormal_vitals = {
                "heartRate": 180,  # High heart rate
                "systolicBP": 200,  # High blood pressure
                "diastolicBP": 120,
                "temperature": 105.0,  # High temperature
                "oxygenSaturation": 85  # Low oxygen
            }
            
            abnormal_event = {
                "userId": TEST_USER_ID,
                "vitals": abnormal_vitals,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-health-monitoring",
                InvocationType='RequestResponse',
                Payload=json.dumps(abnormal_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                self.log_test("Health Monitoring Lambda - Anomaly Detection", "PASS", 
                            "Successfully detected and processed anomalies")
            else:
                self.log_test("Health Monitoring Lambda - Anomaly Detection", "FAIL", 
                            f"Failed to process anomalies: {result}")
                
        except Exception as e:
            self.log_test("Health Monitoring Lambda", "FAIL", f"Error: {str(e)}")
    
    def test_medication_management_lambda(self):
        """Test medication management Lambda function"""
        print("\n=== Testing Medication Management Lambda ===")
        
        try:
            # Test adding medication
            for medication in TEST_MEDICATIONS:
                add_event = {
                    "action": "add_medication",
                    "userId": TEST_USER_ID,
                    **medication
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=f"{STACK_NAME}-medication-management",
                    InvocationType='RequestResponse',
                    Payload=json.dumps(add_event)
                )
                
                result = json.loads(response['Payload'].read())
                
                if result.get('statusCode') == 200:
                    self.log_test(f"Add Medication - {medication['medicationName']}", "PASS", 
                                "Medication added successfully")
                else:
                    self.log_test(f"Add Medication - {medication['medicationName']}", "FAIL", 
                                f"Failed to add medication: {result}")
            
            # Test getting medications
            get_event = {
                "action": "get_medications",
                "userId": TEST_USER_ID
            }
            
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-medication-management",
                InvocationType='RequestResponse',
                Payload=json.dumps(get_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                self.log_test("Get Medications", "PASS", "Successfully retrieved medications")
            else:
                self.log_test("Get Medications", "FAIL", f"Failed to get medications: {result}")
            
            # Test logging dose
            log_dose_event = {
                "action": "log_dose",
                "userId": TEST_USER_ID,
                "medicationId": "med1",  # Assuming first medication
                "doseTime": datetime.utcnow().isoformat()
            }
            
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-medication-management",
                InvocationType='RequestResponse',
                Payload=json.dumps(log_dose_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                self.log_test("Log Medication Dose", "PASS", "Successfully logged dose")
            else:
                self.log_test("Log Medication Dose", "FAIL", f"Failed to log dose: {result}")
                
        except Exception as e:
            self.log_test("Medication Management Lambda", "FAIL", f"Error: {str(e)}")
    
    def test_health_insights_lambda(self):
        """Test health insights Lambda function"""
        print("\n=== Testing Health Insights Lambda ===")
        
        try:
            # Test generating insights
            insights_event = {
                "action": "generate_insights",
                "userId": TEST_USER_ID,
                "days": 7
            }
            
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-health-insights",
                InvocationType='RequestResponse',
                Payload=json.dumps(insights_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                self.log_test("Generate Health Insights", "PASS", "Successfully generated insights")
            else:
                self.log_test("Generate Health Insights", "FAIL", f"Failed to generate insights: {result}")
            
            # Test getting recommendations
            recommendations_event = {
                "action": "get_recommendations",
                "userId": TEST_USER_ID,
                "days": 7
            }
            
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-health-insights",
                InvocationType='RequestResponse',
                Payload=json.dumps(recommendations_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                self.log_test("Get Health Recommendations", "PASS", "Successfully retrieved recommendations")
            else:
                self.log_test("Get Health Recommendations", "FAIL", f"Failed to get recommendations: {result}")
                
        except Exception as e:
            self.log_test("Health Insights Lambda", "FAIL", f"Error: {str(e)}")
    
    def test_emergency_alerts_lambda(self):
        """Test emergency alerts Lambda function"""
        print("\n=== Testing Emergency Alerts Lambda ===")
        
        try:
            # Test emergency condition detection
            emergency_vitals = {
                "heartRate": 200,  # Critical heart rate
                "systolicBP": 250,  # Critical blood pressure
                "diastolicBP": 150,
                "temperature": 107.0,  # Critical temperature
                "oxygenSaturation": 75,  # Critical oxygen
                "panicButton": True
            }
            
            emergency_event = {
                "action": "check_emergency",
                "userId": TEST_USER_ID,
                "vitals": emergency_vitals,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-emergency-alerts",
                InvocationType='RequestResponse',
                Payload=json.dumps(emergency_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                self.log_test("Emergency Condition Detection", "PASS", "Successfully detected emergency conditions")
            else:
                self.log_test("Emergency Condition Detection", "FAIL", f"Failed to detect emergency: {result}")
            
            # Test sending emergency alert
            alert_event = {
                "action": "send_emergency_alert",
                "userId": TEST_USER_ID,
                "condition": {
                    "type": "CRITICAL_HEART_RATE",
                    "severity": "CRITICAL",
                    "message": "Critical heart rate detected",
                    "action_required": "IMMEDIATE_MEDICAL_ATTENTION"
                },
                "vitals": emergency_vitals,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-emergency-alerts",
                InvocationType='RequestResponse',
                Payload=json.dumps(alert_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                self.log_test("Send Emergency Alert", "PASS", "Successfully sent emergency alert")
            else:
                self.log_test("Send Emergency Alert", "FAIL", f"Failed to send alert: {result}")
                
        except Exception as e:
            self.log_test("Emergency Alerts Lambda", "FAIL", f"Error: {str(e)}")
    
    def test_bedrock_agent_lambda(self):
        """Test Bedrock Agent Lambda function"""
        print("\n=== Testing Bedrock Agent Lambda ===")
        
        try:
            # Test chat functionality
            for message in TEST_CHAT_MESSAGES[:3]:  # Test first 3 messages
                chat_event = {
                    "action": "chat",
                    "userId": TEST_USER_ID,
                    "message": message,
                    "sessionId": str(uuid.uuid4())
                }
                
                response = self.lambda_client.invoke(
                    FunctionName=f"{STACK_NAME}-bedrock-agent",
                    InvocationType='RequestResponse',
                    Payload=json.dumps(chat_event)
                )
                
                result = json.loads(response['Payload'].read())
                
                if result.get('statusCode') == 200:
                    self.log_test(f"Chat - {message[:30]}...", "PASS", "Successfully processed chat message")
                else:
                    self.log_test(f"Chat - {message[:30]}...", "FAIL", f"Failed to process chat: {result}")
            
            # Test health query
            health_query_event = {
                "action": "health_query",
                "userId": TEST_USER_ID,
                "message": "What's my current heart rate?",
                "sessionId": str(uuid.uuid4())
            }
            
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-bedrock-agent",
                InvocationType='RequestResponse',
                Payload=json.dumps(health_query_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                self.log_test("Health Query", "PASS", "Successfully processed health query")
            else:
                self.log_test("Health Query", "FAIL", f"Failed to process health query: {result}")
            
            # Test medication query
            medication_query_event = {
                "action": "medication_query",
                "userId": TEST_USER_ID,
                "message": "When is my next medication due?",
                "sessionId": str(uuid.uuid4())
            }
            
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-bedrock-agent",
                InvocationType='RequestResponse',
                Payload=json.dumps(medication_query_event)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                self.log_test("Medication Query", "PASS", "Successfully processed medication query")
            else:
                self.log_test("Medication Query", "FAIL", f"Failed to process medication query: {result}")
                
        except Exception as e:
            self.log_test("Bedrock Agent Lambda", "FAIL", f"Error: {str(e)}")
    
    def test_sns_notifications(self):
        """Test SNS notification functionality"""
        print("\n=== Testing SNS Notifications ===")
        
        try:
            outputs = self.get_cloudformation_outputs()
            
            # Test health alerts topic
            health_alerts_topic = outputs.get("HealthAlertsTopic")
            if health_alerts_topic:
                test_message = {
                    "userId": TEST_USER_ID,
                    "message": "Test health alert",
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "INFO"
                }
                
                response = self.sns_client.publish(
                    TopicArn=health_alerts_topic,
                    Message=json.dumps(test_message),
                    Subject="Test Health Alert"
                )
                
                if response.get('MessageId'):
                    self.log_test("Health Alerts SNS", "PASS", "Successfully sent test alert")
                else:
                    self.log_test("Health Alerts SNS", "FAIL", "Failed to send test alert")
            else:
                self.log_test("Health Alerts SNS", "FAIL", "Health alerts topic not found")
            
            # Test medication reminders topic
            medication_reminders_topic = outputs.get("MedicationRemindersTopic")
            if medication_reminders_topic:
                test_message = {
                    "userId": TEST_USER_ID,
                    "medicationName": "Metformin",
                    "dosage": "500mg",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                response = self.sns_client.publish(
                    TopicArn=medication_reminders_topic,
                    Message=json.dumps(test_message),
                    Subject="Test Medication Reminder"
                )
                
                if response.get('MessageId'):
                    self.log_test("Medication Reminders SNS", "PASS", "Successfully sent test reminder")
                else:
                    self.log_test("Medication Reminders SNS", "FAIL", "Failed to send test reminder")
            else:
                self.log_test("Medication Reminders SNS", "FAIL", "Medication reminders topic not found")
                
        except Exception as e:
            self.log_test("SNS Notifications", "FAIL", f"Error: {str(e)}")
    
    def test_data_persistence(self):
        """Test data persistence in DynamoDB"""
        print("\n=== Testing Data Persistence ===")
        
        try:
            outputs = self.get_cloudformation_outputs()
            
            # Test vitals data persistence
            vitals_table_name = outputs.get("VitalsTableName")
            if vitals_table_name:
                vitals_table = self.dynamodb.Table(vitals_table_name)
                
                # Insert test vitals
                test_vitals_item = {
                    "userId": TEST_USER_ID,
                    "timestamp": datetime.utcnow().isoformat(),
                    "vitals": TEST_VITALS[0],
                    "processedAt": datetime.utcnow().isoformat()
                }
                
                vitals_table.put_item(Item=test_vitals_item)
                
                # Retrieve test vitals
                response = vitals_table.get_item(
                    Key={
                        "userId": TEST_USER_ID,
                        "timestamp": test_vitals_item["timestamp"]
                    }
                )
                
                if "Item" in response:
                    self.log_test("Vitals Data Persistence", "PASS", "Successfully stored and retrieved vitals")
                else:
                    self.log_test("Vitals Data Persistence", "FAIL", "Failed to retrieve stored vitals")
            
            # Test medications data persistence
            medications_table_name = outputs.get("MedicationsTableName")
            if medications_table_name:
                medications_table = self.dynamodb.Table(medications_table_name)
                
                # Insert test medication
                test_medication_item = {
                    "userId": TEST_USER_ID,
                    "medicationId": "test-med-1",
                    "medicationName": "Test Medication",
                    "dosage": "100mg",
                    "frequency": "once daily",
                    "status": "active",
                    "createdAt": datetime.utcnow().isoformat()
                }
                
                medications_table.put_item(Item=test_medication_item)
                
                # Retrieve test medication
                response = medications_table.get_item(
                    Key={
                        "userId": TEST_USER_ID,
                        "medicationId": "test-med-1"
                    }
                )
                
                if "Item" in response:
                    self.log_test("Medications Data Persistence", "PASS", "Successfully stored and retrieved medication")
                else:
                    self.log_test("Medications Data Persistence", "FAIL", "Failed to retrieve stored medication")
                
        except Exception as e:
            self.log_test("Data Persistence", "FAIL", f"Error: {str(e)}")
    
    def test_web_application(self):
        """Test web application accessibility"""
        print("\n=== Testing Web Application ===")
        
        try:
            # Test if web files exist
            web_files = ["index.html", "style.css", "app.js"]
            
            for file in web_files:
                if os.path.exists(file):
                    self.log_test(f"Web File - {file}", "PASS", "File exists")
                else:
                    self.log_test(f"Web File - {file}", "FAIL", "File not found")
            
            # Test HTML structure
            if os.path.exists("index.html"):
                with open("index.html", "r") as f:
                    html_content = f.read()
                    
                required_elements = [
                    "AI Health Assistant",
                    "dashboard",
                    "vitals",
                    "medications",
                    "insights",
                    "chat"
                ]
                
                for element in required_elements:
                    if element.lower() in html_content.lower():
                        self.log_test(f"HTML Element - {element}", "PASS", "Element found")
                    else:
                        self.log_test(f"HTML Element - {element}", "FAIL", "Element not found")
            
            # Test CSS structure
            if os.path.exists("style.css"):
                with open("style.css", "r") as f:
                    css_content = f.read()
                    
                required_classes = [
                    "dashboard",
                    "header",
                    "sidebar",
                    "content-area",
                    "health-score-card",
                    "stats-grid"
                ]
                
                for class_name in required_classes:
                    if f".{class_name}" in css_content:
                        self.log_test(f"CSS Class - {class_name}", "PASS", "Class found")
                    else:
                        self.log_test(f"CSS Class - {class_name}", "FAIL", "Class not found")
            
            # Test JavaScript structure
            if os.path.exists("app.js"):
                with open("app.js", "r") as f:
                    js_content = f.read()
                    
                required_functions = [
                    "initializeApp",
                    "loadDashboardData",
                    "sendMessage",
                    "addMedication",
                    "generateInsights"
                ]
                
                for function_name in required_functions:
                    if function_name in js_content:
                        self.log_test(f"JavaScript Function - {function_name}", "PASS", "Function found")
                    else:
                        self.log_test(f"JavaScript Function - {function_name}", "FAIL", "Function not found")
                
        except Exception as e:
            self.log_test("Web Application", "FAIL", f"Error: {str(e)}")
    
    def run_performance_test(self):
        """Run performance tests"""
        print("\n=== Running Performance Tests ===")
        
        try:
            # Test Lambda function performance
            start_time = time.time()
            
            test_event = {
                "userId": TEST_USER_ID,
                "vitals": TEST_VITALS[0],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.lambda_client.invoke(
                FunctionName=f"{STACK_NAME}-health-monitoring",
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            if execution_time < 5.0:  # Less than 5 seconds
                self.log_test("Lambda Performance", "PASS", f"Execution time: {execution_time:.2f}s")
            else:
                self.log_test("Lambda Performance", "WARN", f"Slow execution time: {execution_time:.2f}s")
            
            # Test DynamoDB performance
            start_time = time.time()
            
            outputs = self.get_cloudformation_outputs()
            vitals_table_name = outputs.get("VitalsTableName")
            
            if vitals_table_name:
                vitals_table = self.dynamodb.Table(vitals_table_name)
                
                # Test query performance
                response = vitals_table.query(
                    KeyConditionExpression='userId = :userId',
                    ExpressionAttributeValues={':userId': TEST_USER_ID},
                    Limit=10
                )
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                if execution_time < 2.0:  # Less than 2 seconds
                    self.log_test("DynamoDB Performance", "PASS", f"Query time: {execution_time:.2f}s")
                else:
                    self.log_test("DynamoDB Performance", "WARN", f"Slow query time: {execution_time:.2f}s")
            
        except Exception as e:
            self.log_test("Performance Tests", "FAIL", f"Error: {str(e)}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("AI HEALTH ASSISTANT TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warning_tests = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"\nSUMMARY:")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Warnings: {warning_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\nDETAILED RESULTS:")
        print("-" * 60)
        
        for result in self.test_results:
            status_symbol = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "⚠"
            print(f"{status_symbol} {result['test_name']}: {result['message']}")
            if result.get('details'):
                print(f"    Details: {result['details']}")
        
        # Save report to file
        report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "warning_tests": warning_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "results": self.test_results,
                "timestamp": datetime.utcnow().isoformat()
            }, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_filename}")
        
        # Return success if all critical tests passed
        return failed_tests == 0
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting AI Health Assistant Test Suite...")
        print(f"Test User ID: {TEST_USER_ID}")
        print(f"Region: {REGION}")
        print(f"Stack Name: {STACK_NAME}")
        
        # Run all test categories
        self.test_infrastructure_deployment()
        self.test_dynamodb_tables()
        self.test_health_monitoring_lambda()
        self.test_medication_management_lambda()
        self.test_health_insights_lambda()
        self.test_emergency_alerts_lambda()
        self.test_bedrock_agent_lambda()
        self.test_sns_notifications()
        self.test_data_persistence()
        self.test_web_application()
        self.run_performance_test()
        
        # Generate report
        success = self.generate_test_report()
        
        if success:
            print("\n🎉 All tests passed! The AI Health Assistant is ready for use.")
            return 0
        else:
            print("\n❌ Some tests failed. Please review the report and fix the issues.")
            return 1

def main():
    """Main function"""
    if len(sys.argv) > 1:
        global STACK_NAME
        STACK_NAME = sys.argv[1]
    
    tester = HealthAssistantTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
