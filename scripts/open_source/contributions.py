import subprocess
import json
import os
from datetime import datetime

repos = ['modelcontextprotocol/go-sdk', 'modelcontextprotocol/inspector', 'google/adk-go', 'mark3labs/mcp-go']
author = 'IAmSurajBobade'

# Configurable data types to fetch
fetch_types = ['PR', 'Issue', 'Release']

script_dir = os.path.dirname(os.path.abspath(__file__))
tmp_file = os.path.join(script_dir, 'tmp_github_data.json')
repo_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
output_md = os.path.join(repo_root, 'docs', 'open_source_contributions.md')

output_data = []
all_contributions = []

def parse_date(date_str):
    if not date_str:
        return datetime.min
    # Handle GitHub ISO 8601 format (e.g. "2026-02-07T07:04:03Z")
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return datetime.min

def get_repo_short(repo):
    return repo.split('/')[-1]

for repo in repos:
    print(f"Fetching for {repo}...")
    repo_short = get_repo_short(repo)

    prs = []
    issues = []
    mentions = []

    # PRs
    if 'PR' in fetch_types:
        try:
            prs_out = subprocess.check_output([
                'gh', 'pr', 'list', '--repo', repo, '--state', 'all', '--author', author,
                '--json', 'title,url,state,mergedAt,createdAt'
            ])
            prs = json.loads(prs_out)
            for pr in prs:
                date_str = pr.get('mergedAt') or pr.get('createdAt')
                all_contributions.append({
                    'type': 'PR',
                    'repo': repo,
                    'repo_short': repo_short,
                    'title': pr.get('title'),
                    'url': pr.get('url'),
                    'state': pr.get('state'),
                    'date_str': date_str,
                    'date': parse_date(date_str)
                })
        except Exception as e:
            print(f"Error fetching PRs for {repo}: {e}")

    # Issues
    if 'Issue' in fetch_types:
        try:
            issues_out = subprocess.check_output([
                'gh', 'issue', 'list', '--repo', repo, '--state', 'all', '--author', author,
                '--json', 'title,url,state,createdAt'
            ])
            issues = json.loads(issues_out)
            for issue in issues:
                date_str = issue.get('createdAt')
                all_contributions.append({
                    'type': 'Issue',
                    'repo': repo,
                    'repo_short': repo_short,
                    'title': issue.get('title'),
                    'url': issue.get('url'),
                    'state': issue.get('state'),
                    'date_str': date_str,
                    'date': parse_date(date_str)
                })
        except Exception as e:
            print(f"Error fetching issues for {repo}: {e}")

    # Releases
    if 'Release' in fetch_types:
        try:
            releases_out = subprocess.check_output([
                'gh', 'api', f'repos/{repo}/releases', '--paginate'
            ])
            releases = json.loads(releases_out)
            for rel in releases:
                body = rel.get('body', '')
                if body and (author in body or author.lower() in body.lower()):
                    date_str = rel.get('published_at') or rel.get('created_at')
                    tag_name = rel.get('tag_name')
                    url = rel.get('html_url')
                    mentions.append({
                        'tagName': tag_name,
                        'name': rel.get('name'),
                        'url': url
                    })
                    all_contributions.append({
                        'type': 'Release',
                        'repo': repo,
                        'repo_short': repo_short,
                        'title': tag_name,
                        'url': url,
                        'state': 'PUBLISHED',
                        'date_str': date_str,
                        'date': parse_date(date_str)
                    })
        except Exception as e:
            print(f"Error fetching releases for {repo}: {e}")

    output_data.append({
        'repo': repo,
        'prs': prs,
        'issues': issues,
        'releases': mentions
    })

# Save intermediate JSON
with open(tmp_file, 'w') as f:
    json.dump(output_data, f, indent=2)

# Sort by date descending
all_contributions.sort(key=lambda x: x['date'], reverse=True)

# Formatting helpers
def type_icon(t):
    # if t == 'PR': return '🔀'
    # if t == 'Issue': return '🐞'
    if t == 'Release': return '🚀'
    return ''

def state_icon(s):
    s_upper = s.upper() if s else ''
    if s_upper == 'MERGED': return 'MERGED'
    if s_upper == 'CLOSED': return 'CLOSED'
    if s_upper == 'OPEN': return 'OPEN'
    if s_upper == 'PUBLISHED': return '✅ PUBLISHED'
    return s_upper

# Generate Markdown
current_time = datetime.now().strftime("%Y/%m/%d %H:%M")
md_lines = [
    "# Open Source Contributions",
    "",
    "A dynamically generated record of my open source Pull Requests, Issues, and Releases.",
    f"*(Last updated: {current_time})*",
    "",
    "| Date | Title | State | Tags |",
    "|---|---|---|---|"
]

for c in all_contributions:
    date_formatted = c['date'].strftime('%Y-%m-%d') if c['date'] != datetime.min else '-'

    # Extract PR/Issue number if present in URL
    title_display = c['title']
    if c['type'] in ['PR', 'Issue']:
        url_parts = c['url'].split('/')
        if url_parts[-1].isdigit():
            num = url_parts[-1]
            if f"(#{num})" not in title_display:
                title_display = f"{title_display} (#{num})"
    elif c['type'] == 'Release':
        title_display = f"{c['repo_short']}/{c['title']}"

    icon = type_icon(c['type'])
    title_link = f"{icon} [{title_display}]({c['url']})" if icon else f"[{title_display}]({c['url']})"
    status_fmt = state_icon(c['state'])
    tags = f"`{c['repo_short']}`, `{c['type'].lower()}`"

    md_lines.append(f"| {date_formatted} | {title_link} | {status_fmt} | {tags} |")

with open(output_md, 'w') as f:
    f.write('\n'.join(md_lines) + '\n')

print(f"Wrote data to {tmp_file}")
print(f"Updated markdown at {output_md}")
print("Done")