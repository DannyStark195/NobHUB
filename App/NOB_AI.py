from google import genai
from google.genai import types
from flask import current_app #gives access to the current app running and all its resources
import re
def format_text(text): #function to format ai messages
    text = re.sub(r'\*(.*?)\*', r'<b>\1</b>', text)
    text = text.replace('*', '')
    formatted_text = text
    return formatted_text

def NOB(message):
    client = genai.Client(api_key=current_app.config["API_KEY"])
    response = client.models.generate_content(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(
        system_instruction= current_app.config['SYSTEM_INSTRUCTION_NOB']),
        # max_output_tokens=2000,
    contents= message)
    return format_text(response.text)

def Dennis(message):
    client = genai.Client(api_key=current_app.config["API_KEY"])
    response = client.models.generate_content(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(
        system_instruction= current_app.config['SYSTEM_INSTRUCTION_DENNIS']),
        # max_output_tokens=3000,
    contents= message)
    return format_text(response.text)
AIs = ['N.O.B', 'Dennis']
