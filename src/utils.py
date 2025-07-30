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
    """
    Get a message from the list configuration and personalize it for a contact
    Obtiene un mensaje de la configuración de la lista y lo personaliza para un contacto
    """
    if message_type not in list_config['messages']:
        raise ValueError(f"Message type '{message_type}' not found in list configuration")
    
    # Get the message in the contact's language (default to English if not specified)
    # Obtiene el mensaje en el idioma del contacto (por defecto inglés si no está especificado)
    lang = contact.get('utmLanguage', 'en')
    if lang not in list_config['messages'][message_type]:
        lang = 'en'  # Fallback to English if the language is not available
        # Si el idioma no está disponible, usa inglés por defecto
    
    message = list_config['messages'][message_type][lang]
    
    # Get contact name, ensure it's not empty
    # Obtiene el nombre del contacto, asegura que no esté vacío
    contact_name = contact.get('name', '').strip()
    if not contact_name:
        contact_name = "amigo"  # Default fallback name in Spanish
        if lang == 'en':
            contact_name = "friend"  # Default fallback name in English
    
    # Replace placeholders
    # Reemplaza los marcadores de posición
    try:
        # First replace {{contact.name}} with contact_name
        # Primero reemplaza {{contact.name}} por el nombre del contacto
        message = message.replace('{{contact.name}}', contact_name)
        
        # Then replace {agent_name} with the actual agent name
        # Luego reemplaza {agent_name} por el nombre del agente
        message = message.replace('{agent_name}', agent_name)
        
        # Finally, replace any course placeholders if present
        # Finalmente, reemplaza cualquier marcador de curso si está presente
        if '{course}' in message:
            message = message.format(course=contact.get('course', 'generic'))
            
        return message
    except Exception as e:
        print(f"Error formatting message: {e}")
        return message  # Return unformatted message as fallback
        # Devuelve el mensaje sin formato si ocurre un error

def load_list_config(list_name):
    """
    Load the configuration for a specific list from its YML file
    Carga la configuración para una lista específica desde su archivo YML
    """
    yml_path = os.path.join('src', 'followup-list', f'{list_name}.yml')
    if not os.path.exists(yml_path):
        raise FileNotFoundError(f"List configuration file not found: {yml_path}")
    
    with open(yml_path, 'r') as f:
        return yaml.safe_load(f)

def process_template_string(template_str, contact, agent_name, list_config):
    """
    Process a template string, replacing variables and function calls
    Procesa una cadena de plantilla, reemplazando variables y llamadas de función
    """
    # Replace get_message calls
    # Reemplaza llamadas a get_message
    if '{{get_message(' in template_str:
        # Extract the message type and format the get_message call
        # Extrae el tipo de mensaje y formatea la llamada a get_message
        parts = template_str.split('{{get_message(')[1].split(')}}')[0]
        message_type = parts.split(',')[0].strip("'")
        
        # Format the message type with contact values if needed
        # Formatea el tipo de mensaje con los valores del contacto si es necesario
        if '{course}' in message_type:
            course = contact.get('course', 'generic')
            message_type = message_type.replace('{course}', course)
        if '{academy}' in message_type:
            academy = contact.get('academy', '')
            if academy:
                message_type = message_type.replace('{academy}', academy)
            else:
                # If no academy specified, fall back to the course-only template
                # Si no se especifica academia, usa la plantilla solo de curso
                message_type = message_type.split('_and_academy_')[0]
                
        return get_message(message_type, contact, agent_name, list_config)
    
    # Handle contact variables with {{contact.field}} syntax
    # Maneja variables de contacto con la sintaxis {{contact.campo}}
    if '{{contact.' in template_str:
        # Find all contact variable references
        # Encuentra todas las referencias de variables de contacto
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
    """
    Show a countdown timer that can be skipped by pressing Enter
    Muestra un temporizador regresivo que se puede omitir presionando Enter
    """
    def check_input():
        if os.name == 'nt':  # Windows
            # Check for Enter key on Windows
            # Verifica la tecla Enter en Windows
            return msvcrt.kbhit() and msvcrt.getch() == b'\r'
        else:  # Unix-like
            # Check for Enter key on Unix-like systems
            # Verifica la tecla Enter en sistemas tipo Unix
            return select.select([sys.stdin], [], [], 0)[0] and sys.stdin.read(1) == '\n'

    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\rWaiting {i} seconds before next contact... (Press Enter to skip) ")
        # EN: Esperando antes del siguiente contacto... (Presiona Enter para saltar)
        # ES: Esperando antes del siguiente contacto... (Presiona Enter para saltar)
        sys.stdout.flush()
        
        # Check for input every 0.1 seconds
        # Verifica la entrada cada 0.1 segundos
        for _ in range(10):
            if check_input():
                sys.stdout.write("\r" + " " * 70 + "\r")  # Clear the line
                # Limpia la línea
                sys.stdout.flush()
                return
            time.sleep(0.1)
    
    sys.stdout.write("\r" + " " * 70 + "\r")  # Clear the line
    # Limpia la línea
    sys.stdout.flush()

def get_pending_contacts(list_name):
    """
    Fetch pending contacts from the API
    Obtiene contactos pendientes desde la API
    """
    url = f"https://brevo-webhook.replit.app/api/followups/{list_name}?status=PENDING"
    response = requests.get(url)
    if response.status_code == 200:
        json_response = response.json()
        if 'data' in json_response and isinstance(json_response['data'], list):
            return json_response['data']
        else:
            print("No contacts array found in the response") # EN: No contacts array found
            print("No se encontró el arreglo de contactos en la respuesta") # ES: No se encontró el arreglo de contactos
            return []
    else:
        print(f"Error fetching contacts for {url}:", response.status_code) # EN: Error fetching contacts
        print(f"Error al obtener contactos para {url}:", response.status_code) # ES: Error al obtener contactos
        return []

def update_contact(contact_id, status, message):
    """
    Update a contact's status and message in the API
    Actualiza el estado y mensaje de un contacto en la API
    """
    try:
        url = f"https://brevo-webhook.replit.app/api/followups/{contact_id}"
        data = {
            "status": status,
            "statusText": message
        }
        response = requests.put(url, json=data)
        if response.status_code == 200:
            print(f"Successfully updated contact {contact_id} to status {status}") # EN: Successfully updated contact
            print(f"Contacto {contact_id} actualizado exitosamente al estado {status}") # ES: Contacto actualizado exitosamente
            return True
        else:
            error_msg = f"Error updating contact {contact_id}: {response.status_code}" # EN: Error updating contact
            error_msg = f"Error al actualizar el contacto {contact_id}: {response.status_code}" # ES: Error al actualizar el contacto
            if response.status_code == 400:
                error_msg += f"\nResponse: {response.text}"
            elif response.status_code == 404:
                error_msg += "\nContact not found"
                error_msg += "\nContacto no encontrado" # ES: Contacto no encontrado
            elif response.status_code == 429:
                error_msg += "\nRate limit exceeded"
                error_msg += "\nLímite de solicitudes excedido" # ES: Límite de solicitudes excedido
            print(error_msg)
            return False
    except requests.exceptions.RequestException as e:
        print(f"Network error while updating contact {contact_id}: {str(e)}") # EN: Network error
        print(f"Error de red al actualizar el contacto {contact_id}: {str(e)}") # ES: Error de red
        return False
    except Exception as e:
        print(f"Unexpected error while updating contact {contact_id}: {str(e)}") # EN: Unexpected error
        print(f"Error inesperado al actualizar el contacto {contact_id}: {str(e)}") # ES: Error inesperado
        return False
