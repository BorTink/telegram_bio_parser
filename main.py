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
# client = TelegramClient('session_name', api_id, api_hash)

# Paths to your text files
excel_file = 'output_real.xlsx'  # Update this path

# Read channel links from text file
channels_links = pd.read_excel(excel_file)
channels_links = channels_links['url']

table_start = 0
table_cur = table_start

def get_free_proxies():
    proxies = []
    urls = [
        "https://www.sslproxies.org/",
        "https://free-proxy-list.net/",
        "https://www.us-proxy.org/"
    ]

    for url in urls:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            # Try to find the table using different approaches
            table = soup.find("table", {"class": "table table-striped table-bordered"})

            if table and table.tbody:
                for row in table.tbody.find_all("tr"):
                    tds = row.find_all("td")
                    if len(tds) > 6 and tds[4].text.strip() == "elite proxy" and tds[6].text.strip() == "yes":
                        proxy = f"http://{tds[0].text.strip()}:{tds[1].text.strip()}"
                        if is_proxy_working(proxy):
                            proxies.append(proxy)
                    if len(proxies) >= 10:
                        break
            else:
                print(f"No valid proxy table found at {url}")
        except Exception as e:
            print(f"Failed to get proxies from {url}: {e}")

    return proxies


def is_proxy_working(proxy):
    try:
        response = requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=5)
        return response.status_code == 200
    except:
        return False

# List of proxy servers
# proxies = get_free_proxies()
proxies = ['http://221.140.235.236:5002', 'http://189.240.60.166:9090', 'http://189.240.60.168:9090', 'http://103.235.67.130:80', 'http://189.240.60.169:9090', 'http://189.240.60.171:9090', 'http://203.209.80.44:3128', 'http://172.183.241.1:8080', 'http://221.140.235.237:5002', 'http://189.240.60.169:9090']


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
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/601.6.17 (KHTML, like Gecko) Version/9.1.2 Safari/601.6.17",
    ]
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1'
    }
    return headers


def random_delay():
    time.sleep(random.uniform(3, 10))  # Increased delay to reduce load on the server


def get_random_proxy():
    return random.choice(proxies)


def parse_telegram_channel(url):
    session = requests.Session()
    headers = get_random_headers()
    proxy = get_random_proxy()

    # Fetch the web page with random headers and proxy
    response = session.get(url, headers=headers)

    # Introduce a random delay to mimic human browsing behavior
    random_delay()

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        channel_description_section = soup.find('p', class_='card-text mt-3')
        channel_name = soup.find('h1')
        if (channel_name):
            channel_name = channel_name.get_text(strip=True)
        else:
            channel_name = 'Channel Name not found'

        if (channel_description_section):
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

def get_channel_admins(table_start):
    table_cur = table_start
    channel_info_list = []
    request_count = 0
    for link in channels_links[table_start:]:
        if request_count >= 20:
            print("Rate limit reached, waiting for 2 seconds...")
            time.sleep(2)
            request_count = 0

        try:
            request_count += 1
            description_info, channel_name = parse_telegram_channel(link)

            # Use regular expression to find all usernames
            usernames = re.findall(username_regex, description_info)

            # Filter out potential channel usernames
            individual_usernames = []

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
            time.sleep(3600 * 4)  # program stops for 4 hours for cooldown

        time.sleep(0.1)

    # Create a DataFrame and export to Excel
    df = pd.DataFrame(channel_info_list)
    df.to_excel('channel_contacts.xlsx', index=False)
    print('Completed')


get_channel_admins(table_start=table_start)

print("Completed. Check the 'channel_contacts.xlsx' file.")
