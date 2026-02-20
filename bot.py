import os
import time
import random
import requests
import threading
from dotenv import load_dotenv
from datetime import datetime, timedelta
from colorama import Fore, Style, init

# Initialize Colorama
init(autoreset=True)
load_dotenv()

def display_logo():
    print(
        f"""
        {Fore.CYAN + Style.BRIGHT}        ███████╗██╗   ██╗██╗    ███████╗ █████╗ ██╗   ██╗ ██████╗███████╗████████╗
        {Fore.CYAN + Style.BRIGHT}        ██╔════╝██║   ██║██║    ██╔════╝██╔══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝
        {Fore.CYAN + Style.BRIGHT}        ███████╗██║   ██║██║    █████╗  ███████║██║   ██║██║     █████╗     ██║   
        {Fore.CYAN + Style.BRIGHT}        ╚════██║██║   ██║██║    ██╔══╝  ██╔══██║██║   ██║██║     ██╔══╝     ██║   
        {Fore.CYAN + Style.BRIGHT}        ███████║╚██████╔╝██║    ██║     ██║  ██║╚██████╔╝╚██████╗███████╗   ██║   
        {Fore.CYAN + Style.BRIGHT}        ╚══════╝ ╚═════╝ ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝   ╚═╝   
        {Fore.YELLOW + Style.BRIGHT}                 SUI Discord Faucet Bot - Multi-Account Support
        """
    )

def get_env_data():
    tokens_str = os.getenv('DISCORD_TOKENS', '')
    addresses_str = os.getenv('SUI_ADDRESSES', '')
    
    tokens = [t.strip() for t in tokens_str.split(',') if t.strip()]
    addresses = [a.strip() for a in addresses_str.split(',') if a.strip()]
    return tokens, addresses

def log_msg(acc_idx, message, color=Fore.WHITE):
    time_now = datetime.now().strftime('%H:%M:%S')
    print(f"{Fore.LIGHTBLACK_EX}[{time_now}] {Fore.CYAN}[Acc {acc_idx+1}] {color}{message}")

def send_faucet_msg(token, address, channel_id, acc_idx):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    payload = {'content': f"!faucet {address}"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200 or response.status_code == 201:
            log_msg(acc_idx, f"SUCCESS: Sent !faucet {address[:6]}...{address[-4:]}", Fore.GREEN)
            return True
        elif response.status_code == 429:
            log_msg(acc_idx, "RATE LIMIT: Discord is rate limiting your requests.", Fore.RED)
            return False
        else:
            log_msg(acc_idx, f"FAILED: Status {response.status_code} - {response.text}", Fore.RED)
            return False
    except Exception as e:
        log_msg(acc_idx, f"ERROR: {str(e)}", Fore.RED)
        return False

def account_worker(token, address, channel_id, acc_idx):
    # Initial random stagger to prevent all accounts sending at the exact same second
    initial_delay = acc_idx * random.randint(15, 30)
    log_msg(acc_idx, f"Wait {initial_delay}s for initial stagger...", Fore.YELLOW)
    time.sleep(initial_delay)

    while True:
        send_faucet_msg(token, address, channel_id, acc_idx)
        
        # 6 Hours (21600s) + random 2-5 minutes buffer
        wait_time = 21600 + random.randint(120, 300)
        next_run = datetime.now() + timedelta(seconds=wait_time)
        
        log_msg(acc_idx, f"Cooldown: Next request at {next_run.strftime('%Y-%m-%d %H:%M:%S')}", Fore.BLUE)
        time.sleep(wait_time)

if __name__ == "__main__":
    display_logo()
    discord_tokens, sui_addresses = get_env_data()

    if not discord_tokens or not sui_addresses:
        print(f"{Fore.RED}Error: DISCORD_TOKENS or SUI_ADDRESSES missing in .env file.")
        exit()

    target_channel = input(f"{Fore.WHITE}Enter Faucet Channel ID: ").strip()

    num_accounts = min(len(discord_tokens), len(sui_addresses))
    print(f"{Fore.GREEN}Starting {num_accounts} workers...\n")

    for i in range(num_accounts):
        t = threading.Thread(
            target=account_worker, 
            args=(discord_tokens[i], sui_addresses[i], target_channel, i),
            daemon=True
        )
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}System stopped by user.")
