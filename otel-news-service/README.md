# Logging with Open Telemetry

Open Telemetry is a well established standard for logging.
Deriq.AI prefers open telemetry logging where possible.
We recommend the adoption of Open Telemetry to generate application events and logs. Below an outline about Open Telemetry and a simple event logger example.

## OpenTelemetry

The OpenTelemetry event data model is essentially a specialized subset of the OpenTelemetry Log Record data model. It is enhanced with semantic conventions to represent significant occurrences at a specific point in time.

**Core Components of an Event (as a Log Record):**

Using [Logs Data Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/) as reference, below is a high level summary of the event structure.

* **Timestamp:** The exact time when the event occurred. This is crucial for temporal analysis and correlation with other telemetry data. It's typically recorded with high precision.
* **Severity:** Indicates the importance or urgency of the event (e.g., TRACE, DEBUG, INFO, WARN, ERROR, FATAL). Represented by both:
  * [`SeverityNumber`](https://opentelemetry.io/docs/specs/otel/logs/data-model/#field-severitynumber): A numerical value. 
  * [`SeverityText`](https://opentelemetry.io/docs/specs/otel/logs/data-model/#field-severitytext): A human-readable text. 
* **Name (Event Name):** A descriptive identifier for the event (e.g., `order.placed`, `exception`). Event names should be meaningful and follow OpenTelemetry naming guidelines, often using a dot-separated structure to indicate scope (e.g., `<scope>.<entity>.<action>`).
* **Body (Event Payload):** Contains the specific details or payload of the event. The body can be unstructured or structured data (e.g., a string, a JSON object). OpenTelemetry recommends using the body to represent the core information about the event. Semantic conventions for specific event types may define the expected structure and fields within the body.
* **Attributes:** Key-value pairs that provide additional context and metadata about the event. Attributes can include things like user IDs, transaction IDs, error codes, and other relevant information that helps in filtering, grouping, and analyzing events. Unlike body fields which are specific to an event name, attributes can be compared across different event types or other telemetry signals.
* **Resource:** Describes the source of the event, such as the service, host, or container where the event originated. Resource attributes provide context about the environment in which the event occurred (e.g., `service.name`, `host.name`, `cloud.region`).
* **Instrumentation Scope:** Identifies the library or instrumentation that generated the event, including its name and version. This helps in understanding the origin of the telemetry data.
* **Trace Context (TraceId, SpanId, TraceFlags):** If the event occurs within the context of a distributed trace, these fields link the event to a specific trace and span, allowing for correlation of events within a request flow.

## OpenTelemetry NEWS Sample Event generator and CloudWatch exporter script

### Overview

This Python script [logger.py](./logger.py) is used to illustrate the use of OpenTelemetry. The app is focused on a hypothetical news feed consumption service. It will help you to learn the uses of various forms of logging and tracing in open telemetry format.

1. **Generate a sample OpenTelemetry (OTel) event:** It creates a structured log event representing the output of a hypothetical NEWS Processing service handling news feed articles. This event includes details like extracted entities, confidence scores, trace context (trace ID, span ID), and resource information.
2. **Send the event to AWS CloudWatch Logs:** It uses the `boto3` library to interact with AWS CloudWatch Logs, ensuring the target log group and stream exist (creating them if necessary) and then sending the generated OTel event as a log message.

### **Summary: `CloudWatchLogger` Class**

The `CloudWatchLogger` class is designed to **send structured log events to AWS CloudWatch Logs**, enriched with **OpenTelemetry tracing**. It includes support for thread safety, trace metadata, retry logic, and structured formatting of logs.

---

#### **Constructor: `__init__`**

* **Purpose**: Initializes the logger with AWS log group/stream names and sets up OpenTelemetry tracing.
* **Key Actions**:
  * Stores log group and stream.
  * Initializes a thread lock.
  * Sets up OpenTelemetry tracer.
  * Calls `_ensure_log_group_and_stream()` to verify or create log group and stream.
  * (**Note**: The `boto3` client is commented out and needs to be enabled.)

---

#### **Private Methods**

##### **`_ensure_log_group_and_stream()`**

* **Purpose**: Ensures the specified log group and log stream exist in CloudWatch.
* **Behavior**:
  * Creates log group and stream if they don't exist.
  * Refreshes the sequence token required to send logs.

##### **`_refresh_sequence_token()`**

* **Purpose**: Updates the `sequence_token` by querying CloudWatch for the current token.
* **Used when**: Sending logs or recovering from an invalid token error.

##### **`_get_current_timestamp_ns()`**

* **Purpose**: Returns the current time in **nanoseconds**.
* **Used for**: Timestamps on log events.

##### **`_generate_trace_context()`**

* **Purpose**: Creates a trace context (trace ID and span ID) using OpenTelemetry.
* **Used in**: `create_event()` to include traceability in logs.

---

#### **Public Methods**

##### **`create_event(entities, low_confidence_entities, article_url, severity_text, severity_number)`**

* **Purpose**: Builds a structured log event with:
  * Timestamp
  * Severity level
  * Entities and low-confidence entities
  * Article metadata
  * Trace and span IDs
  * Versioning and instrumentation metadata

#### **`send_event(event)`**

* **Purpose**: Sends a **single** event to CloudWatch by wrapping it in a list and calling `send_events()`.

#### **`send_events(events)`**

* **Purpose**: Sends **multiple** log events to CloudWatch Logs.
* **Features**:
  * Converts each event to JSON format.
  * Adds timestamp.
  * Handles retry logic (up to 3 times) for `InvalidSequenceTokenException`.
  * Uses a thread lock to ensure only one thread sends logs at a time.

#### **`generate_exception_event()`**

* **Purpose**: Forces a divide by zero exception. Creates a OTEL critial error event. Returns the event to the caller.

---

### **Notable Features**

* OpenTelemetry integration for tracing
* Thread-safe log transmission
* Retry logic for handling AWS sequence token issues
* Uses `threading.Lock()` to ensure thread safety
* Requires configuring `boto3` client with the right credentials for AWS interaction in logger.py
* Replace the dummy log_group, log_stream and region when initializing a CloudWatchLogger object in main.py

---

## How to Run

1. **Prerequisites:**

    * Python 3 installed.
    * AWS credentials configured. Refer to [Default Credential Chain](https://docs.aws.amazon.com/sdk-for-go/v1/developer-guide/configuring-sdk.html#specifying-credentials) for various options. 
    
    The configured user/role needs permissions for `logs:CreateLogStream`, `logs:PutLogEvents`, `logs:DescribeLogGroups`, `logs:DescribeLogStreams`. Use the existing AWS managed permissions policy: `AmazonAPIGatewayPushToCloudWatchLogs`

2. **Install Dependencies (Ideally in a venv and activate it - so you don't pollute your global py environment):**

    ```bash
    [If using pip package manager] pip install -r requirements.txt

    OR

    [If using uv package manager] uv sync
    ```

3. **Address TODO in CloudWatchLogger.init():** Use your preferred way to initialize the boto3 client with your credentials.

4. **Address TODO CloudWatchLogger intialization in main.py:** Replace the dummy log_group, log_stream and region.

5. **Execute:**

    ```bash
    [If not using UV] python main.py
    [If using UV] uv run main.py
    ```

The script will create the log group and log stream if they don't exist. Then 10 threads are spawned. Each thread will simulate one INFO and one ERROR OTEL event with named entity recognition threshold values and send them to CloudWatch log stream. Finally in the main thread, an exception event is simulated and logged to Cloudwatch log stream.

Output - Navigate to your Cloudwatch console and view the insert log entries.

## References
* OpenTelemetry primer
  * [Observability Primer](https://opentelemetry.io/docs/concepts/observability-primer/)
  * [Logs](https://opentelemetry.io/docs/concepts/signals/logs/)
* OpenTelemetry for Python
  * [SDK](https://opentelemetry.io/docs/languages/python/)
  * [Getting Started](https://opentelemetry.io/docs/languages/python/getting-started/)


## [Future work] - OpenTelemetry Collector

There are better alternatives to writing directly to the Cloudwatch log streams directly from the code. At a later stage, we will evaluate the deployment of an OpenTelmetry collector. It is an open source project that offers a vendor-agnostic implementation of how to receive, process and export telemetry data. It removes the need to run, operate, and maintain multiple agents/collectors. This works with improved scalability.

