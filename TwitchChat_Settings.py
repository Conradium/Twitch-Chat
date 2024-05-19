import concurrent.futures
import time
import os
from colorama import Fore, Back, Style, init        # colouring in the console
import requests
import keyboard         # killswitch
import TwitchChat
  


# Remember to setup your Client_ID, Client_Secret & OAuth_Token in your environment variables if you want to get the User ID.
CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
oauth_token = os.getenv('TWITCH_OAUTH_TOKEN')

# If you want to get the User ID, set this to True, otherwise leave it on False.
GetUserID = False

# Replace this with the Twitch username you want to use, if you have problems, try using the username in lowercase
TWITCH_CHANNEL = 'username' 

# The lower the message, the faster the messages are processed: it's the number of seconds it will take to handle all messages in the queue.
# Twitch delivers messages in batches, if set to 0 it will process it instantly, that's pretty bad if you have many messages incoming.
# So if you don't have many messages, just leave it on 0.2.
MESSAGE_RATE = 0.2

# If you have a lot of messages, you can for example put in 10, so it will only process the first 10 messages of the queue/batch, the rest will be deleted.
# This won't be a problem if you aren't getting a lot of messages, so just leave it on 50.  Not recommended to set higher than 50.
MAX_QUEUE_LENGTH = 50

# Maximum number of messages it will process at the same time, just leave it on 100.
MAX_WORKERS = 100




last_time = time.time()
message_queue = []
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
active_tasks = []
init(autoreset=True)


if GetUserID == True:
    if CLIENT_ID == None or CLIENT_SECRET == None or oauth_token == None:
        if CLIENT_ID == None:
            print(Fore.RED + 'Client ID is missing in the environment variables.')
        if CLIENT_SECRET == None:
            print(Fore.RED + 'Client Secret is missing in the environment variables.')
        if oauth_token == None:
            print(Fore.RED + 'OAuth Token is missing in the environment variables.')
        print(Fore.YELLOW + 'Please set the environment variables for the script to work properly. Remember that after setting up the environment variables, you need to restart VSCode (your editor).')
        exit()
    else:
        print(Fore.GREEN + 'Client ID: ' + Fore.BLUE + f'{CLIENT_ID[:5]}.......{CLIENT_ID[-3:]}', Fore.GREEN + 'Client Secret: ' + Fore.BLUE + f'{CLIENT_SECRET[:5]}.......{CLIENT_SECRET[-3:]}', Fore.GREEN + 'OAuth Token: ' + Fore.BLUE + f'{oauth_token[:5]}.......{oauth_token[-3:]}', sep='\n')

            # If you are logging and want to see your hidden tokens, remove the comment before the print.
            
            # BE AWARE: DON'T DO THIS IF YOU STREAM OR RECORD!! IT WILL REVEAL YOUR TOKENS!!
            # EVERYBODY THAT IS ABLE TO SEE YOUR SCREEN WILL KNOW YOUR TOKENS!!
            
        # print(Fore.GREEN + 'Client ID: ' + Fore.BLUE + f'{CLIENT_ID}', Fore.GREEN + 'Client Secret: ' + Fore.BLUE + f'{CLIENT_SECRET}', Fore.GREEN + 'OAuth Token: ' + Fore.BLUE + f'{oauth_token}', sep='\n')
        
        
# Countdown before the script starts, upper the counter if you need to select a window before the program starts.
countdown = 2
print(' ')
if countdown != 0:
    print('Starting countdown ...')
    while countdown > 0:
        print(countdown)
        countdown -= 1
        time.sleep(1)
    print(' ')


t = TwitchChat.Twitch()
t.twitch_connect(TWITCH_CHANNEL)


def get_user_id(username, client_id, oauth_token):
    url = 'https://api.twitch.tv/helix/users'
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {oauth_token}'
    }
    params = {
        'login': username
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data['data']:
            return data['data'][0]['id']
        else:
            return None
    except requests.exceptions.RequestException as exception:
        print(Fore.RED + f"Error fetching user ID for {username}: " + Fore.YELLOW + str(exception))
        return None

    
# Remember that the Username is always lowercase (twitch standard).
# It's better if you use the message at lowercase to avoid problems, but if neccecary, just remove the .lower().
def handle_message(message):
    try:
        msg = message['message']
        username = message['username'].lower()
        
        if GetUserID:
            user_id = get_user_id(username, CLIENT_ID, oauth_token)
            print(f"{username} ({user_id}): {msg}")
        else:
            print(f"{username}: {msg}")
        
        

########################################## Add Rules ##########################################




        # If you use msg.lower(), it will ignore the case of the message.

        # If the message is exactly "hello"
        if msg.lower() == "hello":
            print(Fore.MAGENTA + "User said Hello")

        # If message contains the word "hello"
        if "hello" in msg.lower():
            print(Fore.MAGENTA + "User said Hello")




########################################## <- Love you :3 -> ##########################################
    except Exception as exception:
        print(Fore.RED + "Encountered exception: " + Fore.YELLOW + str(exception))



while True:

    active_tasks = [t for t in active_tasks if not t.done()]

    # Check for new messages
    new_messages = t.twitch_receive_messages();
    if new_messages:
        message_queue += new_messages; # New messages are added to the back of the queue
        message_queue = message_queue[-MAX_QUEUE_LENGTH:] # Shorten the queue to only the most recent X messages

    messages_to_handle = []
    if not message_queue: # No messages in the queue
        last_time = time.time()
    else:
        # Determine how many messages it should handle now
        r = 1 if MESSAGE_RATE == 0 else (time.time() - last_time) / MESSAGE_RATE
        n = int(r * len(message_queue))
        if n > 0:
            # Removes the messages from the queue that it handled
            messages_to_handle = message_queue[0:n]
            del message_queue[0:n]
            last_time = time.time();


    # If User presses Shift+Backspace, automatically end the program - Killswitch
    if keyboard.is_pressed('shift+backspace'):
        
        print(' ')
        print('\033[1m' + Back.YELLOW + Fore.RED + 'Program ended by user' + '\033[0m')
        print(' ')
        exit()
        

    if not messages_to_handle:
        continue
    else:
        for message in messages_to_handle:
            if len(active_tasks) <= MAX_WORKERS:
                active_tasks.append(thread_pool.submit(handle_message, message))
            else:
                print(Back.YELLOW + Fore.RED + Style.BRIGHT + f'WARNING: active tasks ({len(active_tasks)}) exceeds number of workers ({MAX_WORKERS}). ({len(message_queue)} messages in the queue)')
 