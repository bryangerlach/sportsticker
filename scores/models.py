from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    url = models.URLField()
    league = models.CharField(max_length=10, default='nhl')
    short_name = models.CharField(max_length=10, default='DAL') # <--- Add this (e.g., DAL)

    def __str__(self):
        return f"{self.name} ({self.short_name})"

class GameScore(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='games', null=True)
    team_name = models.CharField(max_length=100)
    opponent = models.CharField(max_length=100)
    score_summary = models.TextField()
    game_status = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.team_name} - {self.game_status}"