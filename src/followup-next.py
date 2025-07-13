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

def create_completion_handler(contact):
    """Create a completion handler for a specific contact"""
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
    return handle_agent_completion

def should_process_contact(contact):
    """Determine whether to process a contact based on environment and contact info"""
    # Always need a phone number
    if not contact.get('phone'):
        print(f"Contact {contact.get('id')} is missing a phone number")
        update_contact(contact.get('id'), "ERROR", "Missing phone")
        return False
        
    # In development mode, only process 4geeks.com emails
    if os.getenv('ENVIRONMENT') == 'development':
        if not contact.get('email'):
            print(f"Skipping {contact.get('id')} in development mode: no email")
            return False
            
        if '@4geeksacademy.com' not in contact['email'].lower():
            print(f"Skipping {contact.get('id')} in development mode: not a 4Geeks Academy email")
            return False
            
        print(f"Processing test contact: {contact.get('email')}")
        
    return True

async def process_contact(contact, _agent, list_config):
    """Process a single contact"""
    if not contact:
        print("Invalid contact object")
        return False

    if not should_process_contact(contact):
        return False

    update_contact(contact.get('id'), "STARTED", "Agent has started contacting the contact")

    max_retries = 3
    for attempt in range(max_retries):
        try:
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
            
            # Run the agent with await since it's an async operation
            await _agent._run()

            # Verify the chat was properly loaded and message sent by checking agent completion
            if hasattr(_agent, 'history') and _agent.history:
                thoughts = _agent.history.model_thoughts()
                if thoughts:
                    # Check for successful message sending indicators
                    success_indicators = [
                        "message sent",
                        "checkmark appears",
                        "message delivered",
                        "type a message"  # Indicates chat is loaded
                    ]
                    thought_texts = [str(thought).lower() for thought in thoughts]
                    if any(indicator in " ".join(thought_texts) for indicator in success_indicators):
                        print("Message sending verified with delivery indicators")
                        return True
                    
            print("Could not verify message sending completion")
            if attempt < max_retries - 1:
                print(f"Retrying attempt {attempt + 1}/{max_retries}...")
            return False
        except Exception as e:
            print(f"Error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                print("Retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue
            else:
                print("Max retries reached, marking contact as error")
                update_contact(contact.get('id'), "ERROR", f"Failed after {max_retries} attempts: {str(e)}")
                return False

async def process_contact_queue(contacts, list_config, loop, browserAgent=None):
    """Process a queue of contacts"""
    if not contacts:
        return None, None
        
    for current_contact in contacts:
        # Check if we should process this contact
        if should_process_contact(current_contact):
            # We found a valid contact to process
            agent = browserAgent or BrowserAgent(
                name=list_config['agent']['name'],
                on_complete=create_completion_handler(current_contact)
            )
            return current_contact, agent
                
    # No valid contacts to process
    return None, browserAgent

async def main_loop(args, list_config, loop):
    """Main processing loop"""
    browserAgent = None
    consecutive_errors = 0
    try:
        while True:
            try:
                if consecutive_errors >= 3:
                    print("Too many consecutive errors, recreating browser agent")
                    if browserAgent:
                        try:
                            await browserAgent.close()
                        except:
                            pass
                    browserAgent = None
                    consecutive_errors = 0
                    await asyncio.sleep(10)  # Wait before retrying
                # Get pending contacts
                contacts = get_pending_contacts(args.list)
                if not contacts:
                    print("No pending contacts found")
                    if os.getenv('ENVIRONMENT') != 'development':
                        print("Waiting for 5 minutes...")
                        countdown(300)  # Wait for 5 minutes before checking again
                    continue

                # Find next contact to process
                contact, browserAgent = await process_contact_queue(contacts, list_config, loop, browserAgent)
                
                if not contact:
                    print("No contacts to process at this time")
                    if os.getenv('ENVIRONMENT') != 'development':
                        print("Waiting 5 minutes...")
                        countdown(300)  # Wait for 5 minutes before checking again
                    continue

                # Process the contact
                process_result = await process_contact(contact, browserAgent, list_config)
                if process_result:
                    consecutive_errors = 0  # Reset error counter on success
                
                # Clean up after the contact is processed
                try:
                    # Wait a bit for status updates to complete
                    await asyncio.sleep(2)
                    
                    # Close browser agent
                    if browserAgent:
                        await browserAgent.close()
                        browserAgent = None
                        
                    # Wait before next contact if we processed this one
                    if process_result:
                        wait_time = random.randint(60, 240)  # Random seconds between 1-4 minutes
                        print(f"\nWaiting {wait_time} seconds ({wait_time/60:.1f} minutes) before next contact...")
                        countdown(wait_time)
                except Exception as e:
                    print(f"Error during cleanup: {str(e)}")
                    if browserAgent:
                        try:
                            await browserAgent.close()
                        except:
                            pass
                        browserAgent = None
                    
            except Exception as e:
                print(f"Error processing contact: {str(e)}")
                consecutive_errors += 1
                if browserAgent:
                    try:
                        await browserAgent.close()
                    except:
                        pass
                    browserAgent = None
                wait_time = min(60 * consecutive_errors, 300)  # Exponential backoff, max 5 minutes
                print(f"Waiting {wait_time} seconds before retrying...")
                countdown(wait_time)

    except KeyboardInterrupt:
        print("\nGracefully shutting down...")
        # Clean up if needed
        if browserAgent:
            await browserAgent.close()
        print("Shutdown complete.")

def main():
    parser = argparse.ArgumentParser(description='Process follow-up contacts')
    parser.add_argument('--list', required=True, help='List name to process (e.g., 4ga-lost)')
    args = parser.parse_args()

    # Load list configuration
    list_config = load_list_config(args.list)
    
    # Create a single asyncio event loop for the whole script
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main_loop(args, list_config, loop))
    finally:
        loop.close()

if __name__ == "__main__":
    main()