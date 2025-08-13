# 🔗 API Calls Summary - Agentic AI Churn Prediction System

## 📊 BigQuery API Calls

### **File: `bigquery_module.py`**

#### **🔧 Client Initialization**
```python
# Line 45-52: BigQuery Client Setup
self.client = bigquery.Client(project=self.project_id)
# OR with service account credentials
credentials = service_account.Credentials.from_service_account_file(credentials_path)
self.client = bigquery.Client(credentials=credentials, project=self.project_id)
```

#### **📥 Data Extraction**
```python
# Line 75-95: Extract Churn Data
query = f"""
SELECT customer_id, subscription_id, monthly_revenue, ...
FROM `{self.project_id}.your_dataset.your_customers_table`
WHERE created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL {days_back} DAY)
"""
df = self.client.query(query).to_dataframe()
```

#### **🤖 ML Model Creation**
```python
# Line 105-130: Create Churn Prediction Model
create_model_query = f"""
CREATE OR REPLACE MODEL `{self.project_id}.your_dataset.{model_name}`
OPTIONS(model_type='logistic_reg', auto_class_weights=true, input_label_cols=['churned_flag'])
AS SELECT ...
FROM `{self.project_id}.your_dataset.your_customers_table`
"""
job = self.client.query(create_model_query)
job.result()  # Wait for completion
```

#### **🔮 Churn Prediction**
```python
# Line 150-180: Run ML Predictions
prediction_query = f"""
SELECT customer_id, predicted_churned_flag, predicted_churned_flag_probs
FROM ML.PREDICT(
    MODEL `{self.project_id}.your_dataset.{model_name}`,
    (SELECT ... FROM `{self.project_id}.your_dataset.your_customers_table`)
)
"""
df = self.client.query(prediction_query).to_dataframe()
```

#### **🚨 Anomaly Detection**
```python
# Line 200-230: Detect Anomalies
anomaly_query = f"""
WITH metric_stats AS (SELECT AVG({metric}) as avg_metric, STDDEV({metric}) as std_metric
FROM `{self.project_id}.your_dataset.your_customers_table`)
SELECT c.customer_id, c.{metric}, (c.{metric} - ms.avg_metric) / ms.std_metric as z_score
FROM `{self.project_id}.your_dataset.your_customers_table` c
CROSS JOIN metric_stats ms
"""
df = self.client.query(anomaly_query).to_dataframe()
```

#### **📝 Action Logging**
```python
# Line 250-280: Log Action Outcomes
insert_query = f"""
INSERT INTO `{self.project_id}.your_dataset.action_logs`
(customer_id, action_type, action_details, outcome, created_at)
VALUES (@customer_id, @action_type, @action_details, @outcome, @created_at)
"""
query_config = QueryJobConfig(query_parameters=[...])
job = self.client.query(insert_query, job_config=query_config)
```

#### **👤 Customer Context**
```python
# Line 300-330: Get Customer Details
context_query = f"""
SELECT customer_id, subscription_id, monthly_revenue, ...
FROM `{self.project_id}.your_dataset.your_customers_table`
WHERE customer_id = @customer_id
"""
query_config = QueryJobConfig(query_parameters=[...])
df = self.client.query(context_query, job_config=query_config).to_dataframe()
```

---

## 📈 Looker API Calls

### **File: `looker_module.py`**

#### **🔧 SDK Initialization**
```python
# Line 35-45: Looker SDK Setup
os.environ['LOOKERSDK_BASE_URL'] = os.getenv('LOOKER_BASE_URL', 'https://your-instance.looker.com')
os.environ['LOOKERSDK_CLIENT_ID'] = os.getenv('LOOKER_CLIENT_ID', 'your-client-id')
os.environ['LOOKERSDK_CLIENT_SECRET'] = os.getenv('LOOKER_CLIENT_SECRET', 'your-client-secret')
self.sdk = api_methods.LookerSDK()
```

#### **📊 Dashboard Data**
```python
# Line 65-85: Fetch Dashboard
dashboard = self.sdk.dashboard(dashboard_id)
dashboard_elements = self.sdk.dashboard_dashboard_elements(dashboard_id)
```

#### **👁️ Look Data**
```python
# Line 105-125: Get Look Data
look = self.sdk.look(look_id)
look_data = self.sdk.look_results(look_id)
```

#### **🔍 Custom Queries**
```python
# Line 145-170: Execute Custom Query
query_request = models.WriteQuery(
    model=query.get('model'),
    view=query.get('view'),
    fields=query.get('fields', []),
    filters=query.get('filters', {}),
    sorts=query.get('sorts', []),
    limit=query.get('limit', 1000)
)
query_result = self.sdk.create_query(query_request)
query_data = self.sdk.run_query(query_result.id, 'json')
```

#### **📊 KPI Metrics**
```python
# Line 190-220: Fetch Churn KPIs
kpi_looks = {
    'monthly_churn_rate': 'your-monthly-churn-look-id',
    'customer_lifetime_value': 'your-clv-look-id',
    'revenue_churn': 'your-revenue-churn-look-id',
    'active_customers': 'your-active-customers-look-id',
    'support_tickets': 'your-support-tickets-look-id'
}
for kpi_name, look_id in kpi_looks.items():
    look_data = self.get_look_data(look_id)
```

#### **👤 Customer Insights**
```python
# Line 240-270: Get Customer Insights
customer_query = {
    'model': 'your_model',
    'view': 'your_customers_view',
    'fields': ['customers.customer_id', 'customers.monthly_revenue', ...],
    'filters': {'customers.customer_id': customer_id},
    'limit': 1
}
query_result = self.execute_query(customer_query)
```

#### **📈 Trend Data**
```python
# Line 290-320: Get Trend Analysis
trend_query = {
    'model': 'your_model',
    'view': 'your_metrics_view',
    'fields': ['metrics.date', f'metrics.{metric}'],
    'filters': {'metrics.date': f'>= {days} days ago'},
    'sorts': ['metrics.date'],
    'limit': days
}
query_result = self.execute_query(trend_query)
```

---

## 🧠 LangChain & OpenAI API Calls

### **File: `agent_reasoning.py`**

#### **🔧 OpenAI Client Setup**
```python
# Line 55-65: ChatOpenAI Initialization
self.llm = ChatOpenAI(
    model=model_name,  # "gpt-4"
    temperature=temperature,  # 0.1
    openai_api_key=api_key
)
```

#### **📝 Prompt Templates**
```python
# Line 180-200: Root Cause Analysis Prompt
root_cause_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert customer success analyst..."""),
    ("human", """Customer Analysis Context:
    Customer Metrics: {customer_metrics}
    Churn Prediction: {prediction_metrics}
    KPI Context: {kpi_metrics}
    Please analyze the root cause...""")
])
```

#### **🤖 LLM Inference**
```python
# Line 210-220: OpenAI API Call for Root Cause
formatted_prompt = root_cause_prompt.format_messages(
    customer_metrics=json.dumps(analysis_context['customer_metrics'], indent=2),
    prediction_metrics=json.dumps(analysis_context['prediction_metrics'], indent=2),
    kpi_metrics=json.dumps(analysis_context['kpi_metrics'], indent=2)
)
response = self.llm.invoke(formatted_prompt)
```

#### **🔍 Action Determination**
```python
# Line 280-300: Action Decision Prompt
action_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an automated customer success agent..."""),
    ("human", """Analysis Results:
    Root Cause Analysis: {root_cause}
    Customer Context: {customer_metrics}
    Churn Prediction: {prediction_metrics}
    Determine the most appropriate action...""")
])
```

#### **🎯 Structured Output Parsing**
```python
# Line 70-75: Pydantic Output Parsers
self.action_parser = PydanticOutputParser(pydantic_object=ActionDecision)
self.cause_parser = PydanticOutputParser(pydantic_object=RootCauseAnalysis)

# Line 225-235: Parse LLM Response
try:
    root_cause = self.cause_parser.parse(response.content)
    return root_cause.dict()
except Exception as parse_error:
    return self._parse_root_cause_fallback(response.content)
```

---

## 📱 External API Calls

### **File: `actions_module.py`**

#### **💬 Slack API**
```python
# Line 35-40: Slack Client Setup
self.slack_client = WebClient(token=slack_token)

# Line 130-150: Send Slack Alert
response = self.slack_client.chat_postMessage(
    channel=channel_id,
    text=message['text'],
    blocks=message['blocks']
)
```

#### **🎫 Jira API**
```python
# Line 50-60: Jira Client Setup
self.jira_client = JIRA(
    server=jira_url,
    basic_auth=(jira_username, jira_api_token)
)

# Line 250-280: Create Jira Ticket
new_issue = self.jira_client.create_issue(fields=issue_dict)
```

#### **📧 SendGrid API**
```python
# Line 65-70: SendGrid Client Setup
self.sendgrid_client = SendGridAPIClient(api_key=sendgrid_api_key)

# Line 380-400: Send Email
message = Mail(
    from_email=from_email,
    to_emails=to_email,
    subject=subject,
    html_content=html_content
)
response = self.sendgrid_client.send(message)
```

---

## 🔄 API Call Flow Summary

### **1. Data Pipeline**
```
BigQuery → Extract Customer Data → ML Prediction → Anomaly Detection
```

### **2. Intelligence Layer**
```
Looker → KPI Context → LangChain → OpenAI GPT-4 → Structured Analysis
```

### **3. Action Execution**
```
Analysis Results → Slack/Jira/SendGrid → Action Logging → BigQuery
```

### **4. Complete Workflow**
```
BigQuery (Data) → Looker (Context) → OpenAI (Reasoning) → External APIs (Actions) → BigQuery (Logging)
```

---

## 🛠️ Configuration Requirements

### **Environment Variables Needed:**
```bash
# BigQuery
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Looker
LOOKER_BASE_URL=https://your-instance.looker.com
LOOKER_CLIENT_ID=your-client-id
LOOKER_CLIENT_SECRET=your-client-secret

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Slack
SLACK_BOT_TOKEN=your-slack-bot-token
SLACK_CHANNEL_ID=your-channel-id

# Jira
JIRA_URL=https://your-instance.atlassian.net
JIRA_USERNAME=your-username
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=your-project-key

# SendGrid
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@yourcompany.com
```

---

## 📊 API Call Statistics

- **BigQuery API Calls:** 6 different operations
- **Looker API Calls:** 7 different operations  
- **OpenAI API Calls:** 2 main reasoning operations
- **External API Calls:** 3 platforms (Slack, Jira, SendGrid)
- **Total API Integrations:** 4 major platforms
- **Structured Data Flow:** End-to-end automation

---

*This system demonstrates comprehensive API integration across data storage, business intelligence, AI reasoning, and action execution platforms.*
