"""
Agent Reasoning Module for Agentic AI Churn Prediction System
============================================================

This module handles:
- LangChain-based reasoning logic
- OpenAI integration for decision making
- Root cause analysis
- Action determination (Slack, Jira, Email)
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionDecision(BaseModel):
    """Structured output for action decisions."""
    action_type: str = Field(description="Type of action: 'slack_alert', 'jira_ticket', 'email', or 'none'")
    priority: str = Field(description="Priority level: 'high', 'medium', 'low'")
    reason: str = Field(description="Reasoning for the action decision")
    action_details: Dict = Field(description="Specific details for the action")
    confidence: float = Field(description="Confidence score (0-1)")

class RootCauseAnalysis(BaseModel):
    """Structured output for root cause analysis."""
    primary_cause: str = Field(description="Primary root cause of the issue")
    contributing_factors: List[str] = Field(description="List of contributing factors")
    severity: str = Field(description="Severity: 'critical', 'high', 'medium', 'low'")
    recommended_actions: List[str] = Field(description="List of recommended actions")
    confidence: float = Field(description="Confidence score (0-1)")

class AgentReasoning:
    """Manages LangChain-based reasoning for churn prediction and action determination."""
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1):
        """
        Initialize the reasoning agent.
        
        Args:
            model_name: OpenAI model to use
            temperature: Model temperature for creativity vs consistency
        """
        # TODO: Replace with your actual OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OPENAI_API_KEY not found. Please set the environment variable.")
            api_key = "your-openai-api-key"
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=api_key
        )
        
        self.action_parser = PydanticOutputParser(pydantic_object=ActionDecision)
        self.cause_parser = PydanticOutputParser(pydantic_object=RootCauseAnalysis)
        
        logger.info(f"Agent reasoning initialized with model: {model_name}")
    
    def analyze_churn_risk(self, customer_data: Dict, prediction_data: Dict, kpi_context: Dict) -> Dict:
        """
        Analyze churn risk and determine appropriate actions.
        
        Args:
            customer_data: Customer context and metrics
            prediction_data: Churn prediction results
            kpi_context: KPI data from Looker
            
        Returns:
            Dictionary containing analysis results and action decisions
        """
        try:
            logger.info(f"Analyzing churn risk for customer: {customer_data.get('customer_id')}")
            
            # Prepare context for analysis
            analysis_context = self._prepare_analysis_context(customer_data, prediction_data, kpi_context)
            
            # Perform root cause analysis
            root_cause = self._analyze_root_cause(analysis_context)
            
            # Determine action based on analysis
            action_decision = self._determine_action(analysis_context, root_cause)
            
            return {
                'customer_id': customer_data.get('customer_id'),
                'analysis_timestamp': datetime.now().isoformat(),
                'root_cause_analysis': root_cause,
                'action_decision': action_decision,
                'analysis_context': analysis_context
            }
            
        except Exception as e:
            logger.error(f"Error analyzing churn risk: {e}")
            raise
    
    def _prepare_analysis_context(self, customer_data: Dict, prediction_data: Dict, kpi_context: Dict) -> Dict:
        """Prepare comprehensive context for analysis."""
        
        # Extract key metrics
        customer_metrics = {
            'customer_id': customer_data.get('customer_id'),
            'monthly_revenue': customer_data.get('monthly_revenue'),
            'total_revenue': customer_data.get('total_revenue'),
            'days_since_last_login': customer_data.get('days_since_last_login'),
            'login_frequency_30d': customer_data.get('login_frequency_30d'),
            'purchase_frequency_30d': customer_data.get('purchase_frequency_30d'),
            'support_tickets_30d': customer_data.get('support_tickets_30d'),
            'feature_usage_count': customer_data.get('feature_usage_count')
        }
        
        # Extract prediction data
        prediction_metrics = {
            'churn_probability': prediction_data.get('predicted_churned_flag_probs', [0, 0])[1],
            'predicted_churn': prediction_data.get('predicted_churned_flag', 0)
        }
        
        # Extract KPI context
        kpi_metrics = {}
        if kpi_context and 'kpis' in kpi_context:
            for kpi_name, kpi_data in kpi_context['kpis'].items():
                if kpi_data and 'data' in kpi_data:
                    kpi_metrics[kpi_name] = kpi_data['data']
        
        return {
            'customer_metrics': customer_metrics,
            'prediction_metrics': prediction_metrics,
            'kpi_metrics': kpi_metrics,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _analyze_root_cause(self, analysis_context: Dict) -> Dict:
        """Analyze root cause of churn risk using LLM reasoning."""
        
        # Create prompt for root cause analysis
        root_cause_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert customer success analyst specializing in churn prediction and root cause analysis. 
            
            Analyze the provided customer data and determine the most likely root cause of churn risk.
            
            Consider:
            1. Customer behavior patterns
            2. Revenue trends
            3. Engagement metrics
            4. Support interactions
            5. Feature usage patterns
            
            Provide a structured analysis with:
            - Primary root cause
            - Contributing factors
            - Severity assessment
            - Recommended actions
            - Confidence level"""),
            ("human", """Customer Analysis Context:
            
            Customer Metrics:
            {customer_metrics}
            
            Churn Prediction:
            {prediction_metrics}
            
            KPI Context:
            {kpi_metrics}
            
            Please analyze the root cause of this customer's churn risk and provide your assessment in the specified format.""")
        ])
        
        try:
            # Format the prompt
            formatted_prompt = root_cause_prompt.format_messages(
                customer_metrics=json.dumps(analysis_context['customer_metrics'], indent=2),
                prediction_metrics=json.dumps(analysis_context['prediction_metrics'], indent=2),
                kpi_metrics=json.dumps(analysis_context['kpi_metrics'], indent=2)
            )
            
            # Get LLM response
            response = self.llm.invoke(formatted_prompt)
            
            # Parse the response
            try:
                root_cause = self.cause_parser.parse(response.content)
                return root_cause.dict()
            except Exception as parse_error:
                logger.warning(f"Failed to parse structured response: {parse_error}")
                # Fallback to manual parsing
                return self._parse_root_cause_fallback(response.content)
                
        except Exception as e:
            logger.error(f"Error in root cause analysis: {e}")
            return {
                'primary_cause': 'Analysis failed',
                'contributing_factors': [],
                'severity': 'unknown',
                'recommended_actions': [],
                'confidence': 0.0
            }
    
    def _determine_action(self, analysis_context: Dict, root_cause: Dict) -> Dict:
        """Determine appropriate action based on analysis."""
        
        # Create prompt for action determination
        action_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an automated customer success agent that determines appropriate actions based on churn risk analysis.
            
            Available actions:
            1. slack_alert - Send immediate alert to customer success team
            2. jira_ticket - Create detailed ticket for investigation
            3. email - Send personalized email to customer
            4. none - No action needed
            
            Consider:
            - Churn probability
            - Customer value (revenue)
            - Severity of issues
            - Urgency of response needed
            - Available team resources
            
            Provide structured decision with:
            - Action type
            - Priority level
            - Reasoning
            - Action details
            - Confidence level"""),
            ("human", """Analysis Results:
            
            Root Cause Analysis:
            {root_cause}
            
            Customer Context:
            {customer_metrics}
            
            Churn Prediction:
            {prediction_metrics}
            
            Determine the most appropriate action for this customer.""")
        ])
        
        try:
            # Format the prompt
            formatted_prompt = action_prompt.format_messages(
                root_cause=json.dumps(root_cause, indent=2),
                customer_metrics=json.dumps(analysis_context['customer_metrics'], indent=2),
                prediction_metrics=json.dumps(analysis_context['prediction_metrics'], indent=2)
            )
            
            # Get LLM response
            response = self.llm.invoke(formatted_prompt)
            
            # Parse the response
            try:
                action_decision = self.action_parser.parse(response.content)
                return action_decision.dict()
            except Exception as parse_error:
                logger.warning(f"Failed to parse structured response: {parse_error}")
                # Fallback to manual parsing
                return self._parse_action_fallback(response.content)
                
        except Exception as e:
            logger.error(f"Error in action determination: {e}")
            return {
                'action_type': 'none',
                'priority': 'low',
                'reason': 'Analysis failed',
                'action_details': {},
                'confidence': 0.0
            }
    
    def _parse_root_cause_fallback(self, response_content: str) -> Dict:
        """Fallback parser for root cause analysis."""
        try:
            # Simple keyword-based parsing
            content_lower = response_content.lower()
            
            # Determine severity
            if any(word in content_lower for word in ['critical', 'severe', 'urgent']):
                severity = 'critical'
            elif any(word in content_lower for word in ['high', 'significant']):
                severity = 'high'
            elif any(word in content_lower for word in ['medium', 'moderate']):
                severity = 'medium'
            else:
                severity = 'low'
            
            return {
                'primary_cause': 'Analysis completed (fallback parsing)',
                'contributing_factors': ['Unable to parse specific factors'],
                'severity': severity,
                'recommended_actions': ['Review customer manually'],
                'confidence': 0.5
            }
        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}")
            return {
                'primary_cause': 'Analysis failed',
                'contributing_factors': [],
                'severity': 'unknown',
                'recommended_actions': [],
                'confidence': 0.0
            }
    
    def _parse_action_fallback(self, response_content: str) -> Dict:
        """Fallback parser for action determination."""
        try:
            content_lower = response_content.lower()
            
            # Determine action type
            if 'slack' in content_lower:
                action_type = 'slack_alert'
            elif 'jira' in content_lower or 'ticket' in content_lower:
                action_type = 'jira_ticket'
            elif 'email' in content_lower:
                action_type = 'email'
            else:
                action_type = 'none'
            
            # Determine priority
            if any(word in content_lower for word in ['high', 'urgent', 'critical']):
                priority = 'high'
            elif any(word in content_lower for word in ['medium', 'moderate']):
                priority = 'medium'
            else:
                priority = 'low'
            
            return {
                'action_type': action_type,
                'priority': priority,
                'reason': 'Analysis completed (fallback parsing)',
                'action_details': {},
                'confidence': 0.5
            }
        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}")
            return {
                'action_type': 'none',
                'priority': 'low',
                'reason': 'Analysis failed',
                'action_details': {},
                'confidence': 0.0
            }
    
    def analyze_anomaly(self, customer_data: Dict, anomaly_data: Dict, kpi_context: Dict) -> Dict:
        """
        Analyze anomalies and determine appropriate actions.
        
        Args:
            customer_data: Customer context and metrics
            anomaly_data: Anomaly detection results
            kpi_context: KPI data from Looker
            
        Returns:
            Dictionary containing analysis results and action decisions
        """
        try:
            logger.info(f"Analyzing anomaly for customer: {customer_data.get('customer_id')}")
            
            # Prepare context for anomaly analysis
            analysis_context = self._prepare_anomaly_context(customer_data, anomaly_data, kpi_context)
            
            # Perform root cause analysis
            root_cause = self._analyze_anomaly_root_cause(analysis_context)
            
            # Determine action based on analysis
            action_decision = self._determine_anomaly_action(analysis_context, root_cause)
            
            return {
                'customer_id': customer_data.get('customer_id'),
                'analysis_timestamp': datetime.now().isoformat(),
                'anomaly_type': anomaly_data.get('anomaly_flag'),
                'z_score': anomaly_data.get('z_score'),
                'root_cause_analysis': root_cause,
                'action_decision': action_decision,
                'analysis_context': analysis_context
            }
            
        except Exception as e:
            logger.error(f"Error analyzing anomaly: {e}")
            raise
    
    def _prepare_anomaly_context(self, customer_data: Dict, anomaly_data: Dict, kpi_context: Dict) -> Dict:
        """Prepare context for anomaly analysis."""
        
        return {
            'customer_metrics': customer_data,
            'anomaly_metrics': {
                'z_score': anomaly_data.get('z_score'),
                'anomaly_flag': anomaly_data.get('anomaly_flag'),
                'metric_value': anomaly_data.get('metric_value')
            },
            'kpi_metrics': kpi_context.get('kpis', {}),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _analyze_anomaly_root_cause(self, analysis_context: Dict) -> Dict:
        """Analyze root cause of anomaly using LLM reasoning."""
        # Similar to _analyze_root_cause but focused on anomalies
        # Implementation would be similar with anomaly-specific prompts
        return self._analyze_root_cause(analysis_context)
    
    def _determine_anomaly_action(self, analysis_context: Dict, root_cause: Dict) -> Dict:
        """Determine appropriate action for anomalies."""
        # Similar to _determine_action but with anomaly-specific logic
        return self._determine_action(analysis_context, root_cause)

# Example usage and testing
if __name__ == "__main__":
    # Test the agent reasoning module independently
    try:
        agent = AgentReasoning()
        
        # Test with sample data
        sample_customer_data = {
            'customer_id': 'CUST123',
            'monthly_revenue': 500,
            'days_since_last_login': 15,
            'login_frequency_30d': 2,
            'support_tickets_30d': 3
        }
        
        sample_prediction_data = {
            'predicted_churned_flag': 1,
            'predicted_churned_flag_probs': [0.3, 0.7]
        }
        
        sample_kpi_context = {
            'kpis': {
                'monthly_churn_rate': {'data': 0.05},
                'revenue_churn': {'data': 0.03}
            }
        }
        
        analysis_result = agent.analyze_churn_risk(
            sample_customer_data, 
            sample_prediction_data, 
            sample_kpi_context
        )
        
        print("Analysis completed successfully")
        print(f"Action decided: {analysis_result['action_decision']['action_type']}")
        
    except Exception as e:
        print(f"Agent reasoning test failed: {e}") 