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

* **Configuration:** Sets AWS region, CloudWatch log group name, and log stream name via constants.
* **AWS CloudWatch Interaction:**
  * `create_log_stream`: Checks if a specified CloudWatch log stream exists within a log group and creates it if it doesn't. Handles potential `ResourceAlreadyExistsException`.
  * `put_log_events`: Sends a list of log events (dictionaries with `timestamp` and `message` keys) to a specified CloudWatch log stream. Includes basic error handling for `boto3` exceptions.
* **OpenTelemetry Event Generation:**
  * `generate_otel_event`:
    * Initializes a basic OpenTelemetry tracer.
      * Starts an OTel span to get a valid `trace_id` and `span_id` from the current context.
      * Constructs a Python dictionary mimicking the structure of an OpenTelemetry Log Data Model event. This includes:
        * `timestamp`: Nanosecond precision timestamp.
        * `severity`: Log level (e.g., "INFO").
        * `name`: A descriptive name for the event type.
        * `body`: The main payload, containing structured data about the NEWS results (entities, confidence, source URL).
        * `attributes`: Key-value pairs providing additional context (e.g., model versions, thresholds, trace/span IDs).
        * `resource`: Attributes describing the service generating the event (e.g., service name, host).
        * `instrumentation_scope`: Information about the library generating the event.
        * `format_trace_id`, `format_span_id`: Helper functions to format integer trace/span IDs into their standard hexadecimal representations.
* **Integration Function:**
  * `otel_event_to_cloudwatch`: Takes the generated OTel event dictionary, formats it into the structure required by `put_log_events` (timestamp and JSON string message), ensures the log stream exists, and calls `put_log_events` to send it.
* **Main Execution (`main` function):**
  * Performs minimal OpenTelemetry SDK initialization (sets up a `TracerProvider` with resource attributes but doesn't configure a real exporter like OTLP or Jaeger). This setup is primarily needed to generate valid trace/span contexts within `generate_otel_event`.
  * Calls `generate_otel_event` to create the sample event.
  * Calls `otel_event_to_cloudwatch` to send the event to AWS.
  * Calls `tracer_provider.shutdown()` for graceful OTel SDK cleanup.

## How to Run

1. **Prerequisites:**

    * Python 3 installed.
    * AWS credentials configured (e.g., via environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, or an IAM role if running on EC2/ECS/Lambda). The configured user/role needs permissions for `logs:CreateLogStream` and `logs:PutLogEvents`.
    * A CloudWatch Log Group (specified by `LOG_GROUP_NAME`) must exist in the target AWS region (`AWS_REGION`). The script *does not* create the log group, only the log stream within it.
2. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure:** Modify the constants `LOG_GROUP_NAME`, `LOG_STREAM_NAME`, and `AWS_REGION` at the top of the script to match your environment.
4. **Execute:**

    ```bash
    python news-sample-event.py
    ```

The script will print messages indicating whether the log stream was created (or already existed) and the success or failure of sending the log event to CloudWatch.
