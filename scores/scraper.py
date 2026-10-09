import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import re

HEADERS = {"User-Agent": "DjangoSportsApp/1.0"}

def convert_time_tags(soup_container):
    for time_tag in soup_container.find_all("time"):
        dt_str = time_tag.get("datetime")
        if dt_str:
            try:
                utc_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                central_tz = ZoneInfo("America/Chicago")
                central_dt = utc_dt.astimezone(central_tz)
                formatted_time = central_dt.strftime('%I:%M %p').lstrip('0')
                time_tag.string = f" {formatted_time}"
            except Exception:
                pass

def fix_external_links(soup):
    """Rewrites relative Plain Text Sports links to absolute URLs and opens them in a new tab."""
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("/"):
            a_tag["href"] = f"https://plaintextsports.com{href}"
        # Make external links open in a new tab so users don't lose your dashboard
        a_tag["target"] = "_blank"

def convert_to_local_time(line_text):
    match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*([A-Z]{2,3})', line_text)
    if not match:
        return line_text
    
    time_part, tz_abbr = match.groups()
    
    tz_map = {
        'PT': 'America/Los_Angeles', 'PST': 'America/Los_Angeles', 'PDT': 'America/Los_Angeles',
        'ET': 'America/New_York', 'EST': 'America/New_York', 'EDT': 'America/New_York',
        'CT': 'America/Chicago', 'CST': 'America/Chicago', 'CDT': 'America/Chicago',
        'MT': 'America/Denver', 'MST': 'America/Denver', 'MDT': 'America/Denver'
    }
    
    source_tz_name = tz_map.get(tz_abbr, 'America/New_York')
    
    try:
        dt_obj = datetime.strptime(time_part, '%I:%M %p')
        today = datetime.now().date()
        dt_with_date = datetime(today.year, today.month, today.day, dt_obj.hour, dt_obj.minute)
        
        source_tz = ZoneInfo(source_tz_name)
        local_dt = dt_with_date.replace(tzinfo=source_tz)
        
        target_tz = ZoneInfo('America/Chicago')
        converted_dt = local_dt.astimezone(target_tz)
        
        new_time_str = converted_dt.strftime('%I:%M %p %Z')
        return line_text.replace(f"{time_part} {tz_abbr}", new_time_str)
    except Exception:
        return line_text

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
        
        convert_time_tags(soup)
        
        games = []
        if league_type == 'mls':
            containers = soup.select("div[id]")
        else:
            containers = soup.select("a.text-fg.no-underline")
            
        for container in containers:
            if team.short_name.upper() in container.get_text().upper():
                
                for br in container.find_all("br"):
                    br.replace_with("\n")
                
                for span in container.find_all("span"):
                    if not span.get_text(strip=True):
                        span.replace_with("")
                
                raw_text = container.get_text()
                
                cleaned_lines = []
                for line in raw_text.split("\n"):
                    if "+" in line and "-" in line:
                        continue
                    
                    line_no_pipes = line.replace("|", "")
                    cleaned = line_no_pipes.strip()
                    if not cleaned:
                        continue
                        
                    converted_line = convert_to_local_time(cleaned)
                    
                    parts = [p.strip() for p in converted_line.split("  ") if p.strip()]
                    
                    if len(parts) > 2:
                        team_name = parts[0]
                        score = parts[-1]
                        extras = " ".join(parts[1:-1])
                        normalized_line = f"{team_name:<6} ({extras}){' ' * 10:>5} {score}"
                        cleaned_lines.append(normalized_line)
                    elif len(parts) == 2 and not any(word in parts[0] for word in ["End", "1st", "2nd", "3rd", "OT", "Final"]):
                        cleaned_lines.append(f"{parts[0]:<15} {parts[1]}")
                    else:
                        cleaned_lines.append(converted_line)
                
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
        
        # Convert times to Central Time
        convert_time_tags(soup)

        # Fix relative links so they point to plaintextsports.com instead of your app
        fix_external_links(soup)

        for element in soup.find_all(text=True):
            if element.parent.name not in ['style', 'script', 'time']:
                new_text = convert_to_local_time(element)
                if new_text != element:
                    element.replace_with(new_text)

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
        
        # Fix relative links on standings pages too
        fix_external_links(soup)
        
        styles = "".join([style.string for style in soup.find_all("style") if style.string])
        body_content = soup.body.decode_contents() if soup.body else "Content unavailable"
        return {'styles': styles, 'body_content': body_content}
    except Exception as e:
        return {'styles': "", 'body_content': f"<p>Failed to load standings: {e}</p>"}