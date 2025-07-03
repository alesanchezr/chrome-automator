import yaml
import os
import requests
import sys
import time
from string import Template
import threading
if os.name == 'nt':
    import msvcrt
else:
    import select

def get_message(message_type, contact, agent_name, list_config):
    """Get a message from the list configuration"""
    if message_type not in list_config['messages']:
        raise ValueError(f"Message type '{message_type}' not found in list configuration")
    
    # Get the message in the contact's language (default to English if not specified)
    lang = contact.get('utmLanguage', 'en')
    if lang not in list_config['messages'][message_type]:
        lang = 'en'  # Fallback to English if the language is not available
    
    message = list_config['messages'][message_type][lang]
    
    # Get contact name, ensure it's not empty
    contact_name = contact.get('name', '').strip()
    if not contact_name:
        contact_name = "amigo"  # Default fallback name in Spanish
        if lang == 'en':
            contact_name = "friend"  # Default fallback name in English
    
    # Replace placeholders
    try:
        # First replace {{contact.name}} with contact_name
        message = message.replace('{{contact.name}}', contact_name)
        
        # Then replace {agent_name} with the actual agent name
        message = message.replace('{agent_name}', agent_name)
        
        # Finally, replace any course placeholders if present
        if '{course}' in message:
            message = message.format(course=contact.get('course', 'generic'))
            
        return message
    except Exception as e:
        print(f"Error formatting message: {e}")
        return message  # Return unformatted message as fallback

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
        
        # Handle subscription offer message type
        if message_type == 'subscription_offer_generic' and contact.get('course'):
            message_type = f"subscription_offer_{contact.get('course')}"
            
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
    """Show a countdown timer that can be skipped by pressing Enter"""
    def check_input():
        if os.name == 'nt':  # Windows
            return msvcrt.kbhit() and msvcrt.getch() == b'\r'
        else:  # Unix-like
            return select.select([sys.stdin], [], [], 0)[0] and sys.stdin.read(1) == '\n'

    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\rWaiting {i} seconds before next contact... (Press Enter to skip) ")
        sys.stdout.flush()
        
        # Check for input every 0.1 seconds
        for _ in range(10):
            if check_input():
                sys.stdout.write("\r" + " " * 70 + "\r")  # Clear the line
                sys.stdout.flush()
                return
            time.sleep(0.1)
    
    sys.stdout.write("\r" + " " * 70 + "\r")  # Clear the line
    sys.stdout.flush()

def get_pending_contacts(list_name):
    """Fetch pending contacts from the API"""
    url = f"https://brevo-webhook.replit.app/api/followups/{list_name}?status=PENDING"
    response = requests.get(url)
    if response.status_code == 200:
        json_response = response.json()
        if 'data' in json_response and isinstance(json_response['data'], list):
            return json_response['data']
        else:
            print("No contacts array found in the response")
            return []
    else:
        print(f"Error fetching contacts for {url}:", response.status_code)
        return []

def update_contact(contact_id, status, message):
    """Update a contact's status and message"""
    try:
        url = f"https://brevo-webhook.replit.app/api/followups/{contact_id}"
        data = {
            "status": status,
            "statusText": message
        }
        response = requests.put(url, json=data)
        if response.status_code == 200:
            print(f"Successfully updated contact {contact_id} to status {status}")
            return True
        else:
            error_msg = f"Error updating contact {contact_id}: {response.status_code}"
            if response.status_code == 400:
                error_msg += f"\nResponse: {response.text}"
            elif response.status_code == 404:
                error_msg += "\nContact not found"
            elif response.status_code == 429:
                error_msg += "\nRate limit exceeded"
            print(error_msg)
            return False
    except requests.exceptions.RequestException as e:
        print(f"Network error while updating contact {contact_id}: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error while updating contact {contact_id}: {str(e)}")
        return False