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
    else:
        url = "https://plaintextsports.com/nhl/"
        
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        convert_time_tags(soup)
        
        games = []
        containers = soup.select("a.text-fg.no-underline, div[id]")
            
        for container in containers:
            container_id = container.get("id", "")
            if container.name == "div" and ("-" not in container_id or container_id in ["page-loaded-wrapper", "data-loaded-wrapper", "full-width-line"]):
                continue

            container_text = container.get_text(separator="  ").upper()
            
            if team.short_name.upper() in container_text or team.name.upper() in container_text:
                cleaned_lines = []
                
                if container.name == "div":
                    game_url = f"https://plaintextsports.com/mls/#{container_id}"
                    
                    # 1. Team Names
                    team_links = container.select(".justified-line a")
                    t1 = team_links[0].get_text(strip=True) if len(team_links) > 0 else "Home"
                    t2 = team_links[1].get_text(strip=True) if len(team_links) > 1 else "Away"
                    
                    # 2. Score & Clock
                    clock = ""
                    score = ""
                    justified = container.select(".justified-line")
                    if len(justified) >= 2:
                        score_spans = justified[1].find_all("span", recursive=False)
                        middle_text = score_spans[1].get_text(" ", strip=True) if len(score_spans) >= 2 else justified[1].get_text(" ", strip=True)
                        
                        # Match pattern: <score1> - <clock> - <score2> (or without extra dash)
                        m = re.search(r'(\d+)\s*-\s*(.+?)(?:\s*-\s*|\s+)(\d+)$', middle_text)
                        if m:
                            s1 = m.group(1).strip()
                            clock = m.group(2).strip().strip("-").strip()
                            s2 = m.group(3).strip()
                            score = f"{s1} - {s2}"
                        else:
                            score = middle_text
                            
                    # 3. Events
                    events = []
                    # Remove headers
                    for rel in container.select(".relative"):
                        rel.extract()
                        
                    for raw in container.get_text().splitlines():
                        line = raw.strip("\r\n|").rstrip()
                        if not line or set(line.strip()).issubset({"+", "-"}):
                            continue
                            
                        clean_text = line.strip()
                        clean_text = clean_text.replace("#yellow", "(Y)").replace("#2nd yellow", "(YY)").replace("#red", "(R)")
                        clean_text = " ".join(clean_text.split())
                        
                        # If it had leading spaces, it belongs to Team 2 (right)
                        is_right = line.startswith("    ") or line.startswith("\t")
                        events.append({
                            'text': clean_text,
                            'align': 'right' if is_right else 'left'
                        })
                        
                    games.append({
                        'url': game_url,
                        'is_structured_mls': True,
                        'team_left': t1,
                        'team_right': t2,
                        'clock': clock,
                        'score': score,
                        'events': events,
                        'lines': []
                    })
                        
                else:
                    game_url = "https://plaintextsports.com" + container.get('href', '')
                    
                    for br in container.find_all("br"):
                        br.replace_with("\n")
                    
                    for span in container.find_all("span"):
                        if not span.get_text(strip=True):
                            span.replace_with("")
                    
                    raw_text = container.get_text()
                    lines = []
                    
                    for line in raw_text.split("\n"):
                        if "+" in line and "-" in line:
                            continue
                        clean = line.replace("|", "").strip()
                        if clean:
                            lines.append(convert_to_local_time(clean))

                    # Parse into structured NHL format if there are 3 game lines (Status, Team 1, Team 2)
                    if len(lines) >= 3:
                        status_line = lines[0]
                        team_lines_formatted = []

                        for team_row in lines[1:3]:
                            parts = [p.strip() for p in team_row.split() if p.strip()]
                            if len(parts) >= 2:
                                team_code = parts[0]
                                # Check if last part is the score
                                if parts[-1].isdigit():
                                    score_val = parts[-1]
                                    extras = " ".join(parts[1:-1])
                                elif len(parts) >= 3 and parts[1].isdigit():
                                    score_val = parts[1]
                                    extras = " ".join(parts[2:])
                                else:
                                    score_val = parts[1]
                                    extras = " ".join(parts[2:])
                                
                                formatted = f"{team_code} {score_val}"
                                if extras:
                                    formatted += f" {extras}"
                                team_lines_formatted.append(formatted)
                            else:
                                team_lines_formatted.append(team_row)

                        games.append({
                            'url': game_url,
                            'is_structured_nhl': True,
                            'status_line': status_line,
                            'team1_line': team_lines_formatted[0] if len(team_lines_formatted) > 0 else '',
                            'team2_line': team_lines_formatted[1] if len(team_lines_formatted) > 1 else '',
                            'lines': lines
                        })
                    else:
                        games.append({
                            'url': game_url,
                            'lines': lines
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
        
        convert_time_tags(soup)
        fix_external_links(soup)
        inject_schedule_theme(soup)  # <-- Uses schedule styling

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
        
        fix_external_links(soup)
        inject_standings_theme(soup)  # <-- Uses standings styling
        
        styles = "".join([style.string for style in soup.find_all("style") if style.string])
        body_content = soup.body.decode_contents() if soup.body else "Content unavailable"
        return {'styles': styles, 'body_content': body_content}
    except Exception as e:
        return {'styles': "", 'body_content': f"<p>Failed to load standings: {e}</p>"}

def fetch_next_game(team):
    try:
        response = requests.get(team.url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        convert_time_tags(soup)
        
        if 'nhl' in team.url.lower():
            body_text = soup.get_text()
            lines = body_text.split("\n")
            
            found_upcoming = False
            for line in lines:
                line_str = line.strip()
                if "Upcoming Games:" in line_str:
                    found_upcoming = True
                    continue
                if found_upcoming:
                    if line_str.startswith("G") and ("@" in line_str or "v" in line_str):
                        return convert_to_local_time(line_str)
                    if "Full Schedule:" in line_str:
                        break
            
            # Fallback scan for NHL if header wasn't caught
            for line in lines:
                line_str = line.strip()
                if line_str.startswith("G") and any(m in line_str for m in [" 10/", " 11/", " 12/", " 1/", " 2/", " 3/", " 4/"]):
                    return convert_to_local_time(line_str)
                    
        # MLS or others possibly
        else:
            now = datetime.now(ZoneInfo("America/Chicago"))
            future_games = []
            
            for time_tag in soup.find_all("time"):
                dt_str = time_tag.get("datetime")
                if not dt_str:
                    continue
                try:
                    utc_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    game_time_central = utc_dt.astimezone(ZoneInfo("America/Chicago"))
                    
                    if game_time_central > now:
                        parent_line = time_tag.find_parent(["div", "p"])
                        line_text = parent_line.get_text(separator=" ", strip=True) if parent_line else ""
                        cleaned_line = " ".join(line_text.replace("|", " ").split())
                        
                        if cleaned_line:
                            future_games.append((game_time_central, cleaned_line))
                except Exception:
                    continue
                    
            if future_games:
                future_games.sort(key=lambda x: x[0])
                return future_games[0][1]
                
    except Exception:
        pass
    return None

def inject_schedule_theme(soup):
    """Style injection for team schedule pages (centered, wider layout)."""
    style_tag = soup.new_tag("style")
    style_tag.string = """
        body.dark, body {
            background-color: #121212 !important;
            color: #00ff00 !important;
            max-width: 600px !important;
            margin: 15px auto !important;
            padding: 10px !important;
            white-space: pre-wrap !important;
            font-family: Courier, monospace !important;
            font-size: 13px !important;
        }
        div, span, pre, p {
            white-space: pre-wrap !important;
            font-family: Courier, monospace !important;
        }
        .text-fg, a.text-fg, div, span, body {
            color: #00ff00 !important;
        }
        .text-gray {
            color: #88aa88 !important;
        }
        a.nav, .nav {
            color: #9090ff !important;
        }
        .bg-odd {
            background-color: #1a1a1a !important;
        }
    """
    if soup.head:
        soup.head.append(style_tag)
    elif soup.body:
        soup.body.insert(0, style_tag)

def inject_standings_theme(soup):
    """Style injection for standings pages (centered, full width without side-scrolling)."""
    style_tag = soup.new_tag("style")
    style_tag.string = """
        body.dark, body {
            background-color: #121212 !important;
            color: #00ff00 !important;
            max-width: 600px !important;
            margin: 15px auto !important;
            padding: 10px !important;
            font-family: Courier, monospace !important;
        }
        /* Allow natural wrapping so it fits the screen width nicely */
        div, span, pre, p {
            white-space: pre-wrap !important;
            font-family: Courier, monospace !important;
        }
        .text-fg, a.text-fg, div, span, body {
            color: #00ff00 !important;
        }
        .text-gray {
            color: #88aa88 !important;
        }
        a.nav, .nav {
            color: #9090ff !important;
        }
        /* Keep alternating row banding */
        .bg-odd {
            background-color: #1a1a1a !important;
        }
    """
    if soup.head:
        soup.head.append(style_tag)
    elif soup.body:
        soup.body.insert(0, style_tag)