from google import genai
import os

client = genai.Client(api_key="AIzaSyDZQXlxMt3PtYcbSQQwXen2ihyp1oUwqfw")

models = client.models.list()

for m in models:
    print(m.name)

