import concurrent.futures
import time
import os
from colorama import Fore, Back, Style, init        # colouring in the console
import requests
import keyboard         # killswitch
import TwitchChat






############################################## Settings ##############################################

# Replace this with the Twitch username of the Channel you want to connect to.
TWITCH_CHANNEL = 'username' 

# If you want to get the User ID, set this to True, otherwise leave it on False.
GetUserID = True

    # Remember to setup your Client_ID, Client_Secret & OAuth_Token in your environment variables if you want to get the User ID.
if GetUserID == True:
    CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
    CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
    oauth_token = os.getenv('TWITCH_OAUTH_TOKEN')

# The lower the message_rate, the faster the messages are processed: it's the number of seconds it will take to handle all messages in the queue.
# Twitch delivers messages in batches, if set to 0 it will process it instantly, that's pretty bad if you have many messages incoming.
# So if you don't have many messages, just leave it on 0.2, it's nearly not noticeable.
MESSAGE_RATE = 0.2

# If you have a lot of messages, you can for example put in 10, so it will only process the first 10 messages of the queue/batch, the rest will be deleted.
# This won't be a problem for most people. 
MAX_QUEUE_LENGTH = 100

######################################## <-  ›   ⏑.⏑   ‹  -> ########################################





last_time = time.time()
message_queue = []
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count())
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
            
        print(Fore.YELLOW + 'Please set the environment variables for the script to work properly. Remember that after setting up the environment variables, you need to restart your editor.')
        print(' ')
        print('\033[1m' + Back.YELLOW + Fore.RED + 'Program ended' + '\033[0m')
        print(' ')
        exit()
    else:
        print(Fore.GREEN + 'Client ID: ' + Fore.BLUE + f'{CLIENT_ID[:5]}.......{CLIENT_ID[-3:]}', Fore.GREEN + 'Client Secret: ' + Fore.BLUE + f'{CLIENT_SECRET[:5]}.......{CLIENT_SECRET[-3:]}', Fore.GREEN + 'OAuth Token: ' + Fore.BLUE + f'{oauth_token[:5]}.......{oauth_token[-3:]}', sep='\n')


            # If you are logging and want to see your hidden tokens, remove the comment before the print.
            # BE AWARE: DON'T DO THIS IF YOU STREAM OR RECORD! EVERYBODY THAT IS ABLE TO SEE YOUR SCREEN WILL KNOW YOUR TOKENS!!
            
        # print(Fore.GREEN + 'Client ID: ' + Fore.BLUE + f'{CLIENT_ID}', Fore.GREEN + 'Client Secret: ' + Fore.BLUE + f'{CLIENT_SECRET}', Fore.GREEN + 'OAuth Token: ' + Fore.BLUE + f'{oauth_token}', sep='\n')
        
        
        
# Countdown before the script starts, upper the counter if you need to select a window before the program starts.
countdown = 2
print(' ')
if countdown != 0:
    print('Starting the script in ...')
    while countdown > 0:
        print(countdown)
        countdown -= 1
        time.sleep(1)
    print(' ')
    


TwitchModule = TwitchChat.Twitch()
TwitchModule.twitch_connect(TWITCH_CHANNEL)


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
def handle_message(message):
    try:
        msg = message['message']
        username = message['username']
        
        if GetUserID == True:
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
            
            



##################################### <-  ›   ⏑.⏑   ‹  -> #####################################
    except Exception as exception:
        print(Fore.RED + "Encountered exception: " + Fore.YELLOW + str(exception))



while True:

    active_tasks = [task for task in active_tasks if not task.done()]

    # Check for new messages
    new_messages = TwitchModule.twitch_receive_messages();
    if new_messages:
        message_queue += new_messages; # New messages are added to the back of the queue
        message_queue = message_queue[-MAX_QUEUE_LENGTH:] # Shorten the queue to only the most recent X messages

    messages_to_handle = []
    if not message_queue: # No messages in the queue
        last_time = time.time()
    else:
        # Determine how many messages it should handle now
        msg_rate = 1 if MESSAGE_RATE == 0 else (time.time() - last_time) / MESSAGE_RATE # If MESSAGE_RATE is 0, it will process all messages instantly (1), else it will process them in the time specified
        msg_to_handle = int(msg_rate * len(message_queue))
        if msg_to_handle > 0:
            # Removes the messages from the queue that it handled
            messages_to_handle = message_queue[0:msg_to_handle]
            del message_queue[0:msg_to_handle]
            last_time = time.time();



    if not messages_to_handle:
        continue
    else:
        for message in messages_to_handle:
            if len(active_tasks) <= os.cpu_count():
                active_tasks.append(thread_pool.submit(handle_message, message))
            else:
                print(Back.YELLOW + Fore.RED + Style.BRIGHT + f'WARNING: active tasks ({len(active_tasks)}) exceeds number of workers ({os.cpu_count()}). ({len(message_queue)} messages in the queue)')
 
 
 
    # If User presses Shift+Backspace, automatically end the program - Killswitch
    if keyboard.is_pressed('shift+backspace'):
        
        print(' ')
        print('\033[1m' + Back.YELLOW + Fore.RED + 'Program ended by user' + '\033[0m')
        print(' ')
        exit()