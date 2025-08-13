"""
Main Orchestration Script for Agentic AI Churn Prediction System
===============================================================

This script orchestrates the complete workflow:
1. Extract data from BigQuery
2. Run churn prediction and anomaly detection
3. Fetch KPI context from Looker
4. Use LLM reasoning to analyze and decide actions
5. Execute actions (Slack, Jira, Email)
6. Log outcomes back to BigQuery
"""

import os
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Import our modules
from bigquery_module import BigQueryManager
from looker_module import LookerManager
from agent_reasoning import AgentReasoning
from actions_module import ActionExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agentic_ai_churn.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgenticAIChurnSystem:
    """Main orchestrator for the Agentic AI Churn Prediction System."""
    
    def __init__(self):
        """Initialize all system components."""
        logger.info("Initializing Agentic AI Churn Prediction System...")
        
        # Initialize all modules
        self.bq_manager = BigQueryManager()
        self.looker_manager = LookerManager()
        self.agent_reasoning = AgentReasoning()
        self.action_executor = ActionExecutor()
        
        logger.info("System initialization completed")
    
    def run_churn_analysis_cycle(self) -> Dict:
        """
        Run a complete churn analysis cycle.
        
        Returns:
            Dictionary containing cycle results and statistics
        """
        cycle_start = datetime.now()
        logger.info("Starting churn analysis cycle...")
        
        cycle_results = {
            'cycle_start': cycle_start.isoformat(),
            'customers_analyzed': 0,
            'churn_predictions': 0,
            'anomalies_detected': 0,
            'actions_executed': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'errors': []
        }
        
        try:
            # Step 1: Extract churn data from BigQuery
            logger.info("Step 1: Extracting churn data from BigQuery...")
            churn_data = self.bq_manager.extract_churn_data(days_back=30)
            cycle_results['customers_analyzed'] = len(churn_data)
            logger.info(f"Extracted data for {len(churn_data)} customers")
            
            # Step 2: Run churn prediction
            logger.info("Step 2: Running churn prediction...")
            churn_predictions = self.bq_manager.predict_churn()
            cycle_results['churn_predictions'] = len(churn_predictions)
            logger.info(f"Found {len(churn_predictions)} customers at risk of churning")
            
            # Step 3: Detect anomalies
            logger.info("Step 3: Detecting anomalies...")
            anomalies = self._detect_all_anomalies()
            cycle_results['anomalies_detected'] = len(anomalies)
            logger.info(f"Detected {len(anomalies)} anomalies")
            
            # Step 4: Get KPI context from Looker
            logger.info("Step 4: Fetching KPI context from Looker...")
            kpi_context = self.looker_manager.get_churn_kpis()
            logger.info("KPI context fetched successfully")
            
            # Step 5: Process each customer at risk
            logger.info("Step 5: Processing customers at risk...")
            for _, customer_prediction in churn_predictions.iterrows():
                try:
                    self._process_customer_risk(customer_prediction, kpi_context, cycle_results)
                except Exception as e:
                    error_msg = f"Error processing customer {customer_prediction.get('customer_id')}: {e}"
                    logger.error(error_msg)
                    cycle_results['errors'].append(error_msg)
            
            # Step 6: Process anomalies
            logger.info("Step 6: Processing anomalies...")
            for _, anomaly in anomalies.iterrows():
                try:
                    self._process_anomaly(anomaly, kpi_context, cycle_results)
                except Exception as e:
                    error_msg = f"Error processing anomaly for customer {anomaly.get('customer_id')}: {e}"
                    logger.error(error_msg)
                    cycle_results['errors'].append(error_msg)
            
            cycle_end = datetime.now()
            cycle_results['cycle_end'] = cycle_end.isoformat()
            cycle_results['cycle_duration_seconds'] = (cycle_end - cycle_start).total_seconds()
            
            logger.info(f"Churn analysis cycle completed in {cycle_results['cycle_duration_seconds']:.2f} seconds")
            logger.info(f"Actions executed: {cycle_results['actions_executed']} (Success: {cycle_results['successful_actions']}, Failed: {cycle_results['failed_actions']})")
            
            return cycle_results
            
        except Exception as e:
            error_msg = f"Critical error in churn analysis cycle: {e}"
            logger.error(error_msg)
            cycle_results['errors'].append(error_msg)
            return cycle_results
    
    def _detect_all_anomalies(self) -> List[Dict]:
        """Detect anomalies across multiple metrics."""
        all_anomalies = []
        
        # Define metrics to monitor for anomalies
        metrics_to_monitor = [
            'login_frequency_30d',
            'purchase_frequency_30d',
            'support_tickets_30d',
            'monthly_revenue'
        ]
        
        for metric in metrics_to_monitor:
            try:
                anomalies = self.bq_manager.detect_anomalies(metric, threshold=2.0)
                for _, anomaly in anomalies.iterrows():
                    anomaly_dict = anomaly.to_dict()
                    anomaly_dict['metric_name'] = metric
                    all_anomalies.append(anomaly_dict)
            except Exception as e:
                logger.warning(f"Failed to detect anomalies for metric {metric}: {e}")
        
        return all_anomalies
    
    def _process_customer_risk(self, customer_prediction: Dict, kpi_context: Dict, cycle_results: Dict) -> None:
        """Process a single customer at risk of churning."""
        
        customer_id = customer_prediction.get('customer_id')
        logger.info(f"Processing churn risk for customer: {customer_id}")
        
        # Get customer context
        customer_data = self.bq_manager.get_customer_context(customer_id)
        if not customer_data:
            logger.warning(f"No customer data found for {customer_id}")
            return
        
        # Analyze churn risk using LLM reasoning
        analysis_result = self.agent_reasoning.analyze_churn_risk(
            customer_data, 
            customer_prediction, 
            kpi_context
        )
        
        # Execute action based on analysis
        action_decision = analysis_result.get('action_decision', {})
        if action_decision.get('action_type') != 'none':
            cycle_results['actions_executed'] += 1
            
            action_result = self.action_executor.execute_action(
                action_decision,
                customer_data,
                analysis_result
            )
            
            if action_result.get('status') == 'success':
                cycle_results['successful_actions'] += 1
            else:
                cycle_results['failed_actions'] += 1
            
            # Log action outcome back to BigQuery
            self._log_action_outcome(action_result, analysis_result)
    
    def _process_anomaly(self, anomaly: Dict, kpi_context: Dict, cycle_results: Dict) -> None:
        """Process a single anomaly detection."""
        
        customer_id = anomaly.get('customer_id')
        metric_name = anomaly.get('metric_name', 'unknown')
        logger.info(f"Processing anomaly for customer {customer_id} in metric {metric_name}")
        
        # Get customer context
        customer_data = self.bq_manager.get_customer_context(customer_id)
        if not customer_data:
            logger.warning(f"No customer data found for {customer_id}")
            return
        
        # Analyze anomaly using LLM reasoning
        analysis_result = self.agent_reasoning.analyze_anomaly(
            customer_data,
            anomaly,
            kpi_context
        )
        
        # Execute action based on analysis
        action_decision = analysis_result.get('action_decision', {})
        if action_decision.get('action_type') != 'none':
            cycle_results['actions_executed'] += 1
            
            action_result = self.action_executor.execute_action(
                action_decision,
                customer_data,
                analysis_result
            )
            
            if action_result.get('status') == 'success':
                cycle_results['successful_actions'] += 1
            else:
                cycle_results['failed_actions'] += 1
            
            # Log action outcome back to BigQuery
            self._log_action_outcome(action_result, analysis_result)
    
    def _log_action_outcome(self, action_result: Dict, analysis_result: Dict) -> None:
        """Log action outcomes back to BigQuery for model retraining."""
        
        try:
            action_data = {
                'customer_id': action_result.get('customer_id'),
                'action_type': action_result.get('action_type'),
                'action_details': {
                    'priority': action_result.get('priority'),
                    'confidence': action_result.get('confidence'),
                    'status': action_result.get('status'),
                    'reason': action_result.get('reason')
                },
                'outcome': action_result.get('status'),
                'analysis_context': analysis_result.get('analysis_context', {})
            }
            
            self.bq_manager.log_action_outcome(action_data)
            logger.info(f"Action outcome logged for customer {action_data['customer_id']}")
            
        except Exception as e:
            logger.error(f"Failed to log action outcome: {e}")
    
    def run_scheduled_analysis(self, interval_minutes: int = 60) -> None:
        """
        Run the analysis on a scheduled basis.
        
        Args:
            interval_minutes: Interval between analysis runs in minutes
        """
        logger.info(f"Starting scheduled analysis every {interval_minutes} minutes...")
        
        # Schedule the analysis
        schedule.every(interval_minutes).minutes.do(self.run_churn_analysis_cycle)
        
        # Run initial analysis
        logger.info("Running initial analysis...")
        self.run_churn_analysis_cycle()
        
        # Keep running scheduled tasks
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduled analysis stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduled analysis: {e}")
                time.sleep(60)  # Wait before retrying
    
    def run_single_analysis(self) -> Dict:
        """
        Run a single analysis cycle.
        
        Returns:
            Dictionary containing analysis results
        """
        logger.info("Running single analysis cycle...")
        return self.run_churn_analysis_cycle()
    
    def test_system_components(self) -> Dict:
        """
        Test all system components independently.
        
        Returns:
            Dictionary containing test results
        """
        logger.info("Testing system components...")
        
        test_results = {
            'bigquery': {'status': 'unknown', 'error': None},
            'looker': {'status': 'unknown', 'error': None},
            'agent_reasoning': {'status': 'unknown', 'error': None},
            'action_executor': {'status': 'unknown', 'error': None}
        }
        
        # Test BigQuery
        try:
            test_data = self.bq_manager.extract_churn_data(days_back=1)
            test_results['bigquery'] = {'status': 'success', 'records': len(test_data)}
        except Exception as e:
            test_results['bigquery'] = {'status': 'failed', 'error': str(e)}
        
        # Test Looker
        try:
            test_kpis = self.looker_manager.get_churn_kpis()
            test_results['looker'] = {'status': 'success', 'kpis': len(test_kpis.get('kpis', {}))}
        except Exception as e:
            test_results['looker'] = {'status': 'failed', 'error': str(e)}
        
        # Test Agent Reasoning
        try:
            sample_data = {
                'customer_id': 'TEST123',
                'monthly_revenue': 100,
                'days_since_last_login': 10
            }
            sample_prediction = {
                'predicted_churned_flag': 1,
                'predicted_churned_flag_probs': [0.2, 0.8]
            }
            sample_kpis = {'kpis': {}}
            
            test_analysis = self.agent_reasoning.analyze_churn_risk(
                sample_data, sample_prediction, sample_kpis
            )
            test_results['agent_reasoning'] = {'status': 'success', 'action_type': test_analysis.get('action_decision', {}).get('action_type')}
        except Exception as e:
            test_results['agent_reasoning'] = {'status': 'failed', 'error': str(e)}
        
        # Test Action Executor
        try:
            test_action = {
                'action_type': 'none',
                'priority': 'low',
                'reason': 'Test action',
                'confidence': 0.5
            }
            test_customer = {'customer_id': 'TEST123'}
            test_analysis = {'analysis_context': {}}
            
            test_result = self.action_executor.execute_action(
                test_action, test_customer, test_analysis
            )
            test_results['action_executor'] = {'status': 'success', 'result': test_result.get('status')}
        except Exception as e:
            test_results['action_executor'] = {'status': 'failed', 'error': str(e)}
        
        logger.info("System component testing completed")
        return test_results

def main():
    """Main entry point for the Agentic AI Churn Prediction System."""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize the system
    system = AgenticAIChurnSystem()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Agentic AI Churn Prediction System')
    parser.add_argument('--mode', choices=['single', 'scheduled', 'test'], default='single',
                       help='Run mode: single analysis, scheduled analysis, or component testing')
    parser.add_argument('--interval', type=int, default=60,
                       help='Interval in minutes for scheduled mode (default: 60)')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'test':
            # Test system components
            test_results = system.test_system_components()
            print("\n=== System Component Test Results ===")
            for component, result in test_results.items():
                status = result['status']
                if status == 'success':
                    print(f"✅ {component}: {status}")
                else:
                    print(f"❌ {component}: {status} - {result.get('error', 'Unknown error')}")
        
        elif args.mode == 'scheduled':
            # Run scheduled analysis
            system.run_scheduled_analysis(args.interval)
        
        else:
            # Run single analysis
            results = system.run_single_analysis()
            print("\n=== Analysis Cycle Results ===")
            print(f"Customers Analyzed: {results['customers_analyzed']}")
            print(f"Churn Predictions: {results['churn_predictions']}")
            print(f"Anomalies Detected: {results['anomalies_detected']}")
            print(f"Actions Executed: {results['actions_executed']}")
            print(f"Successful Actions: {results['successful_actions']}")
            print(f"Failed Actions: {results['failed_actions']}")
            print(f"Cycle Duration: {results.get('cycle_duration_seconds', 0):.2f} seconds")
            
            if results['errors']:
                print(f"\nErrors: {len(results['errors'])}")
                for error in results['errors'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
    
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"Critical system error: {e}")
        raise

if __name__ == "__main__":
    main() 