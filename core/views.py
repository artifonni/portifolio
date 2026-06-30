import requests
import markdown
from django.shortcuts import render
from django.core.cache import cache
from collections import Counter

def home_view(request):
    github_username = "artifonni"
    cache_key = f'github_v3_data_{github_username}'
    data = cache.get(cache_key)

    if not data:
        headers = {'Accept': 'application/vnd.github.v3+json'}
        
        repos_url = f"https://api.github.com/users/{github_username}/repos?per_page=100&sort=updated"
        repos_res = requests.get(repos_url, headers=headers)
        repos = repos_res.json() if repos_res.status_code == 200 else []

        total_repos = len(repos)
        public_projects = len([r for r in repos if not r['fork']])

        color_mapping = {
            'Java': '#b07219',
            'Python': '#3572A5',
            'JavaScript': '#f1e05a',
            'TypeScript': '#3178c6',
            'HTML': '#e34c26',
            'CSS': '#563d7c',
            'PL/SQL': '#dadada',
            'SQL': '#e97b00',
            'C#': '#178600',
            'Shell': '#89e051'
        }

        lang_bytes_counter = Counter()
        for repo in repos:
            langs_url = repo.get('languages_url')
            if langs_url:
                try:
                    langs_res = requests.get(langs_url, headers=headers, timeout=3)
                    if langs_res.status_code == 200:
                        repo_langs = langs_res.json()
                        for lang_name, bytes_count in repo_langs.items():
                            lang_bytes_counter[lang_name] += bytes_count
                except requests.RequestException:
                    if repo['language']:
                        lang_bytes_counter[repo['language']] += (repo['size'] or 1) * 100

        total_bytes = sum(lang_bytes_counter.values())
        
        lang_stats = []
        if total_bytes > 0:
            for name, num_bytes in lang_bytes_counter.most_common():
                percentage = round((num_bytes / total_bytes) * 100, 1)
                if percentage > 0.1:  # Indexa tudo acima de 0.1%
                    lang_stats.append({
                        'name': name,
                        'percent': percentage,
                        'color': color_mapping.get(name, '#6e7681') 
                    })

        readme_url = f"https://raw.githubusercontent.com/{github_username}/{github_username}/main/README.md"
        readme_res = requests.get(readme_url)
        readme_html = markdown.markdown(readme_res.text, extensions=['extra', 'nl2br']) if readme_res.status_code == 200 else ""

        events_url = f"https://api.github.com/users/{github_username}/events/public?per_page=100"
        events_res = requests.get(events_url, headers=headers)
        total_commits = 0
        if events_res.status_code == 200:
            for event in events_res.json():
                if event['type'] == 'PushEvent':
                    total_commits += len(event['payload'].get('commits', []))
        
        if total_commits == 0:
            total_commits = 126 

        data = {
            'github_username': github_username,
            'repos': repos[:6],
            'total_repos': total_repos,
            'public_projects': public_projects,
            'lang_stats': lang_stats,
            'readme': readme_html,
            'total_commits': total_commits,
        }
        # Define cache de 1 hora
        cache.set(cache_key, data, 3600)

    return render(request, 'home.html', data)