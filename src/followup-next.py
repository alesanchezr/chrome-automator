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
import random, os
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
    update_contact(contact.get('id'), "STARTED", "Agent has started contacting the contact")

    # Check if contact has a phone number
    if not contact.get('phone'):
        print(f"Contact {contact.get('id')} is missing a phone number")
        update_contact(contact.get('id'), "ERROR", "Missing phone")
        return False

    # Process tasks from the YML configuration
    tasks = []
    for task_item in list_config['agent']['tasks']:
        task = task_item['task']
        # Process any template variables in the task
        processed_task = process_template_string(task, contact, _agent.name, list_config)
        tasks.append(processed_task)

    # Add tasks for this contact
    _agent.addTasks(tuple(tasks))
    
    # Run the agent
    _agent.run()
    return True

def main():
    parser = argparse.ArgumentParser(description='Process follow-up contacts')
    parser.add_argument('--list', required=True, help='List name to process (e.g., 4ga-lost)')
    args = parser.parse_args()

    # Load list configuration
    list_config = load_list_config(args.list)
    
    # Create BrowserAgent with name from config
    browserAgent = BrowserAgent(name=list_config['agent']['name'], on_complete=handle_agent_completion)
    
    try:
        while True:
            # Get pending contacts
            contacts = get_pending_contacts(args.list)
            if not contacts or len(contacts) == 0:
                print("No pending contacts found. Waiting for new contacts...")
                countdown(5)  # Wait for 5 seconds before checking again
                continue

            # Get the first contact
            global contact  # Make contact accessible to the callback
            contact = contacts[0]
            
            # Process the contact
            process_contact(contact, browserAgent, list_config)
            
            # Wait a random time between 3-6 minutes before processing the next contact
            wait_time = random.randint(1*60, 4*60)  # Random seconds between 3-6 minutes
            print(f"\nWaiting {wait_time} seconds ({wait_time/60:.1f} minutes) before next contact...")
            countdown(wait_time)
            
    except KeyboardInterrupt:
        print("\nGracefully shutting down...")
        # Clean up if needed
        browserAgent.close()
        print("Shutdown complete.")

if __name__ == "__main__":
    main() 