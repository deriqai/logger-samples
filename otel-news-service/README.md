# Logging with Open Telemetry

Open Telemetry is a well established standard for logging.
Deriq.AI prefers open telemetry logging where possible.
For new customers, we recommend them to adopt Open Telemetry for logging.

Here is an outline about Open Telemetry and a simple logger example.

## OpenTelemetry NEWS Sample Event to CloudWatch Script

### Overview

This Python script [news-sample-event.py](./news-sample-event.py) is used to illustrate the use of OpenTelemetry. The app is focused on a hypothetical news feed consumption service. It will help you to learn the uses of various forms of logging and tracing in open telemetry format.

1. **Generate a sample OpenTelemetry (OTel) event:** It creates a structured log event representing the output of a hypothetical NEWS Processing service handling news feed articles. This event includes details like extracted entities, confidence scores, trace context (trace ID, span ID), and resource information.
2. **Send the event to AWS CloudWatch Logs:** It uses the `boto3` library to interact with AWS CloudWatch Logs, ensuring the target log group and stream exist (creating them if necessary) and then sending the generated OTel event as a log message.

PS: See <https://opentelemetry.io/docs/languages/python/getting-started/> for a generic get started with Open Telemetry example.

## Functionality


## **Summary: `CloudWatchLogger` Class**

The `CloudWatchLogger` class is designed to **send structured log events to AWS CloudWatch Logs**, enriched with **OpenTelemetry tracing**. It includes support for thread safety, trace metadata, retry logic, and structured formatting of logs.

---

### **Constructor: `__init__`**
- **Purpose**: Initializes the logger with AWS log group/stream names and sets up OpenTelemetry tracing.
- **Key Actions**:
  - Stores log group and stream.
  - Initializes a thread lock.
  - Sets up OpenTelemetry tracer.
  - Calls `_ensure_log_group_and_stream()` to verify or create log group and stream.
  - (**Note**: The `boto3` client is commented out and needs to be enabled.)

---

### **Private Methods**

#### **`_ensure_log_group_and_stream()`**
- **Purpose**: Ensures the specified log group and log stream exist in CloudWatch.
- **Behavior**:
  - Creates log group and stream if they don't exist.
  - Refreshes the sequence token required to send logs.

#### **`_refresh_sequence_token()`**
- **Purpose**: Updates the `sequence_token` by querying CloudWatch for the current token.
- **Used when**: Sending logs or recovering from an invalid token error.

#### **`_get_current_timestamp_ns()`**
- **Purpose**: Returns the current time in **nanoseconds**.
- **Used for**: Timestamps on log events.

#### **`_generate_trace_context()`**
- **Purpose**: Creates a trace context (trace ID and span ID) using OpenTelemetry.
- **Used in**: `create_event()` to include traceability in logs.

---

### **Public Methods**

#### **`create_event(entities, low_confidence_entities, article_url)`**
- **Purpose**: Builds a structured log event with:
  - Timestamp
  - Severity level
  - Entities and low-confidence entities
  - Article metadata
  - Trace and span IDs
  - Versioning and instrumentation metadata

#### **`send_event(event)`**
- **Purpose**: Sends a **single** event to CloudWatch by wrapping it in a list and calling `send_events()`.

#### **`send_events(events)`**
- **Purpose**: Sends **multiple** log events to CloudWatch Logs.
- **Features**:
  - Converts each event to JSON format.
  - Adds timestamp.
  - Handles retry logic (up to 3 times) for `InvalidSequenceTokenException`.
  - Uses a thread lock to ensure only one thread sends logs at a time.

---

### **Notable Features**
- OpenTelemetry integration for tracing
- Thread-safe log transmission
- Retry logic for handling AWS sequence token issues
- Uses `threading.Lock()` to ensure thread safety
- Requires uncommenting and configuring `boto3` client for real AWS interaction

---

## How to Run

1. **Prerequisites:**

    * Python 3 installed.
    * AWS credentials configured (e.g., via environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, or an IAM role if running on EC2/ECS/Lambda). The configured user/role needs permissions for `logs:CreateLogStream` and `logs:PutLogEvents`.
2. **Install Dependencies (Ideally in a venv and activate it - so you don't pollute your global py environment):**

    ```bash
    pip install -r requirements.txt
    ```

3. **Address TODO on line 16 of CloudWatchLogger.init():** Use your preferred way to initialize the boto3 client with your credentials.
4. **Execute:**

    ```bash
    python main.py
    ```

The script will create the log group and log stream if they don't exist. Then 10 threads are spawned. Each thread will insert one otel event in the log stream. It and the success or failure of sending the log event to CloudWatch.

Output - Navigate to your Cloudwatch console and view the insert log entries.
