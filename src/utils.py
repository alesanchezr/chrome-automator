import yaml
import os
import requests
import sys
import time
from string import Template

def get_message(message_type, contact, agent_name, list_config):
    """Get a message from the list configuration"""
    if message_type not in list_config['messages']:
        raise ValueError(f"Message type '{message_type}' not found in list configuration")
    
    # Get the message in the contact's language (default to English if not specified)
    lang = contact.get('language', 'en')
    if lang not in list_config['messages'][message_type]:
        lang = 'en'  # Fallback to English if the language is not available
    
    message = list_config['messages'][message_type][lang]
    return message.format(name=contact.get('name', ''), agent_name=agent_name)

def load_list_config(list_name):
    """Load the configuration for a specific list from its YML file"""
    yml_path = os.path.join('src', 'followup-list', f'{list_name}.yml')
    if not os.path.exists(yml_path):
        raise FileNotFoundError(f"List configuration file not found: {yml_path}")
    
    with open(yml_path, 'r') as f:
        return yaml.safe_load(f)

def process_template_string(template_str, contact, agent_name, list_config):
    """Process a template string, replacing variables and function calls"""
    # Replace get_message calls
    if '{{get_message(' in template_str:
        # Extract the message type and format the get_message call
        parts = template_str.split('{{get_message(')[1].split(')}}')[0]
        message_type = parts.split(',')[0].strip("'")
        return get_message(message_type, contact, agent_name, list_config)
    
    # Handle contact variables with {{contact.field}} syntax
    if '{{contact.' in template_str:
        # Find all contact variable references
        parts = template_str.split('{{')
        result = parts[0]
        for part in parts[1:]:
            if 'contact.' in part:
                field = part.split('}}')[0].split('.')[1]
                value = contact.get(field, '')
                result += str(value) + part.split('}}')[1]
            else:
                result += '{{' + part
        return result
    
    return template_str

def countdown(seconds):
    """Show a countdown timer"""
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\rWaiting {i} seconds before next contact... ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 50 + "\r")  # Clear the line
    sys.stdout.flush()

def get_pending_contacts(list_name):
    """Fetch pending contacts from the API"""
    url = f"https://brevo-webhook.replit.app/api/followups/{list_name}?status=PENDING"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching contacts for {url}:", response.status_code)
        return None

def update_contact(contact_id, status, message):
    """Update a contact's status and message"""
    url = f"https://brevo-webhook.replit.app/api/followups/{contact_id}"
    data = {
        "status": status,
        "statusText": message
    }
    response = requests.put(url, json=data)
    if response.status_code == 200:
        print(f"Successfully updated contact {contact_id}")
        return True
    else:
        print(f"Error updating contact {contact_id}:", response.status_code)
        return False 