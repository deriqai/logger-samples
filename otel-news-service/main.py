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
        article_url=f"https://example.com/{userId}"
    )
    print(f"new event created for user Id: {userId}", event);
    #logger.send_event(event)

if __name__ == "__main__":
    logger = CloudWatchLogger(
        log_group='/aws/news_feed_parser',
        log_stream='entity_extraction_stream',
        region='us-east-1'
    )

    threads = []

    for id in range(10):
        t = threading.Thread(target=worker, args=(logger, id))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("All events sent.")
