import argparse
from agent import BrowserAgent
from utils import (
    get_pending_contacts, 
    update_contact, 
    get_message, 
    load_list_config, 
    process_template_string, 
    countdown
)
import random, os, asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

def handle_agent_completion(history):
    """Handle the completion of agent tasks"""
    if history.is_done() and not history.has_errors():
        print("Agent completed tasks successfully")
        # Get the last thought from the history
        thoughts = history.model_thoughts()
        if thoughts and len(thoughts) > 0:
            last_thought = thoughts[-1]
            
            if hasattr(last_thought, 'evaluation_previous_goal'):
                message = last_thought.evaluation_previous_goal
            else:
                message = str(last_thought)

            status = "COMPLETE" if "success" in message.lower() else "INCOMPLETE"
            update_contact(contact.get('id'), status, message)
        else:
            update_contact(contact.get('id'), "INCOMPLETE", "No thoughts found on the browser agent")
    else:
        print("Agent failed to complete tasks")
        error_message = "Failed to draft message"
        if history.has_errors():
            error_message = f"Error: {history.errors}"
        update_contact(contact.get('id'), "ERROR", error_message)

def process_contact(contact, _agent, list_config):
    """Process a single contact"""
    if not contact:
        print("Invalid contact object")
        return False

    update_contact(contact.get('id'), "STARTED", "Agent has started contacting the contact")

    # Check if contact has a phone number
    if not contact.get('phone'):
        print(f"Contact {contact.get('id')} is missing a phone number")
        update_contact(contact.get('id'), "ERROR", "Missing phone")
        return False

    # Process tasks from the YML configuration
    tasks = []
    
    for task_item in list_config['agent']['tasks']:
        # Skip tasks that are specific to a different system
        if 'system' in task_item and task_item['system'] != _agent.system:
            continue
            
        task = task_item['task']
        # Process any template variables in the task
        processed_task = process_template_string(task, contact, _agent.name, list_config)
        tasks.append(processed_task)

    # Add tasks for this contact
    _agent.addTasks(tuple(tasks))
    
    # Run the agent
    _agent.run()
    return True

def handle_development_contact(contact):
    """Handle a contact in development mode - only returns if we should process this contact"""
    if not contact.get('email'):
        print(f"Skipping {contact.get('id')} in development mode: no email")
        return False
    
    if '@4geeksacademy.com' not in contact['email']:
        print(f"Skipping {contact.get('id')} in development mode (email: {contact.get('email')}) because it is not a 4Geeks Academy email")
        return False
        
    return True  # Process only 4geeks.com emails

def process_contact_queue(contacts, list_config, loop, browserAgent=None):
    """Process a queue of contacts"""
    if not contacts:
        return None, None
        
    for current_contact in contacts:
        # In development mode, only process 4geeks.com emails
        if os.getenv('ENVIRONMENT') == 'development':
            if not current_contact.get('email') or '@4geeksacademy.com' not in current_contact['email']:
                print(f"Skipping {current_contact.get('id')} in development mode (email: {current_contact.get('email')}) because it is not a 4Geeks Academy email")
                continue
                
        # We found a contact to process
        return current_contact, browserAgent or BrowserAgent(name=list_config['agent']['name'], on_complete=handle_agent_completion)
        
    # No contacts to process
    return None, browserAgent

def main():
    parser = argparse.ArgumentParser(description='Process follow-up contacts')
    parser.add_argument('--list', required=True, help='List name to process (e.g., 4ga-lost)')
    args = parser.parse_args()

    # Load list configuration
    list_config = load_list_config(args.list)
    
    # Create a single asyncio event loop for the whole script
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create BrowserAgent with name from config
    browserAgent = None
    try:
        while True:
            try:
                # Get pending contacts
                contacts = get_pending_contacts(args.list)
                if not contacts:
                    print("No pending contacts found. Waiting for 5 minutes...")
                    countdown(300)  # Wait for 5 minutes before checking again
                    continue

                # Find next contact to process
                global contact  # Make contact accessible to the callback
                contact, browserAgent = process_contact_queue(contacts, list_config, loop, browserAgent)
                
                if not contact:
                    print("No contacts to process at this time. Waiting 5 minutes...")
                    countdown(300)  # Wait for 5 minutes before checking again
                    continue

                # Process the contact
                process_contact(contact, browserAgent, list_config)
                
                # Wait a random time between 1-4 minutes before processing the next contact
                wait_time = random.randint(60, 240)  # Random seconds between 1-4 minutes
                print(f"\nWaiting {wait_time} seconds ({wait_time/60:.1f} minutes) before next contact...")
                countdown(wait_time)

                # Close and recreate the browser agent for each contact to prevent memory issues
                if browserAgent:
                    loop.run_until_complete(browserAgent.close())
                    browserAgent = None
                    
            except Exception as e:
                print(f"Error processing contact: {str(e)}")
                if browserAgent:
                    loop.run_until_complete(browserAgent.close())
                    browserAgent = None
                countdown(60)  # Wait a minute before retrying

    except KeyboardInterrupt:
        print("\nGracefully shutting down...")
        # Clean up if needed
        if browserAgent:
            loop.run_until_complete(browserAgent.close())
        print("Shutdown complete.")
    finally:
        loop.close()

if __name__ == "__main__":
    main()