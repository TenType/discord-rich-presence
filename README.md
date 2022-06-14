# discord-rich-presence
A lightweight and safe module for creating custom rich presences on Discord.

## Example
![Discord Rich Presence Example](/examples/example.jpg)

## How to Use

### Making a Discord App
1. Create an app by clicking "New Application" in the [Discord Developers Portal](https://discord.com/developers/applications).
2. Give your app a name and an icon (this can be changed later). Make sure to save your changes.
    - **Optional:** Go to "Rich Presence", and add a few images under the "Rich Presence Assets" section.
3. Under "Application Id" in the "General Information" tab, copy your app's id.

### Installation
4. Install the latest version of [Python](https://www.python.org/downloads/) if you haven't already.
5. Run the following in your terminal:
```
$ pip install discord-rich-presence
```
If all goes well, it should say something like "Successfully installed discord-rich-presence".

### Writing the Code
6. Create a file ending in `.py`, and paste in the following example from [examples/simple.py](examples/simple.py):
```py
from discordrp import Presence
import time

client_id = '000000000000000000' # Replace this with your own client id

with Presence(client_id) as presence:
    presence.set({
        'state': 'In Game',
        'details': "Summoner's Rift",
        'timestamps': {
            'start': int(time.time())
        },
    })

    while True:
        time.sleep(15)
```
Make sure you replace the `client_id` variable with your app's id that you copied earlier.

7. Run the program! You should now see that you have a rich presence on your profile that will be on until you stop the program! Feel free to change the code however you want by adding images, buttons, and more. Check out [examples/complex.py](examples/complex.py) for another example.

## Troubleshooting
If you're having trouble using this module, it might be because of the following:
- your Discord app is not open
- you passed in an incorrect dictionary, which the Discord API rejected
- something unexpected occurred while writing data, in which you should try running the program again
