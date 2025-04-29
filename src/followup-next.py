import argparse
from agent import Agent
from utils import get_pending_contacts, get_message, update_contact
import time
import sys
import random

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

def process_contact(contact, agent):
    """Process a single contact"""
    print("Processing contact:", contact)
    update_contact(contact.get('id'), "STARTED", "Agent has started contacting the contact")

    # Check if contact has a phone number
    if not contact.get('phone'):
        print(f"Contact {contact.get('id')} is missing a phone number")
        update_contact(contact.get('id'), "ERROR", "Missing phone")
        return False

    # Add tasks for this contact
    agent.addTasks((
        f"Open WhatsApp at web.whatsapp.com",
        f"Click on the + icon for a new chat",
        f"On the search bar, search for the number {contact.get('phone', '')}",
        f"If no results are found, stop because the user does not have whatsapp installed for that number",
        f"If a contact is found under that number, click on it to start a new conversation",
        f"On the right side of the screen, you will find the convertsation empty, make sure the input to write a message is also empty, if not, clear it.",
        f"Compose a new message: {get_message('greeting', contact, agent.name)}",
        "Send the message",
        f"Compose another message: {get_message('subscription_offer', contact, agent.name)}",
        "Send the message"
    ))
    
    # Run the agent
    agent.run()
    return True

def countdown(seconds):
    """Show a countdown timer"""
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\rWaiting {i} seconds before next contact... ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r" + " " * 50 + "\r")  # Clear the line
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description='Process follow-up contacts')
    parser.add_argument('--list', required=True, help='List name to process (e.g., 4ga-list)')
    args = parser.parse_args()

    # Create agent once
    agent = Agent(name="Flor", on_complete=handle_agent_completion)
    
    try:
        while True:
            # Get pending contacts
            contacts = get_pending_contacts(args.list)
            if not contacts or len(contacts) == 0:
                print("No pending contacts found. Waiting for new contacts...")
                countdown(60)  # Wait for 1 minute before checking again
                continue

            # Get the first contact
            global contact  # Make contact accessible to the callback
            contact = contacts[0]
            
            # Process the contact
            process_contact(contact, agent)
            
            # Wait a random time between 3-6 minutes before processing the next contact
            wait_time = random.randint(180, 360)  # Random seconds between 3-6 minutes
            print(f"\nWaiting {wait_time} seconds ({wait_time/60:.1f} minutes) before next contact...")
            countdown(wait_time)
            
    except KeyboardInterrupt:
        print("\nGracefully shutting down...")
        # Clean up if needed
        agent.close()
        print("Shutdown complete.")

if __name__ == "__main__":
    main() 