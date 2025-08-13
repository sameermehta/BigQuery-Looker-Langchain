"""
BigQuery Module for Agentic AI Churn Prediction System
======================================================

This module handles:
- BigQuery connection and authentication
- Churn prediction model execution
- Anomaly detection
- Data extraction and logging
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BigQueryManager:
    """Manages BigQuery operations for churn prediction and anomaly detection."""
    
    def __init__(self, project_id: str = None, credentials_path: str = None):
        """
        Initialize BigQuery client.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON file
        """
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        
        # TODO: Replace with your actual project ID
        if not self.project_id:
            self.project_id = "your-gcp-project-id"
            logger.warning("Using placeholder project ID. Please set GCP_PROJECT_ID environment variable.")
        
        # Initialize BigQuery client
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = bigquery.Client(credentials=credentials, project=self.project_id)
        else:
            # Use default credentials (Application Default Credentials)
            self.client = bigquery.Client(project=self.project_id)
        
        logger.info(f"BigQuery client initialized for project: {self.project_id}")
    
    def extract_churn_data(self, days_back: int = 30) -> pd.DataFrame:
        """
        Extract churn-related data from BigQuery.
        
        Args:
            days_back: Number of days of historical data to extract
            
        Returns:
            DataFrame with churn-related features
        """
        # TODO: Replace with your actual table names and schema
        query = f"""
        SELECT 
            customer_id,
            subscription_id,
            subscription_start_date,
            subscription_end_date,
            monthly_revenue,
            total_revenue,
            days_since_last_purchase,
            days_since_last_login,
            login_frequency_30d,
            purchase_frequency_30d,
            support_tickets_30d,
            feature_usage_count,
            churned_flag,
            churn_date,
            created_at,
            updated_at
        FROM `{self.project_id}.your_dataset.your_customers_table`
        WHERE created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
        ORDER BY created_at DESC
        """
        
        try:
            logger.info(f"Extracting churn data for last {days_back} days...")
            df = self.client.query(query).to_dataframe()
            logger.info(f"Extracted {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error extracting churn data: {e}")
            raise
    
    def create_churn_prediction_model(self, model_name: str = "churn_prediction_model"):
        """
        Create and train a churn prediction model using BigQuery ML.
        
        Args:
            model_name: Name of the model to create
        """
        # TODO: Replace with your actual table names and adjust features
        create_model_query = f"""
        CREATE OR REPLACE MODEL `{self.project_id}.your_dataset.{model_name}`
        OPTIONS(
            model_type='logistic_reg',
            auto_class_weights=true,
            input_label_cols=['churned_flag']
        ) AS
        SELECT 
            customer_id,
            subscription_id,
            monthly_revenue,
            total_revenue,
            days_since_last_purchase,
            days_since_last_login,
            login_frequency_30d,
            purchase_frequency_30d,
            support_tickets_30d,
            feature_usage_count,
            churned_flag
        FROM `{self.project_id}.your_dataset.your_customers_table`
        WHERE churned_flag IS NOT NULL
        AND created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        """
        
        try:
            logger.info(f"Creating churn prediction model: {model_name}")
            job = self.client.query(create_model_query)
            job.result()  # Wait for the job to complete
            logger.info(f"Model {model_name} created successfully")
        except Exception as e:
            logger.error(f"Error creating model: {e}")
            raise
    
    def predict_churn(self, model_name: str = "churn_prediction_model") -> pd.DataFrame:
        """
        Run churn prediction on recent customer data.
        
        Args:
            model_name: Name of the trained model
            
        Returns:
            DataFrame with predictions and probabilities
        """
        # TODO: Replace with your actual table names
        prediction_query = f"""
        SELECT 
            customer_id,
            subscription_id,
            monthly_revenue,
            days_since_last_purchase,
            days_since_last_login,
            login_frequency_30d,
            purchase_frequency_30d,
            support_tickets_30d,
            feature_usage_count,
            predicted_churned_flag,
            predicted_churned_flag_probs
        FROM ML.PREDICT(
            MODEL `{self.project_id}.your_dataset.{model_name}`,
            (SELECT 
                customer_id,
                subscription_id,
                monthly_revenue,
                days_since_last_purchase,
                days_since_last_login,
                login_frequency_30d,
                purchase_frequency_30d,
                support_tickets_30d,
                feature_usage_count
            FROM `{self.project_id}.your_dataset.your_customers_table`
            WHERE churned_flag IS NULL
            AND created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY))
        )
        WHERE predicted_churned_flag = 1
        ORDER BY predicted_churned_flag_probs[OFFSET(1)] DESC
        """
        
        try:
            logger.info("Running churn prediction...")
            df = self.client.query(prediction_query).to_dataframe()
            logger.info(f"Found {len(df)} customers at risk of churning")
            return df
        except Exception as e:
            logger.error(f"Error running churn prediction: {e}")
            raise
    
    def detect_anomalies(self, metric: str, threshold: float = 2.0) -> pd.DataFrame:
        """
        Detect anomalies in customer behavior metrics.
        
        Args:
            metric: Metric to analyze (e.g., 'login_frequency_30d', 'monthly_revenue')
            threshold: Standard deviations for anomaly detection
            
        Returns:
            DataFrame with anomalous customers
        """
        # TODO: Replace with your actual table names
        anomaly_query = f"""
        WITH metric_stats AS (
            SELECT 
                AVG({metric}) as avg_metric,
                STDDEV({metric}) as std_metric
            FROM `{self.project_id}.your_dataset.your_customers_table`
            WHERE created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        )
        SELECT 
            c.customer_id,
            c.subscription_id,
            c.{metric},
            (c.{metric} - ms.avg_metric) / ms.std_metric as z_score,
            CASE 
                WHEN ABS((c.{metric} - ms.avg_metric) / ms.std_metric) > {threshold} 
                THEN 'ANOMALY' 
                ELSE 'NORMAL' 
            END as anomaly_flag
        FROM `{self.project_id}.your_dataset.your_customers_table` c
        CROSS JOIN metric_stats ms
        WHERE c.created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        AND ABS((c.{metric} - ms.avg_metric) / ms.std_metric) > {threshold}
        ORDER BY ABS((c.{metric} - ms.avg_metric) / ms.std_metric) DESC
        """
        
        try:
            logger.info(f"Detecting anomalies in {metric}...")
            df = self.client.query(anomaly_query).to_dataframe()
            logger.info(f"Found {len(df)} anomalies in {metric}")
            return df
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise
    
    def log_action_outcome(self, action_data: Dict) -> None:
        """
        Log action outcomes back to BigQuery for model retraining.
        
        Args:
            action_data: Dictionary containing action details and outcomes
        """
        # TODO: Replace with your actual table name
        insert_query = f"""
        INSERT INTO `{self.project_id}.your_dataset.action_logs`
        (customer_id, action_type, action_details, outcome, created_at)
        VALUES
        (@customer_id, @action_type, @action_details, @outcome, @created_at)
        """
        
        try:
            query_config = QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("customer_id", "STRING", action_data.get('customer_id')),
                    bigquery.ScalarQueryParameter("action_type", "STRING", action_data.get('action_type')),
                    bigquery.ScalarQueryParameter("action_details", "STRING", str(action_data.get('action_details'))),
                    bigquery.ScalarQueryParameter("outcome", "STRING", action_data.get('outcome')),
                    bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", datetime.now())
                ]
            )
            
            job = self.client.query(insert_query, job_config=query_config)
            job.result()
            logger.info(f"Action outcome logged for customer {action_data.get('customer_id')}")
        except Exception as e:
            logger.error(f"Error logging action outcome: {e}")
            raise
    
    def get_customer_context(self, customer_id: str) -> Dict:
        """
        Get comprehensive customer context for reasoning.
        
        Args:
            customer_id: Customer ID to get context for
            
        Returns:
            Dictionary with customer context
        """
        # TODO: Replace with your actual table names
        context_query = f"""
        SELECT 
            customer_id,
            subscription_id,
            subscription_start_date,
            monthly_revenue,
            total_revenue,
            days_since_last_purchase,
            days_since_last_login,
            login_frequency_30d,
            purchase_frequency_30d,
            support_tickets_30d,
            feature_usage_count,
            churned_flag,
            created_at
        FROM `{self.project_id}.your_dataset.your_customers_table`
        WHERE customer_id = @customer_id
        """
        
        try:
            query_config = QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id)
                ]
            )
            
            df = self.client.query(context_query, job_config=query_config).to_dataframe()
            if not df.empty:
                return df.iloc[0].to_dict()
            else:
                logger.warning(f"No data found for customer {customer_id}")
                return {}
        except Exception as e:
            logger.error(f"Error getting customer context: {e}")
            return {}

# Example usage and testing
if __name__ == "__main__":
    # Test the BigQuery module independently
    bq_manager = BigQueryManager()
    
    # Test data extraction
    try:
        churn_data = bq_manager.extract_churn_data(days_back=30)
        print(f"Extracted {len(churn_data)} records")
    except Exception as e:
        print(f"Data extraction test failed: {e}")
    
    # Test anomaly detection
    try:
        anomalies = bq_manager.detect_anomalies('login_frequency_30d', threshold=2.0)
        print(f"Found {len(anomalies)} anomalies")
    except Exception as e:
        print(f"Anomaly detection test failed: {e}") 