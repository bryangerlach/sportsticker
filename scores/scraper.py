import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {"User-Agent": "DjangoSportsApp/1.0"}

def fetch_today_games(team):
    if 'mls' in team.url.lower():
        url = "https://plaintextsports.com/mls/"
        league_type = 'mls'
    else:
        url = "https://plaintextsports.com/nhl/"
        league_type = 'nhl'
        
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        games = []
        
        if league_type == 'mls':
            for div in soup.select("div[id]"):
                # Replace HTML breaks with real newlines, keeping spaces intact
                for br in div.find_all("br"):
                    br.replace_with("\n")
                text_content = div.get_text()
                
                if "-" in div.get('id', ''):
                    game_url = f"https://plaintextsports.com/mls/{datetime.now().strftime('%Y-%m-%d')}/#{div.get('id')}"
                    if team.short_name.upper() in text_content.upper():
                        games.append({'url': game_url, 'text': text_content})
        else:
            for a_tag in soup.select("a.text-fg.no-underline"):
                for br in a_tag.find_all("br"):
                    br.replace_with("\n")
                
                # Keep text exactly as rendered in the ASCII box
                text_content = a_tag.get_text()
                game_url = "https://plaintextsports.com" + a_tag['href']
                
                if team.short_name.upper() in text_content.upper():
                    games.append({'url': game_url, 'text': text_content})
                    
        return games
    except Exception as e:
        return []

def fetch_nhl_team(url):
    return _fetch_team_page(url)

def fetch_mls_team(url):
    return _fetch_team_page(url)

def _fetch_team_page(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        styles = "".join([style.string for style in soup.find_all("style") if style.string])
        body_content = soup.body.decode_contents() if soup.body else "Content unavailable"
        team_name_elem = soup.select_one(".font-bold.text-center")
        team_name = team_name_elem.get_text(strip=True) if team_name_elem else "Team Details"
        return {'name': team_name, 'styles': styles, 'body_content': body_content}
    except Exception as e:
        return {'name': "Error", 'styles': "", 'body_content': f"<p>Failed to load team page: {e}</p>"}

def fetch_nhl_standings(url):
    return _fetch_standings_page(url)

def fetch_mls_standings(url):
    return _fetch_standings_page(url)

def _fetch_standings_page(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        styles = "".join([style.string for style in soup.find_all("style") if style.string])
        body_content = soup.body.decode_contents() if soup.body else "Content unavailable"
        return {'styles': styles, 'body_content': body_content}
    except Exception as e:
        return {'styles': "", 'body_content': f"<p>Failed to load standings: {e}</p>"}