import os

# Get environment variables
GITHUB_TOKEN = os.environ.get('GH_TOKEN')
PFT_PASSWORD = os.environ.get('PFT_PASSWORD')

print(GITHUB_TOKEN,PFT_PASSWORD)