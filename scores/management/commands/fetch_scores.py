from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from scores.models import Team, GameScore

class Command(BaseCommand):
    help = 'Precise scraper for Plain Text Sports team pages'

    def handle(self, *args, **options):
        teams = Team.objects.all()
        if not teams.exists():
            self.stdout.write(self.style.WARNING("No teams found in database."))
            return

        headers = {"User-Agent": "DjangoSportsApp/1.0"}
        
        # Central Time today string format (e.g., "10/7" or "10/8")
        central_now = datetime.now(ZoneInfo("America/Chicago"))
        today_str = central_now.strftime("%m/%d").lstrip("0").replace("/0", "/")

        for team in teams:
            try:
                response = requests.get(team.url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Clear old records for this team
                GameScore.objects.filter(team=team).delete()

                # Every game row on Plain Text Sports team pages features a .game-nav anchor
                game_anchors = soup.select("a.game-nav")
                
                for a_tag in game_anchors:
                    game_path = a_tag['href']
                    
                    # Construct full link (handles both full paths and anchor links like /mls/2026-09-26/#dal-lafc)
                    if game_path.startswith("http"):
                        game_url = game_path
                    else:
                        game_url = "https://plaintextsports.com" + game_path

                    # Isolate the exact parent line/container text where this game lives
                    row_container = a_tag.find_parent(["div", "b", "span"]) or a_tag.parent
                    row_text = row_container.get_text(" ", strip=True) if row_container else a_tag.get_text(strip=True)
                    
                    # Clean up multiple whitespaces or line breaks into a clean single string
                    cleaned_summary = " ".join(row_text.split())

                    # Determine if this specific game line matches today's date
                    status = "Today" if today_str in cleaned_summary else "Upcoming"

                    GameScore.objects.create(
                        team=team,
                        team_name=team.name,
                        opponent=game_url,
                        score_summary=cleaned_summary,
                        game_status=status
                    )

                self.stdout.write(self.style.SUCCESS(f"Successfully updated schedule for {team.name}"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to fetch {team.name}: {e}"))