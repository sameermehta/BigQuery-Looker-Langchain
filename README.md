# Agentic AI Churn Prediction System

An intelligent, automated system that predicts customer churn, analyzes root causes using AI reasoning, and executes appropriate actions to prevent customer loss.

## 🚀 Overview

This system combines the power of:
- **BigQuery ML** for churn prediction and anomaly detection
- **Looker API** for KPI context and business intelligence
- **LangChain + OpenAI** for intelligent reasoning and decision making
- **Multi-channel actions** (Slack, Jira, Email) for automated interventions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   BigQuery      │    │     Looker      │    │   OpenAI        │
│   - Data        │    │   - KPIs        │    │   - Reasoning    │
│   - ML Models   │    │   - Context     │    │   - Decisions    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Agentic AI    │
                    │   Orchestrator  │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Slack       │    │      Jira       │    │     Email       │
│   - Alerts      │    │   - Tickets     │    │   - Outreach    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Features

### 🔍 **Intelligent Analysis**
- **Churn Prediction**: ML-powered customer churn risk assessment
- **Anomaly Detection**: Statistical anomaly detection across multiple metrics
- **Root Cause Analysis**: AI-driven analysis of churn factors
- **Context-Aware Decisions**: Incorporates business KPIs and trends

### 🤖 **Automated Actions**
- **Slack Alerts**: Real-time notifications to customer success teams
- **Jira Tickets**: Automated ticket creation for investigation
- **Email Outreach**: Personalized customer communication
- **Action Logging**: Complete audit trail for model improvement

### 📊 **Business Intelligence**
- **KPI Integration**: Real-time business metrics from Looker
- **Trend Analysis**: Historical pattern recognition
- **Performance Monitoring**: System health and effectiveness tracking
- **Feedback Loop**: Continuous model improvement

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Google Cloud Platform account with BigQuery access
- Looker instance with API access
- OpenAI API key
- Slack workspace with bot token
- Jira instance with API access
- SendGrid account for email delivery

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd agentic-ai-churn-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# BigQuery Configuration
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Looker Configuration
LOOKER_BASE_URL=https://your-instance.looker.com
LOOKER_CLIENT_ID=your-client-id
LOOKER_CLIENT_SECRET=your-client-secret

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=your-channel-id

# Jira Configuration
JIRA_URL=https://your-instance.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=CUST

# SendGrid Configuration
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@yourcompany.com
```

## ⚙️ Configuration

### BigQuery Setup

1. **Create the required tables**:
```sql
-- Customers table
CREATE TABLE `your-project.your_dataset.your_customers_table` (
    customer_id STRING,
    subscription_id STRING,
    subscription_start_date DATE,
    subscription_end_date DATE,
    monthly_revenue FLOAT64,
    total_revenue FLOAT64,
    days_since_last_purchase INT64,
    days_since_last_login INT64,
    login_frequency_30d INT64,
    purchase_frequency_30d INT64,
    support_tickets_30d INT64,
    feature_usage_count INT64,
    churned_flag BOOL,
    churn_date DATE,
    email STRING,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Action logs table
CREATE TABLE `your-project.your_dataset.action_logs` (
    customer_id STRING,
    action_type STRING,
    action_details STRING,
    outcome STRING,
    created_at TIMESTAMP
);
```

2. **Update table references** in `bigquery_module.py`:
```python
# TODO: Replace with your actual table names
FROM `{self.project_id}.your_dataset.your_customers_table`
```

### Looker Setup

1. **Create KPI Looks** for:
   - Monthly churn rate
   - Customer lifetime value
   - Revenue churn
   - Active customers
   - Support tickets

2. **Update Look IDs** in `looker_module.py`:
```python
# TODO: Replace with your actual Look IDs
kpi_looks = {
    'monthly_churn_rate': 'your-monthly-churn-look-id',
    'customer_lifetime_value': 'your-clv-look-id',
    # ...
}
```

### Slack Setup

1. **Create a Slack app** and get bot token
2. **Invite bot to channel** where alerts should be sent
3. **Update channel ID** in environment variables

### Jira Setup

1. **Create API token** in Jira account settings
2. **Create custom field** for customer ID (optional)
3. **Update project key** in environment variables

## 🚀 Usage

### Quick Start

1. **Test system components**:
```bash
python main.py --mode test
```

2. **Run single analysis cycle**:
```bash
python main.py --mode single
```

3. **Run scheduled analysis** (every 60 minutes):
```bash
python main.py --mode scheduled --interval 60
```

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --mode {single,scheduled,test}  Run mode (default: single)
  --interval INT                   Interval in minutes for scheduled mode (default: 60)
  --help                          Show help message
```

### Individual Module Testing

Test each module independently:

```bash
# Test BigQuery module
python bigquery_module.py

# Test Looker module
python looker_module.py

# Test Agent reasoning
python agent_reasoning.py

# Test Actions module
python actions_module.py
```

## 📊 Monitoring and Logging

### Log Files
- **Main log**: `agentic_ai_churn.log`
- **Component logs**: Individual module logs

### Key Metrics
- Customers analyzed per cycle
- Churn predictions made
- Anomalies detected
- Actions executed (success/failure rates)
- Cycle duration
- Error rates

### Dashboard Integration
The system logs all actions and outcomes back to BigQuery, enabling:
- Performance dashboards
- ROI analysis
- Model improvement tracking
- Action effectiveness measurement

## 🔧 Customization

### Adding New Metrics
1. Update BigQuery table schema
2. Add metric to anomaly detection in `main.py`
3. Update customer context extraction

### Adding New Actions
1. Implement action in `actions_module.py`
2. Update action decision logic in `agent_reasoning.py`
3. Add action type to execution flow

### Customizing AI Reasoning
1. Modify prompts in `agent_reasoning.py`
2. Adjust decision thresholds
3. Add new analysis types

## 🧪 Testing

### Unit Tests
```bash
# Test individual components
python -m pytest tests/ -v
```

### Integration Tests
```bash
# Test full workflow
python main.py --mode test
```

### Load Testing
```bash
# Test with large datasets
python load_test.py --customers 10000
```

## 🔒 Security

### Best Practices
- Use service accounts for BigQuery access
- Store credentials in environment variables
- Implement proper IAM roles and permissions
- Use API keys with minimal required permissions
- Enable audit logging

### Data Privacy
- Anonymize customer data in logs
- Implement data retention policies
- Comply with GDPR/CCPA requirements
- Secure API communications

## 📈 Performance Optimization

### BigQuery Optimization
- Partition tables by date
- Use clustering for frequently queried columns
- Optimize ML model training schedules
- Implement query caching

### API Rate Limiting
- Implement exponential backoff
- Use connection pooling
- Cache frequently accessed data
- Monitor API quotas

## 🚨 Troubleshooting

### Common Issues

1. **BigQuery Connection Error**
   - Verify service account credentials
   - Check project ID and dataset names
   - Ensure proper IAM permissions

2. **Looker API Error**
   - Verify API credentials
   - Check Look IDs and dashboard IDs
   - Ensure API rate limits

3. **OpenAI API Error**
   - Verify API key
   - Check rate limits and quotas
   - Monitor token usage

4. **Action Execution Failures**
   - Verify API credentials for each service
   - Check network connectivity
   - Review error logs for specific issues

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py --mode single
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 .

# Run tests
pytest tests/ -v
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](link-to-wiki)
- **Issues**: [GitHub Issues](link-to-issues)
- **Discussions**: [GitHub Discussions](link-to-discussions)
- **Email**: support@yourcompany.com

## 🔮 Roadmap

### Phase 1 (Current)
- ✅ Basic churn prediction
- ✅ Anomaly detection
- ✅ Multi-channel actions
- ✅ AI reasoning

### Phase 2 (Next)
- 🔄 Advanced ML models (XGBoost, Neural Networks)
- 🔄 Real-time streaming data
- 🔄 A/B testing for actions
- 🔄 Customer segmentation

### Phase 3 (Future)
- 📋 Predictive maintenance
- 📋 Advanced analytics dashboard
- 📋 Integration with CRM systems
- 📋 Mobile app for alerts

---

**Built with ❤️ for customer success teams**
