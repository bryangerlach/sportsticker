from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from .models import Team
from .scraper import (
    fetch_today_games, 
    fetch_nhl_team, fetch_mls_team
)

def dashboard_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        url = request.POST.get('url')
        league = request.POST.get('league', 'nhl')
        short_name = request.POST.get('short_name', 'DAL').upper()
        
        if name and url:
            slug = slugify(name)
            Team.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'url': url, 'league': league, 'short_name': short_name}
            )
            return redirect('scores:dashboard')

    teams = Team.objects.all()
    team_dashboards = []
    
    for team in teams:
        # Pass the team object so the scraper can check its URL and short name
        today_games = fetch_today_games(team)
        today_game = today_games[0] if today_games else None
        
        if team.league == 'mls':
            team_data = fetch_mls_team(team.url)
        else:
            team_data = fetch_nhl_team(team.url)

        team_dashboards.append({
            'team': team,
            'today_game': today_game,
            'team_data': team_data
        })

    return render(request, 'sports/dashboard.html', {
        'teams': team_dashboards,
    })

def team_detail_view(request, team_slug):
    team = get_object_or_404(Team, slug=team_slug)
    if team.league == 'mls':
        data = fetch_mls_team(team.url)
    else:
        data = fetch_nhl_team(team.url)

    return render(request, 'sports/team_detail.html', {
        'team': team,
        'styles': data['styles'],
        'body_content': data['body_content']
    })

def standings_view(request, league):
    if league == 'mls':
        url = "https://plaintextsports.com/mls/2026/standings"
        from .scraper import fetch_mls_standings
        data = fetch_mls_standings(url)
    else:
        url = "https://plaintextsports.com/nhl/2026-2027/standings"
        from .scraper import fetch_nhl_standings
        data = fetch_nhl_standings(url)

    return render(request, 'sports/standings.html', {
        'league': league.upper(),
        'styles': data['styles'],
        'body_content': data['body_content']
    })