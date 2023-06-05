from discordrp import Presence
import time

client_id = "000000000000000000"  # Replace this with your own client id

with Presence(client_id) as presence:
    presence.set(
        {
            "state": "state",
            "details": "details",
            "timestamps": {
                "start": int(time.time()),
                "end": int(time.time()) + 1000,
            },
            "assets": {
                "large_image": "large_image",  # Replace this with the key of one of your assets
                "large_text": "large text hover",
                "small_image": "small_image",  # Replace this with the key of one of your assets
                "small_text": "small text hover",
            },
            "buttons": [
                {
                    "label": "label 1",
                    "url": "https://example.com",
                },
                {
                    "label": "label 2",
                    "url": "https://example.com",
                },
            ],
        }
    )

    while True:
        time.sleep(15)
