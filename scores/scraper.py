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
            containers = soup.select("div[id]")
        else:
            containers = soup.select("a.text-fg.no-underline")
            
        for container in containers:
            if team.short_name.upper() in container.get_text().upper():
                
                # Convert line break tags to actual newlines
                for br in container.find_all("br"):
                    br.replace_with("\n")
                
                # Clean up empty spacing spans
                for span in container.find_all("span"):
                    if not span.get_text(strip=True):
                        span.replace_with("")
                
                raw_text = container.get_text()
                
                # Process lines: strip boxes, pipes, and normalize spacing/extra info
                cleaned_lines = []
                for line in raw_text.split("\n"):
                    if "+" in line and "-" in line:
                        continue
                    
                    line_no_pipes = line.replace("|", "")
                    cleaned = line_no_pipes.strip()
                    if not cleaned:
                        continue
                        
                    # If it's a team line (contains extra status like PP, etc.)
                    # We can normalize internal multi-spaces down or reposition notes if needed
                    # For example, splitting by chunks of whitespace to separate Team, Note, and Score
                    parts = [p.strip() for p in cleaned.split("  ") if p.strip()]
                    
                    if len(parts) > 2:
                        # e.g., ["DAL", "PP 5-4", "1"] -> rearrange to keep score at the end
                        team_name = parts[0]
                        score = parts[-1]
                        extras = " ".join(parts[1:-1])
                        normalized_line = f"{team_name:<6} ({extras}){' ' * 10:>5} {score}"
                        cleaned_lines.append(normalized_line)
                    elif len(parts) == 2 and not any(word in parts[0] for word in ["End", "1st", "2nd", "3rd", "OT", "Final"]):
                        # Standard team line with just Team and Score
                        cleaned_lines.append(f"{parts[0]:<15} {parts[1]}")
                    else:
                        # Status line (like "End 1st")
                        cleaned_lines.append(cleaned)
                
                if league_type == 'mls':
                    if "-" in container.get('id', ''):
                        game_url = f"https://plaintextsports.com/mls/{datetime.now().strftime('%Y-%m-%d')}/#{container.get('id')}"
                    else:
                        continue
                else:
                    game_url = "https://plaintextsports.com" + container.get('href', '')
                
                games.append({
                    'url': game_url,
                    'lines': cleaned_lines
                })
                
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