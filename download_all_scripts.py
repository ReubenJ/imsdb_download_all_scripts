import os
from urllib.parse import quote

from bs4 import BeautifulSoup
import requests
from rich.progress import track
import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
logging.getLogger("requests").setLevel(logging.WARNING)
log = logging.getLogger("IMSDb Script Downloader")

BASE_URL = 'http://www.imsdb.com'
SCRIPTS_DIR = 'scripts'
EXISTING_SCRIPTS = os.listdir(SCRIPTS_DIR)


def clean_script(text):
    text = text.replace('Back to IMSDb', '')
    text = text.replace('''<b><!--
</b>if (window!= top)
top.location.href=location.href
<b>// -->
</b>
''', '')
    text = text.replace('''          Scanned by http://freemoviescripts.com
          Formatting by http://simplyscripts.home.att.net
''', '')
    return text.replace(r'\r', '')


def get_script(relative_link):
    tail = relative_link.split('/')[-1]
    log.info('fetching %s' % tail)
    script_front_url = BASE_URL + quote(relative_link)
    front_page_response = requests.get(script_front_url)
    front_soup = BeautifulSoup(front_page_response.text, "html.parser")

    try:
        script_link = front_soup.find_all('p', align="center")[0].a['href']
    except IndexError:
        log.error('%s has no script :(' % tail)
        return None, None

    if script_link.endswith('.html'):
        title = script_link.split('/')[-1].split(' Script')[0]
        if title.strip('.html') + '.txt' in EXISTING_SCRIPTS:
            log.info('already downloaded %s, skipping...' % tail)
            return None, None
        script_url = BASE_URL + script_link
        script_soup = BeautifulSoup(requests.get(script_url).text, "html.parser")
        script_text = script_soup.find_all('td', {'class': "scrtext"})[0].get_text()
        script_text = clean_script(script_text)
        return title, script_text
    else:
        log.error('%s is a pdf :(' % tail)
        return None, None


if __name__ == "__main__":
    response = requests.get('https://imsdb.com/all-scripts.html')
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    paragraphs = soup.find("h1", text="All Movie Scripts on IMSDb (A-Z)").find_next_siblings("p")

    for p in track(paragraphs):
        relative_link = p.a['href']
        title, script = get_script(relative_link)
        if not script:
            continue

        with open(os.path.join(SCRIPTS_DIR, title.strip('.html') + '.txt'), 'w') as outfile:
            outfile.write(script)
