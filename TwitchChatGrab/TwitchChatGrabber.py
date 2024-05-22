import os
import socket
import re
from colorama import Fore, Back, Style, init
import random
import time
import concurrent.futures
import requests
import keyboard
from dotenv import load_dotenv

init(autoreset=True)

load_dotenv()

CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
oauth_token = os.getenv('TWITCH_OAUTH_TOKEN')
GetUserID = False
MESSAGE_RATE = 0.2
MAX_QUEUE_LENGTH = 50
MAX_WORKERS = 100
last_time = time.time()
message_queue = []
active_tasks = []
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

class Twitch:
    re_prog = None
    sock = None
    partial = b''
    login_ok = False
    channel = ''
    login_timestamp = 0

    def twitch_connect(self, channel):
        if self.sock: self.sock.close()
        self.sock = None
        self.partial = b''
        self.login_ok = False
        self.channel = channel

        self.re_prog = re.compile(b'^(?::(?:([^ !\r\n]+)![^ \r\n]*|[^ \r\n]*) )?([^ \r\n]+)(?: ([^:\r\n]*))?(?: :([^\r\n]*))?\r\n', re.MULTILINE)

        print(Fore.CYAN + 'Connecting to Twitch...')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sock.connect(('irc.chat.twitch.tv', 6667))

        user = 'justinfan%i' % random.randint(10000, 99999)
        print(Fore.GREEN + 'Successfully connected to Twitch.')
        print(Fore.CYAN + 'Logging in anonymously as ' + Fore.BLUE + user + Fore.GREEN + ' ...')
        self.sock.send(('PASS asdf\r\nNICK %s\r\n' % user).encode())

        self.sock.settimeout(1.0/60.0)

        self.login_timestamp = time.time()

    def reconnect(self, delay):
        time.sleep(delay)
        self.twitch_connect(self.channel)

    def receive_and_parse_data(self):
        buffer = b''
        while True:
            received = b''
            try:
                received = self.sock.recv(4096)
            except socket.timeout:
                break
            if not received:
                print(Fore.RED + 'Connection closed by Twitch. Reconnecting in 5 seconds...')
                self.reconnect(5)
                return []
            buffer += received

        if buffer:
            if self.partial:
                buffer = self.partial + buffer
                self.partial = []

            res = []
            matches = list(self.re_prog.finditer(buffer))
            for match in matches:
                res.append({
                    'name':     (match.group(1) or b'').decode(errors='replace'),
                    'command':  (match.group(2) or b'').decode(errors='replace'),
                    'params':   list(map(lambda p: p.decode(errors='replace'), (match.group(3) or b'').split(b' '))),
                    'trailing': (match.group(4) or b'').decode(errors='replace'),
                })

            if not matches:
                self.partial += buffer
            else:
                end = matches[-1].end()
                if end < len(buffer):
                    self.partial = buffer[end:]

            return res

        return []

    def twitch_receive_messages(self):
        privmsgs = []
        for irc_message in self.receive_and_parse_data():
            cmd = irc_message['command']
            if cmd == 'PRIVMSG':
                privmsgs.append({
                    'username': irc_message['name'],
                    'message': irc_message['trailing'],
                })
            elif cmd == 'PING':
                self.sock.send(b'PONG :tmi.twitch.tv\r\n')
            elif cmd == '001':
                print(Fore.GREEN + 'Successfully logged in.')
                print(Fore.CYAN + 'Joining channel ' + Fore.BLUE + "%s." % self.channel)
                self.sock.send(('JOIN #%s\r\n' % self.channel).encode())
                self.login_ok = True
            elif cmd == 'JOIN':
                print(Fore.GREEN + 'Successfully joined channel ' + Fore.BLUE + '%s' % irc_message['params'][0].lstrip('#'))
                print(' ')

        if not self.login_ok:
            if time.time() - self.login_timestamp > 10:
                print(Fore.RED + 'No response from Twitch. Reconnecting...')
                self.reconnect(0)
                return []

        return privmsgs

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

def handle_message(message):
    try:
        msg = message['message']
        username = message['username'].lower()

        if GetUserID:
            user_id = get_user_id(username, CLIENT_ID, oauth_token)
            print(f"{username} ({user_id}): {msg}")
        else:
            print(f"{username}: {msg}")

        if msg.lower() == "hello":
            print(Fore.MAGENTA + "User said Hello")

        if "hello" in msg.lower():
            print(Fore.MAGENTA + "User said Hello")
    except Exception as exception:
        print(Fore.RED + "Encountered exception: " + Fore.YELLOW + str(exception))

t = Twitch()

# Get the Twitch username from the user
twitch_username = input("Enter the Twitch username to grab the chats from: ")
t.twitch_connect(twitch_username)

while True:
    new_messages = t.twitch_receive_messages()
    if new_messages:
        message_queue += new_messages
        message_queue = message_queue[-MAX_QUEUE_LENGTH:]

    if not message_queue:
        last_time = time.time()
    else:
        r = 1 if MESSAGE_RATE == 0 else (time.time() - last_time) / MESSAGE_RATE
        n = int(r * len(message_queue))
        if n > 0:
            messages_to_handle = message_queue[0:n]
            del message_queue[0:n]
            last_time = time.time()
            for message in messages_to_handle:
                if len(active_tasks) <= MAX_WORKERS:
                    active_tasks.append(thread_pool.submit(handle_message, message))
                else:
                    print(Back.YELLOW + Fore.RED + Style.BRIGHT + f'WARNING: active tasks ({len(active_tasks)}) exceeds number of workers ({MAX_WORKERS}). ({len(message_queue)} messages in the queue)')

    if keyboard.is_pressed('shift+backspace'):
        print(' ')
        print('\033[1m' + Back.YELLOW + Fore.RED + 'Program ended by user' + '\033[0m')
        print(' ')
        exit()