lets create a command called "followup-next.py --list=4ga-list " that when called fetches the following API endpoint:

GET  @https://brevo-webhook.replit.app/api/followups/4ga-lost?status=PENDING 

Retrives the first contact from that list and tries to send a 