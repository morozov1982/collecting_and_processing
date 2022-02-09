import requests
import json
from pprint import pprint

URL = 'https://api.github.com/users/morozov1982/repos'

response = requests.get(URL)
data = response.json()
data_str = json.dumps(data)

with open('full_data.json', 'w', encoding='utf-8') as f:
    f.write(data_str)

sample_data = []

for repo in data:
    current_data = {
        'name': repo['name'],
        'full_name': repo['full_name'],
        'html_url': repo['html_url'],
        'git_url': repo['git_url'],
        'ssh_url': repo['ssh_url'],
        'clone_url': repo['clone_url'],
    }
    # pprint(current_data)
    sample_data.append(current_data)

sample_data_str = json.dumps(sample_data)

with open('sample_data.json', 'w', encoding='utf-8') as f:
    f.write(sample_data_str)
