# pip install openai azure-identity

import time

import openai
from openai import AzureOpenAI
from azure.identity import DeviceCodeCredential

# Replace the endpoint and deployment of your AOAI resource if necessary
endpoint = 'https://epic-dms-aoai.openai.azure.com/'
deployment = 'gpt-4o' 
# Available deployments are:
# - gpt-35-turbo (version: 0215)
# - gpt-4 (version: 0613)
# - gpt-4o (version: 2024-08-06)
# - gpt-4o-mini (version: 2024-07-18)

# Need "Cognitive Services OpenAI User" role assigned to the user for that AOAI resource
# All interns should have already been added the role. 
# You may verify by going to iam.corp.adobe.com and checking if you are in GRP-EPIC-AOAI-USERS

# If you see the following exception raised, please reach out to @hawang or whoever give you the access
# openai.AuthenticationError: Error code: 401 - {'error': {'code': 'PermissionDenied', 'message': 'Principal does not have access to API/Operation.'}}

scope = "https://cognitiveservices.azure.com/.default"

tp = DeviceCodeCredential()
tr = None
client = None

# You will see the following printed out when calling token_provider() 
# "To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code XXXXXX to authenticate."
# Follow the instructions and login with your Adobe account.
tp.authenticate()

while True:
    now = int(time.time())

    if not client or not tr or now >= tr.expires_on:
        while True:
            try:
                tr = tp.get_token(scope)
            except Exception as e:
                print(f"Try re-authenticate due to error: {e}")
                tp.authenticate()
            else:
                break

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token = tr.token,
            # api_version="2024-02-01",
            api_version = "2025-04-01-preview",  # Use the latest API version
        )
    
    try:
        completion = client.chat.completions.create(
            model=deployment,
            messages=[
                {
                    "role": "user",
                    "content": "Hello World"
                },
            ],
        )
    except openai.AuthenticationError as e:
        print(f"Try refresh token due to error {e}")
        client = None
        continue

    print(completion.to_json())

    # print(now)
    # time.sleep(3600)