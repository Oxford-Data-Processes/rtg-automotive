import datetime
import uuid

from aws_utils import events

events_handler = events.EventsHandler()

events_handler.publish_event(
    "rtg-automotive-generate-ebay-table-lambda-event-bus",
    "com.oxforddataprocesses",
    "RtgAutomotiveGenerateEbayTable",
    {
        "event_type": "RtgAutomotiveGenerateEbayTable",
        "user": "admin",
        "trigger_id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    },
)
