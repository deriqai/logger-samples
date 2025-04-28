import json
import time
import boto3
from typing import List, Dict, Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import format_trace_id, format_span_id


class CloudWatchLogger:
    def __init__(self, log_group: str, log_stream: str, region: str = 'us-east-1'):
        self.log_group = log_group
        self.log_stream = log_stream

        #TODO 
        # self.client = boto3.client('logs', region_name=region)
        # self.sequence_token: Optional[str] = None
        # self.lock = threading.Lock()  # Lock to protect writes

        # self._ensure_log_group_and_stream()

        # Setup OpenTelemetry tracer
        resource = Resource.create({"service.name": "news_feed_parser"})
        trace.set_tracer_provider(TracerProvider(resource=resource))
        self.tracer = trace.get_tracer(__name__)

    def _ensure_log_group_and_stream(self):
        try:
            self.client.create_log_group(logGroupName=self.log_group)
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass

        try:
            self.client.create_log_stream(logGroupName=self.log_group, logStreamName=self.log_stream)
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass

        self._refresh_sequence_token()

    def _refresh_sequence_token(self):
        """Force refresh the current sequence token."""
        response = self.client.describe_log_streams(
            logGroupName=self.log_group,
            logStreamNamePrefix=self.log_stream
        )
        streams = response.get('logStreams', [])
        if streams:
            self.sequence_token = streams[0].get('uploadSequenceToken')
        else:
            self.sequence_token = None

    def _get_current_timestamp_ns(self) -> int:
        return int(time.time() * 1e9)

    def _generate_trace_context(self) -> Dict[str, str]:
        with self.tracer.start_as_current_span("news_feed.entity_extracted") as span:
            return {
                "trace_id": format_trace_id(span.get_span_context().trace_id),
                "span_id": format_span_id(span.get_span_context().span_id)
            }

    def create_event(self, entities: List[Dict], low_confidence_entities: List[Dict], article_url: str) -> Dict:
        trace_context = self._generate_trace_context()

        event = {
            "timestamp": self._get_current_timestamp_ns(),
            "severity": "INFO",
            "severity_number": 9,
            "name": "news_feed.entity_extracted",
            "body": {
                "entities": entities,
                "low_confidence_entities": low_confidence_entities,
                "article_url": article_url,
                "confidence_threshold": 0.70
            },
            "attributes": {
                "news_feed.parser.version": "v1.2.0",
                "ner_model.name": "advanced_ner",
                "ner_model.version": "5.0.0",
                "ner_model.confidence_threshold": 0.70,
                "trace_id": trace_context["trace_id"],
                "span_id": trace_context["span_id"]
            },
            "resource": {
                "attributes": {
                    "service.name": "news_feed_parser",
                    "service.version": "0.5.0",
                    "host.name": "my-ner-worker"
                }
            },
            "instrumentation_scope": {
                "name": "com.example.news_parser.ner",
                "version": "1.0.0"
            }
        }
        return event

    def send_event(self, event: Dict):
        self.send_events([event])

    def send_events(self, events: List[Dict]):
        log_events = [
            {
                'timestamp': int(time.time() * 1000),
                'message': json.dumps(event)
            } for event in events
        ]

        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            with self.lock:  # Only one thread can send at a time
                try:
                    kwargs = {
                        'logGroupName': self.log_group,
                        'logStreamName': self.log_stream,
                        'logEvents': log_events
                    }

                    if self.sequence_token:
                        kwargs['sequenceToken'] = self.sequence_token

                    response = self.client.put_log_events(**kwargs)
                    self.sequence_token = response.get('nextSequenceToken')
                    print(f"Successfully sent {len(events)} event(s).")
                    break  # Success, exit loop

                except self.client.exceptions.InvalidSequenceTokenException as e:
                    print("Invalid sequence token detected. Refreshing...")
                    self._refresh_sequence_token()
                    attempts += 1

                except Exception as e:
                    print(f"Error sending logs to CloudWatch: {e}")
                    break  # Some other error; don't retry infinitely

        else:
            print(f"Failed to send after {max_attempts} attempts.")

