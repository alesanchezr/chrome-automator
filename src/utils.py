import yaml
import os
import requests

def load_messages():
    """Load messages from the YAML file"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, 'messages.yml')
    with open(yaml_path, 'r') as file:
        return yaml.safe_load(file)

def get_message(message_id, contact, agent_name="Flor"):
    """Get the appropriate message based on the message ID and contact's language"""
    messages = load_messages()
    if message_id not in messages:
        raise ValueError(f"Message ID '{message_id}' not found in messages.yml")
    
    language = contact.get('utmLanguage', 'en')  # Default to English if no language specified
    message_template = messages[message_id].get(language, messages[message_id]['en'])  # Fallback to English if language not found
    return message_template.format(name=contact.get('name', ''), agent_name=agent_name)

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