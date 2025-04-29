import threading

from logger import CloudWatchLogger

def worker(logger: CloudWatchLogger, userId: int):
    """Simulates processing for a user and creates a log event.

    This function is designed to be executed in a separate thread. It
    generates a sample log event containing dummy entity information
    derived from the provided user ID, using the given logger instance.

    Args:
        logger: An instance of CloudWatchLogger used for creating the event.
        userId: The identifier for the user associated with this event.
    """
    event = logger.create_event(
        entities=[{"type": "PERSON", "value": f"User {userId}", "confidence": 0.91}],
        low_confidence_entities=[],
        article_url=f"https://example.com/{userId}",
        severity_text="INFO",
        severity_number=9
    )
    print(f"new INFO event created for user Id: {userId}")
    logger.send_event(event)

    event = logger.create_event(
        entities=[],
        low_confidence_entities=[{"type": "PERSON", "value": f"User {userId}", "confidence": 0.6}],
        article_url=f"https://example.com/{userId}",
        severity_text="ERROR",
        severity_number=17
    )

    print(f"new ERROR event created for user Id: {userId}")
    logger.send_event(event)

if __name__ == "__main__":
    logger = CloudWatchLogger(
        # TODO: Replace the dummy log_group, log_stream and region.
        log_group='<log_group_name>',
        log_stream='<log_stream_name>',
        region='<region>'
    )

    threads = []

    for id in range(10):
        t = threading.Thread(target=worker, args=(logger, id))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Now simulate an exception event
    print ("Simulating an divide by zero exception event")
    exception_event = logger.generate_exception_event()
    logger.send_event(exception_event)
    print ("Logged divide by zero exception event")

    print("All events sent. Check the CloudWatch logs dashboard for results.")
