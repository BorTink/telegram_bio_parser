import pandas as pd
from telethon import TelegramClient, functions, types
import re
import asyncio
import requests
from bs4 import BeautifulSoup
import time
import random

# Regular expression to extract all usernames from the bio
username_regex = r'@\w+'

# Your actual API credentials
api_id = 23637041
api_hash = '222e9ed7cdd437dda6888281b377f83a'
client = TelegramClient('session_name', api_id, api_hash)

# Paths to your text files
excel_file = 'output_real.xlsx'  # Update this path

# Read channel links from text file
channels_links = pd.read_excel(excel_file)
channels_links = channels_links['url']

table_start = 0
table_cur = table_start


def replace_html_tags_with_spaces(html_text):
    pattern = re.compile(r'<[^>]+>')
    res = pattern.sub(' ', html_text)
    res = res.replace('\n', ' ')
    return res


def get_random_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'DNT': '1'
    }
    return headers


def random_delay():
    time.sleep(random.uniform(1, 3))


def parse_telegram_channel(url):
    session = requests.Session()
    headers = get_random_headers()

    # Fetch the web page with random headers
    response = session.get(url, headers=headers)

    # Introduce a random delay to mimic human browsing behavior
    random_delay()

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        channel_description_section = soup.find('p', class_='card-text mt-3')
        channel_name = soup.find('h1')
        if channel_name:
            channel_name = channel_name.get_text(strip=True)
        else:
            channel_name = 'Channel Name not found'

        if channel_description_section:
            d = str(channel_description_section)
            description_text = replace_html_tags_with_spaces(d)
            return description_text, channel_name
        else:
            return 'Description section not found.', 'None'
    else:
        return f'Failed to retrieve the page. Status code: {response.status_code}', 'None'


async def get_entity_with_retry(client, username_or_id):
    while True:
        try:
            entity = await client.get_entity(username_or_id)
            return entity
        except Exception as e:
            if 'A wait of' in str(e):
                wait_time = int(re.search(r'(\d+) seconds', str(e)).group(1))
                print(f"Rate limit exceeded. Waiting for {wait_time} seconds...")
                await asyncio.sleep(wait_time + 1)  # Wait for the required time plus a buffer
            else:
                print(f"Failed to process {username_or_id}: {e}")
                return None


async def get_channel_admins(table_start):
    table_cur = table_start
    channel_info_list = []
    request_count = 0
    for link in channels_links[table_start:]:
        if channel_info_list:
            print(channel_info_list[-1])
        if request_count >= 20:
            print("Rate limit reached, waiting for 2 seconds...")
            await asyncio.sleep(2)
            request_count = 0

        try:
            request_count += 1
            description_info, channel_name = parse_telegram_channel(link)

            # Use regular expression to find all usernames
            usernames = re.findall(username_regex, description_info)

            # Filter out potential channel usernames
            individual_usernames = []
            # for username in usernames:
            #     if request_count >= 20:
            #         print("Rate limit reached, waiting for 2 seconds...")
            #         await asyncio.sleep(2)
            #         request_count = 0
            #
            #     user_entity = await get_entity_with_retry(client, username)
            #     request_count += 1
            #
            #     if user_entity and isinstance(user_entity, types.User) and not user_entity.bot:
            #         individual_usernames.append(username)
            #     await asyncio.sleep(0.1)  # Small delay to avoid hitting rate limits

            # Append the information to our list
            channel_info_list.append({
                'Channel Link': link,
                'Channel Name': channel_name,
                'Usernames': ', '.join(usernames) if usernames else 'No individual usernames found'
            })
            print(channel_info_list[-1])
        except Exception as e:
            print(f"Failed to process {link}: {e}")
            channel_info_list.append({
                'Channel Link': link,
                'Channel Name': 'Failed to retrieve name',
                'Usernames': 'Error 2'
            })

        table_cur = table_cur + 1
        if table_cur % 100 == 0:
            table_start = table_cur
            print('SLEEPING FOR 4 HOURS FOR COOLDOWN')
            time.sleep(3600 * 4)  # program stops for 4 hours for cooldown

        time.sleep(0.1)

        await asyncio.sleep(0.1)  # Small delay to avoid hitting rate limits

    # Create a DataFrame and export to Excel
    df = pd.DataFrame(channel_info_list)
    df.to_excel('channel_contacts.xlsx', index=False)
    print('Completed')

# Execute the async function
with client:
    client.loop.run_until_complete(get_channel_admins(table_start=table_start))

print("Completed. Check the 'channel_contacts.xlsx' file.")
