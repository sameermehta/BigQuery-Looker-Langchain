"""
Looker Module for Agentic AI Churn Prediction System
===================================================

This module handles:
- Looker API connection and authentication
- Dashboard and visualization data extraction
- KPI metrics retrieval
- Query execution for context
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from looker_sdk import models40 as models, error
from looker_sdk.rtl import transport
from looker_sdk.rtl import api_methods
from looker_sdk.rtl import auth_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LookerManager:
    """Manages Looker API operations for KPI data and visualizations."""
    
    def __init__(self, config_file: str = None):
        """
        Initialize Looker SDK client.
        
        Args:
            config_file: Path to Looker configuration file (looker.ini)
        """
        # TODO: Replace with your actual Looker configuration
        if config_file:
            os.environ['LOOKERSDK_CONFIG_FILE'] = config_file
        else:
            # Set environment variables for Looker SDK
            # TODO: Replace with your actual Looker instance URL and credentials
            os.environ['LOOKERSDK_BASE_URL'] = os.getenv('LOOKER_BASE_URL', 'https://your-instance.looker.com')
            os.environ['LOOKERSDK_CLIENT_ID'] = os.getenv('LOOKER_CLIENT_ID', 'your-client-id')
            os.environ['LOOKERSDK_CLIENT_SECRET'] = os.getenv('LOOKER_CLIENT_SECRET', 'your-client-secret')
        
        try:
            self.sdk = api_methods.LookerSDK()
            logger.info("Looker SDK client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Looker SDK: {e}")
            raise
    
    def get_dashboard_data(self, dashboard_id: str) -> Dict:
        """
        Fetch dashboard data and visualizations.
        
        Args:
            dashboard_id: Looker dashboard ID
            
        Returns:
            Dictionary containing dashboard data and visualizations
        """
        try:
            # TODO: Replace with your actual dashboard ID
            if dashboard_id == "placeholder":
                dashboard_id = "your-dashboard-id"
            
            logger.info(f"Fetching dashboard data for ID: {dashboard_id}")
            
            # Get dashboard details
            dashboard = self.sdk.dashboard(dashboard_id)
            
            # Get dashboard elements (visualizations)
            dashboard_elements = self.sdk.dashboard_dashboard_elements(dashboard_id)
            
            # Extract data for each visualization
            visualizations = []
            for element in dashboard_elements:
                if element.look_id:
                    look_data = self.get_look_data(element.look_id)
                    visualizations.append({
                        'element_id': element.id,
                        'title': element.title,
                        'type': element.type,
                        'look_id': element.look_id,
                        'data': look_data
                    })
            
            return {
                'dashboard_id': dashboard_id,
                'title': dashboard.title,
                'description': dashboard.description,
                'visualizations': visualizations,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            raise
    
    def get_look_data(self, look_id: str) -> Dict:
        """
        Fetch data from a specific Look.
        
        Args:
            look_id: Looker Look ID
            
        Returns:
            Dictionary containing Look data
        """
        try:
            logger.info(f"Fetching Look data for ID: {look_id}")
            
            # Get Look details
            look = self.sdk.look(look_id)
            
            # Get Look data
            look_data = self.sdk.look_results(look_id)
            
            return {
                'look_id': look_id,
                'title': look.title,
                'description': look.description,
                'query': look.query,
                'data': look_data,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching Look data: {e}")
            raise
    
    def execute_query(self, query: Dict) -> Dict:
        """
        Execute a custom query and return results.
        
        Args:
            query: Query dictionary with model, view, fields, etc.
            
        Returns:
            Dictionary containing query results
        """
        try:
            logger.info("Executing custom query...")
            
            # Create query request
            query_request = models.WriteQuery(
                model=query.get('model'),
                view=query.get('view'),
                fields=query.get('fields', []),
                filters=query.get('filters', {}),
                sorts=query.get('sorts', []),
                limit=query.get('limit', 1000)
            )
            
            # Execute query
            query_result = self.sdk.create_query(query_request)
            query_data = self.sdk.run_query(query_result.id, 'json')
            
            return {
                'query_id': query_result.id,
                'data': query_data,
                'executed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def get_churn_kpis(self) -> Dict:
        """
        Get churn-related KPI metrics from Looker.
        
        Returns:
            Dictionary containing churn KPIs
        """
        try:
            logger.info("Fetching churn KPI metrics...")
            
            # TODO: Replace with your actual Look IDs for churn KPIs
            kpi_looks = {
                'monthly_churn_rate': 'your-monthly-churn-look-id',
                'customer_lifetime_value': 'your-clv-look-id',
                'revenue_churn': 'your-revenue-churn-look-id',
                'active_customers': 'your-active-customers-look-id',
                'support_tickets': 'your-support-tickets-look-id'
            }
            
            kpi_data = {}
            for kpi_name, look_id in kpi_looks.items():
                try:
                    look_data = self.get_look_data(look_id)
                    kpi_data[kpi_name] = look_data
                except Exception as e:
                    logger.warning(f"Could not fetch KPI {kpi_name}: {e}")
                    kpi_data[kpi_name] = None
            
            return {
                'kpis': kpi_data,
                'fetched_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching churn KPIs: {e}")
            raise
    
    def get_customer_insights(self, customer_id: str) -> Dict:
        """
        Get customer-specific insights and metrics.
        
        Args:
            customer_id: Customer ID to get insights for
            
        Returns:
            Dictionary containing customer insights
        """
        try:
            logger.info(f"Fetching insights for customer: {customer_id}")
            
            # TODO: Replace with your actual model and view names
            customer_query = {
                'model': 'your_model',
                'view': 'your_customers_view',
                'fields': [
                    'customers.customer_id',
                    'customers.monthly_revenue',
                    'customers.total_revenue',
                    'customers.days_since_last_login',
                    'customers.login_frequency_30d',
                    'customers.support_tickets_30d'
                ],
                'filters': {
                    'customers.customer_id': customer_id
                },
                'limit': 1
            }
            
            query_result = self.execute_query(customer_query)
            
            return {
                'customer_id': customer_id,
                'insights': query_result,
                'fetched_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching customer insights: {e}")
            raise
    
    def get_trend_data(self, metric: str, days: int = 30) -> Dict:
        """
        Get trend data for a specific metric.
        
        Args:
            metric: Metric to analyze (e.g., 'churn_rate', 'revenue')
            days: Number of days to look back
            
        Returns:
            Dictionary containing trend data
        """
        try:
            logger.info(f"Fetching trend data for {metric} over {days} days...")
            
            # TODO: Replace with your actual model and view names
            trend_query = {
                'model': 'your_model',
                'view': 'your_metrics_view',
                'fields': [
                    'metrics.date',
                    f'metrics.{metric}'
                ],
                'filters': {
                    'metrics.date': f'>= {days} days ago'
                },
                'sorts': ['metrics.date'],
                'limit': days
            }
            
            query_result = self.execute_query(trend_query)
            
            return {
                'metric': metric,
                'trend_data': query_result,
                'period_days': days,
                'fetched_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching trend data: {e}")
            raise
    
    def get_alert_context(self, alert_type: str) -> Dict:
        """
        Get contextual data for alerts and notifications.
        
        Args:
            alert_type: Type of alert (e.g., 'churn_risk', 'anomaly')
            
        Returns:
            Dictionary containing alert context
        """
        try:
            logger.info(f"Fetching context for {alert_type} alert...")
            
            # TODO: Replace with your actual dashboard IDs for different alert types
            alert_dashboards = {
                'churn_risk': 'your-churn-risk-dashboard-id',
                'anomaly': 'your-anomaly-dashboard-id',
                'revenue_drop': 'your-revenue-dashboard-id',
                'support_spike': 'your-support-dashboard-id'
            }
            
            dashboard_id = alert_dashboards.get(alert_type)
            if dashboard_id:
                dashboard_data = self.get_dashboard_data(dashboard_id)
                kpi_data = self.get_churn_kpis()
                
                return {
                    'alert_type': alert_type,
                    'dashboard_context': dashboard_data,
                    'kpi_context': kpi_data,
                    'fetched_at': datetime.now().isoformat()
                }
            else:
                logger.warning(f"No dashboard configured for alert type: {alert_type}")
                return {
                    'alert_type': alert_type,
                    'error': 'No dashboard configured for this alert type'
                }
                
        except Exception as e:
            logger.error(f"Error fetching alert context: {e}")
            raise

# Example usage and testing
if __name__ == "__main__":
    # Test the Looker module independently
    try:
        looker_manager = LookerManager()
        
        # Test KPI fetching
        kpis = looker_manager.get_churn_kpis()
        print(f"Fetched {len(kpis['kpis'])} KPIs")
        
        # Test trend data
        trend_data = looker_manager.get_trend_data('churn_rate', days=30)
        print(f"Fetched trend data for churn_rate")
        
    except Exception as e:
        print(f"Looker module test failed: {e}") 