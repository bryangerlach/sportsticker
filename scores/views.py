from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from .models import Team
from .scraper import fetch_today_games, fetch_nhl_team, fetch_mls_team, fetch_nhl_standings, fetch_mls_standings, fetch_next_game

@login_required(login_url='/admin/login/')
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
        today_games = fetch_today_games(team)
        today_game = today_games[0] if today_games else None
        
        # Fetch the next upcoming game if no game is today
        next_game = None
        if not today_game:
            next_game = fetch_next_game(team)

        team_dashboards.append({
            'team': team,
            'today_game': today_game,
            'next_game': next_game,
        })

    return render(request, 'sports/dashboard.html', {
        'teams': team_dashboards,
    })

@login_required(login_url='/admin/login/')
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

@login_required(login_url='/admin/login/')
def standings_view(request, league):
    if league == 'mls':
        url = "https://plaintextsports.com/mls/2026/standings"
        data = fetch_mls_standings(url)
    else:
        url = "https://plaintextsports.com/nhl/2026-2027/standings"
        data = fetch_nhl_standings(url)

    return render(request, 'sports/standings.html', {
        'league': league.upper(),
        'styles': data['styles'],
        'body_content': data['body_content']
    })