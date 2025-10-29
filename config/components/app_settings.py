import os

API_TOKEN = os.environ.get('API_TOKEN', 'test-token')
LINK_SECRET = os.environ.get('LINK_SECRET', 'a-super-secret-key')
SITE_URL = os.environ.get('SITE_URL', "https://pressure.loca.lt")
STARTUP_PATH = "/background/start"
STARTUP_INTERVAL = 60 * 30
ALICE_BOT_USERNAME = os.environ.get('ALICE_BOT_USERNAME', "AliceBPBot") # Placeholder for the bot's username
