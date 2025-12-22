import argparse
import json
import logging
import time
import traceback
import redis

from app import create_app
from app.config import Config
from app.controllers.main import process_message
from app.resources import initLogger

initLogger()
logger = logging.getLogger(Config.APP_NAME)


def run_worker(queue_name: str):
    logger.info(f"Listening on Redis queue → {queue_name}")
    r = redis.from_url(Config.REDIS_URL, decode_responses=True)

    app = create_app()
    with app.app_context():
        while True:
            try:
                # Wait for a message (blocking up to 5 seconds)
                message = r.blpop(queue_name, timeout=5)
                if not message:
                    continue  # no message → loop again

                _, raw_data = message
                logger.debug(f"Received message: {raw_data}")

                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in message: {e}")
                    continue

                process_message(queue_name, data)
                logger.debug("Message processed successfully")

            except Exception as e:
                logger.error(f"Worker error: {e}")
                logger.debug(traceback.format_exc())

            time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Redis queue worker")
    parser.add_argument("--queue", required=True, help="Redis queue name to listen to")
    args = parser.parse_args()

    run_worker(args.queue)
