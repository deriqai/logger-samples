import logging
import time
import json
from opentelemetry import trace
from opentelemetry.sdk import trace as sdktrace
from opentelemetry.sdk.resource import Resource
from typing import Optional, Dict, List
# You would typically install these with:
# pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto
# pip install boto3

# AWS CloudWatch Logs integration (requires boto3)
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Configuration
LOG_GROUP_NAME = "my-opentelemetry-logs"  # Replace with your CloudWatch Logs group name
LOG_STREAM_NAME = "my-worker-stream"  # Replace with your CloudWatch Logs stream name
AWS_REGION = "us-west-2"  # Replace with your AWS region

# Function to generate a random hexadecimal ID (for trace_id, span_id)
import uuid

def generate_hex_id():
    return uuid.uuid4().hex

def create_log_stream(log_group_name: str, log_stream_name: str, region_name: str = AWS_REGION) -> None:
    """
    Creates a CloudWatch Logs stream if it doesn't exist.
    """
    client = boto3.client("logs", region_name=region_name)
    try:
        client.create_log_stream(
            logGroupName=log_group_name, logStreamName=log_stream_name
        )
        print(f"Log stream '{log_stream_name}' created in log group '{log_group_name}'")
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"Log stream '{log_stream_name}' already exists in log group '{log_stream_name}'")
    except Exception as e:
        print(f"Error creating log stream: {e}")
        raise  # Re-raise to handle it in the main function

def put_log_events(
    log_group_name: str,
    log_stream_name: str,
    log_events: List[Dict],
    region_name: str = AWS_REGION,
) -> Optional[dict]:
    """
    Sends log events to CloudWatch Logs.

    Args:
        log_group_name: The name of the log group.
        log_stream_name: The name of the log stream.
        log_events: A list of log events.  Each event is a dictionary.
        region_name: The AWS region.

    Returns:
        The response from CloudWatch Logs, or None on error.
    """
    client = boto3.client("logs", region_name=region_name)
    try:
        response = client.put_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            logEvents=log_events,
        )
        return response
    except BotoCoreError as e:
        print(f"Error sending logs (BotoCore): {e}")
        return None
    except ClientError as e:
        print(f"Error sending logs (Client): {e}")
        print(f"Error details: {e.response}")  # Print the full error response
        return None
    except Exception as e:
        print(f"Error sending logs: {e}")
        return None

def otel_event_to_cloudwatch(event: dict, log_group_name: str, log_stream_name: str, region_name: str = AWS_REGION) -> None:
    """
    Sends an OpenTelemetry event to CloudWatch Logs.

    Args:
        event: The OpenTelemetry event dictionary.
        log_group_name: The name of the CloudWatch Logs group.
        log_stream_name: The name of the CloudWatch Logs stream.
        region_name: The AWS region.
    """
    # Prepare the log event for CloudWatch Logs
    log_event = {
        "timestamp": event["timestamp"],  # Use the original timestamp
        "message": json.dumps(event),  # Convert the entire event to a JSON string
    }

    try:
        # Ensure the log stream exists.  Create it if it doesn't.
        create_log_stream(log_group_name, log_stream_name, region_name)

        # Send the log event to CloudWatch Logs
        response = put_log_events(log_group_name, log_stream_name, [log_event], region_name)

        if response:
            print(f"Successfully sent log event to CloudWatch Logs: {response}")
        else:
            print("Failed to send log event to CloudWatch Logs.")

    except Exception as e:
        print(f"An error occurred: {e}")
        # It's often good practice to re-raise exceptions after logging them,
        # especially if this function is part of a larger system where the caller
        # needs to know about the failure.  However, if this function is the
        # top-level handler, you might choose to just log and continue.
        # raise  # Uncomment this line to re-raise the exception
        pass #Or pass

def generate_otel_event():
    """Generates the OpenTelemetry event dictionary."""

    # Initialize tracer
    tracer = trace.get_tracer("my_tracer", "1.0.0")  # Replace with your tracer name and version

    # Start a span.  This will create a new trace if one doesn't exist,
    # and add the span to the current trace context.
    with tracer.start_as_current_span("generate_otel_event_span") as span:
        context = trace.get_current_span().get_span_context()

        event = {
            "timestamp": int(time.time_ns()),  # Use current time in nanoseconds
            "severity": "INFO",
            "severity_number": 9,
            "name": "news_feed.entity_extracted",
            "body": {
                "entities": [
                    {
                        "type": "PERSON",
                        "value": "Sundar Pichai",
                        "confidence": 0.92
                    },
                    {
                        "type": "ORGANIZATION",
                        "value": "Google",
                        "confidence": 0.88
                    },
                    {
                        "type": "LOCATION",
                        "value": "California",
                        "confidence": 0.95
                    }
                    # ... more high-confidence entities
                ],
                "low_confidence_entities": [
                    {
                        "type": "PRODUCT",
                        "value": "Cloud Service",
                        "confidence": 0.65,
                        "threshold": 0.70
                    },
                    {
                        "type": "MISC",
                        "value": "New Update",
                        "confidence": 0.68,
                        "threshold": 0.70
                    }
                    # ... entities below the threshold
                ],
                "article_url": "https://example.com/news/article456",
                "confidence_threshold": 0.70
            },
            "attributes": {     # customize attributes as per your needs
                "news_feed.parser.version": "v1.2.0",
                "my_model.name": "advanced_news",  # replace with your own model / service names
                "my_model.version": "5.0.0",
                "my_model.confidence_threshold": 0.70,
                # Include trace and span IDs from the current span context.
                "trace_id": format_trace_id(context.trace_id),
                "span_id": format_span_id(context.span_id),
            },
            "resource": {
                "attributes": {
                    "service.name": "news_feed_parser",
                    "service.version": "0.5.0",
                    "host.name": "my-worker"
                    # ... other resource attributes
                }
            },
            "instrumentation_scope": {
                "name": "com.example.news_parser",
                "version": "1.0.0"
            }
        }
        return event

def format_trace_id(trace_id: int) -> str:
    """Formats a trace ID as a 16-character hexadecimal string."""
    return f"{trace_id:032x}"

def format_span_id(span_id: int) -> str:
    """Formats a span ID as an 8-character hexadecimal string."""
    return f"{span_id:016x}"

def main():
    """Main function to generate the event and send it to CloudWatch."""
    # Initialize the OpenTelemetry SDK (you might have this elsewhere in your app)
    resource = Resource(attributes={
        "service.name": "news_feed_parser",
        "service.version": "0.5.0",
        "host.name": "my-worker"
    })
    tracer_provider = sdktrace.TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    event = generate_otel_event()
    otel_event_to_cloudwatch(event, LOG_GROUP_NAME, LOG_STREAM_NAME, AWS_REGION)

    # Shutdown the tracer provider when your application exits.
    tracer_provider.shutdown()

if __name__ == "__main__":
    main()

