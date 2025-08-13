"""
Actions Module for Agentic AI Churn Prediction System
====================================================

This module handles:
- Slack API integration for alerts
- Jira API integration for ticket creation
- SendGrid API integration for email notifications
- Action execution and logging
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from jira import JIRA
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionExecutor:
    """Executes actions based on agent reasoning decisions."""
    
    def __init__(self):
        """Initialize action executor with API clients."""
        self.slack_client = None
        self.jira_client = None
        self.sendgrid_client = None
        
        # Initialize Slack client
        slack_token = os.getenv('SLACK_BOT_TOKEN')
        if slack_token:
            self.slack_client = WebClient(token=slack_token)
            logger.info("Slack client initialized")
        else:
            logger.warning("SLACK_BOT_TOKEN not found. Slack actions will be disabled.")
        
        # Initialize Jira client
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if all([jira_url, jira_username, jira_api_token]):
            try:
                self.jira_client = JIRA(
                    server=jira_url,
                    basic_auth=(jira_username, jira_api_token)
                )
                logger.info("Jira client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Jira client: {e}")
        else:
            logger.warning("Jira credentials not found. Jira actions will be disabled.")
        
        # Initialize SendGrid client
        sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        if sendgrid_api_key:
            self.sendgrid_client = SendGridAPIClient(api_key=sendgrid_api_key)
            logger.info("SendGrid client initialized")
        else:
            logger.warning("SENDGRID_API_KEY not found. Email actions will be disabled.")
    
    def execute_action(self, action_decision: Dict, customer_data: Dict, analysis_result: Dict) -> Dict:
        """
        Execute the determined action.
        
        Args:
            action_decision: Action decision from agent reasoning
            customer_data: Customer context and metrics
            analysis_result: Full analysis results
            
        Returns:
            Dictionary containing execution results
        """
        action_type = action_decision.get('action_type', 'none')
        priority = action_decision.get('priority', 'low')
        
        logger.info(f"Executing {action_type} action with {priority} priority for customer {customer_data.get('customer_id')}")
        
        try:
            if action_type == 'slack_alert':
                result = self._send_slack_alert(action_decision, customer_data, analysis_result)
            elif action_type == 'jira_ticket':
                result = self._create_jira_ticket(action_decision, customer_data, analysis_result)
            elif action_type == 'email':
                result = self._send_email(action_decision, customer_data, analysis_result)
            elif action_type == 'none':
                result = {
                    'action_type': 'none',
                    'status': 'skipped',
                    'reason': 'No action required',
                    'executed_at': datetime.now().isoformat()
                }
            else:
                result = {
                    'action_type': action_type,
                    'status': 'failed',
                    'reason': f'Unknown action type: {action_type}',
                    'executed_at': datetime.now().isoformat()
                }
            
            # Add common metadata
            result.update({
                'customer_id': customer_data.get('customer_id'),
                'priority': priority,
                'confidence': action_decision.get('confidence', 0.0)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            return {
                'action_type': action_type,
                'status': 'failed',
                'reason': str(e),
                'customer_id': customer_data.get('customer_id'),
                'priority': priority,
                'executed_at': datetime.now().isoformat()
            }
    
    def _send_slack_alert(self, action_decision: Dict, customer_data: Dict, analysis_result: Dict) -> Dict:
        """Send Slack alert to customer success team."""
        
        if not self.slack_client:
            return {
                'action_type': 'slack_alert',
                'status': 'failed',
                'reason': 'Slack client not initialized'
            }
        
        try:
            # TODO: Replace with your actual Slack channel ID
            channel_id = os.getenv('SLACK_CHANNEL_ID', 'your-slack-channel-id')
            
            # Create alert message
            message = self._create_slack_message(action_decision, customer_data, analysis_result)
            
            # Send message
            response = self.slack_client.chat_postMessage(
                channel=channel_id,
                text=message['text'],
                blocks=message['blocks']
            )
            
            return {
                'action_type': 'slack_alert',
                'status': 'success',
                'slack_ts': response['ts'],
                'channel': channel_id,
                'executed_at': datetime.now().isoformat()
            }
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {
                'action_type': 'slack_alert',
                'status': 'failed',
                'reason': f"Slack API error: {e.response['error']}"
            }
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return {
                'action_type': 'slack_alert',
                'status': 'failed',
                'reason': str(e)
            }
    
    def _create_slack_message(self, action_decision: Dict, customer_data: Dict, analysis_result: Dict) -> Dict:
        """Create formatted Slack message with blocks."""
        
        customer_id = customer_data.get('customer_id')
        priority = action_decision.get('priority', 'low')
        churn_prob = analysis_result.get('analysis_context', {}).get('prediction_metrics', {}).get('churn_probability', 0)
        
        # Priority emoji
        priority_emoji = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }.get(priority, '⚪')
        
        # Create message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{priority_emoji} Churn Risk Alert - {customer_id}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Customer ID:*\n{customer_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:*\n{priority.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Churn Probability:*\n{churn_prob:.1%}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Monthly Revenue:*\n${customer_data.get('monthly_revenue', 0):,.0f}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Root Cause:*\n{analysis_result.get('root_cause_analysis', {}).get('primary_cause', 'Unknown')}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Action Required:*\n{action_decision.get('reason', 'No specific action')}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Customer Details"
                        },
                        "url": f"https://your-crm.com/customer/{customer_id}",
                        "style": "primary"
                    }
                ]
            }
        ]
        
        return {
            'text': f"Churn Risk Alert: Customer {customer_id} has {churn_prob:.1%} churn probability",
            'blocks': blocks
        }
    
    def _create_jira_ticket(self, action_decision: Dict, customer_data: Dict, analysis_result: Dict) -> Dict:
        """Create Jira ticket for customer investigation."""
        
        if not self.jira_client:
            return {
                'action_type': 'jira_ticket',
                'status': 'failed',
                'reason': 'Jira client not initialized'
            }
        
        try:
            # TODO: Replace with your actual Jira project key
            project_key = os.getenv('JIRA_PROJECT_KEY', 'CUST')
            
            # Create ticket details
            customer_id = customer_data.get('customer_id')
            priority = action_decision.get('priority', 'low')
            churn_prob = analysis_result.get('analysis_context', {}).get('prediction_metrics', {}).get('churn_probability', 0)
            root_cause = analysis_result.get('root_cause_analysis', {}).get('primary_cause', 'Unknown')
            
            # Map priority to Jira priority
            jira_priority_map = {
                'high': 'High',
                'medium': 'Medium',
                'low': 'Low'
            }
            
            # Create issue
            issue_dict = {
                'project': {'key': project_key},
                'summary': f'Churn Risk Alert: Customer {customer_id} - {churn_prob:.1%} churn probability',
                'description': self._create_jira_description(customer_data, analysis_result),
                'issuetype': {'name': 'Task'},
                'priority': {'name': jira_priority_map.get(priority, 'Medium')},
                'labels': ['churn-risk', 'automated-alert', f'customer-{customer_id}'],
                'customfield_10001': customer_id,  # TODO: Replace with your actual custom field ID for customer ID
            }
            
            new_issue = self.jira_client.create_issue(fields=issue_dict)
            
            return {
                'action_type': 'jira_ticket',
                'status': 'success',
                'jira_key': new_issue.key,
                'jira_id': new_issue.id,
                'url': f"{os.getenv('JIRA_URL')}/browse/{new_issue.key}",
                'executed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating Jira ticket: {e}")
            return {
                'action_type': 'jira_ticket',
                'status': 'failed',
                'reason': str(e)
            }
    
    def _create_jira_description(self, customer_data: Dict, analysis_result: Dict) -> str:
        """Create detailed Jira ticket description."""
        
        customer_id = customer_data.get('customer_id')
        root_cause = analysis_result.get('root_cause_analysis', {})
        prediction_metrics = analysis_result.get('analysis_context', {}).get('prediction_metrics', {})
        
        description = f"""
h2. Customer Churn Risk Alert

h3. Customer Information
* Customer ID: {customer_id}
* Monthly Revenue: ${customer_data.get('monthly_revenue', 0):,.0f}
* Total Revenue: ${customer_data.get('total_revenue', 0):,.0f}
* Days Since Last Login: {customer_data.get('days_since_last_login', 'N/A')}
* Login Frequency (30d): {customer_data.get('login_frequency_30d', 'N/A')}
* Support Tickets (30d): {customer_data.get('support_tickets_30d', 'N/A')}

h3. Churn Analysis
* Churn Probability: {prediction_metrics.get('churn_probability', 0):.1%}
* Primary Root Cause: {root_cause.get('primary_cause', 'Unknown')}
* Severity: {root_cause.get('severity', 'Unknown')}
* Confidence: {root_cause.get('confidence', 0):.1%}

h3. Contributing Factors
{chr(10).join([f"* {factor}" for factor in root_cause.get('contributing_factors', [])])}

h3. Recommended Actions
{chr(10).join([f"* {action}" for action in root_cause.get('recommended_actions', [])])}

h3. Analysis Context
* Analysis Timestamp: {analysis_result.get('analysis_timestamp', 'N/A')}
* Model Confidence: {analysis_result.get('action_decision', {}).get('confidence', 0):.1%}

---
*This ticket was automatically created by the Agentic AI Churn Prediction System.*
        """
        
        return description.strip()
    
    def _send_email(self, action_decision: Dict, customer_data: Dict, analysis_result: Dict) -> Dict:
        """Send personalized email to customer."""
        
        if not self.sendgrid_client:
            return {
                'action_type': 'email',
                'status': 'failed',
                'reason': 'SendGrid client not initialized'
            }
        
        try:
            # TODO: Replace with your actual email configuration
            from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@yourcompany.com')
            to_email = customer_data.get('email', 'customer@example.com')  # TODO: Add email to customer data
            
            # Create email content
            subject, html_content, text_content = self._create_email_content(action_decision, customer_data, analysis_result)
            
            # Create email
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            # Send email
            response = self.sendgrid_client.send(message)
            
            return {
                'action_type': 'email',
                'status': 'success',
                'sendgrid_message_id': response.headers.get('X-Message-Id'),
                'to_email': to_email,
                'executed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                'action_type': 'email',
                'status': 'failed',
                'reason': str(e)
            }
    
    def _create_email_content(self, action_decision: Dict, customer_data: Dict, analysis_result: Dict) -> tuple:
        """Create personalized email content."""
        
        customer_id = customer_data.get('customer_id')
        monthly_revenue = customer_data.get('monthly_revenue', 0)
        root_cause = analysis_result.get('root_cause_analysis', {})
        
        subject = f"Important: Your Account Needs Attention - {customer_id}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Hello Valued Customer,</h2>
            
            <p>We've noticed some changes in your account activity that we'd like to discuss with you.</p>
            
            <h3>Account Summary</h3>
            <ul>
                <li><strong>Customer ID:</strong> {customer_id}</li>
                <li><strong>Monthly Value:</strong> ${monthly_revenue:,.0f}</li>
                <li><strong>Last Login:</strong> {customer_data.get('days_since_last_login', 'N/A')} days ago</li>
            </ul>
            
            <h3>How We Can Help</h3>
            <p>Our team is here to ensure you're getting the most value from our service. We'd love to:</p>
            <ul>
                <li>Review your current usage and identify optimization opportunities</li>
                <li>Provide additional training or support if needed</li>
                <li>Discuss any challenges you might be facing</li>
                <li>Explore ways to enhance your experience</li>
            </ul>
            
            <h3>Next Steps</h3>
            <p>Please reply to this email or contact our customer success team to schedule a brief call. We're committed to your success!</p>
            
            <p>Best regards,<br>
            Your Customer Success Team</p>
            
            <hr>
            <p><small>This email was sent by our automated customer success system.</small></p>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello Valued Customer,
        
        We've noticed some changes in your account activity that we'd like to discuss with you.
        
        Account Summary:
        - Customer ID: {customer_id}
        - Monthly Value: ${monthly_revenue:,.0f}
        - Last Login: {customer_data.get('days_since_last_login', 'N/A')} days ago
        
        How We Can Help:
        Our team is here to ensure you're getting the most value from our service. We'd love to:
        - Review your current usage and identify optimization opportunities
        - Provide additional training or support if needed
        - Discuss any challenges you might be facing
        - Explore ways to enhance your experience
        
        Next Steps:
        Please reply to this email or contact our customer success team to schedule a brief call. We're committed to your success!
        
        Best regards,
        Your Customer Success Team
        
        ---
        This email was sent by our automated customer success system.
        """
        
        return subject, html_content, text_content.strip()

# Example usage and testing
if __name__ == "__main__":
    # Test the actions module independently
    try:
        executor = ActionExecutor()
        
        # Test with sample data
        sample_action_decision = {
            'action_type': 'slack_alert',
            'priority': 'high',
            'reason': 'High churn risk detected',
            'confidence': 0.85
        }
        
        sample_customer_data = {
            'customer_id': 'CUST123',
            'monthly_revenue': 500,
            'days_since_last_login': 15,
            'email': 'customer@example.com'
        }
        
        sample_analysis_result = {
            'analysis_context': {
                'prediction_metrics': {
                    'churn_probability': 0.75
                }
            },
            'root_cause_analysis': {
                'primary_cause': 'Decreased engagement',
                'severity': 'high'
            }
        }
        
        result = executor.execute_action(
            sample_action_decision,
            sample_customer_data,
            sample_analysis_result
        )
        
        print(f"Action executed: {result['status']}")
        print(f"Action type: {result['action_type']}")
        
    except Exception as e:
        print(f"Actions module test failed: {e}") 