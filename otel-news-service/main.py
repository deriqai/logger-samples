import threading

from logger import CloudWatchLogger

def worker(logger: CloudWatchLogger, i: int):
    event = logger.create_event(
        entities=[{"type": "PERSON", "value": f"User {i}", "confidence": 0.91}],
        low_confidence_entities=[],
        article_url=f"https://example.com/{i}"
    )
    #logger.send_event(event)

if __name__ == "__main__":
    logger = CloudWatchLogger(
        log_group='/aws/news_feed_parser',
        log_stream='entity_extraction_stream',
        region='us-east-1'
    )

    threads = []

    for i in range(10):
        t = threading.Thread(target=worker, args=(logger, i))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("All events sent.")
