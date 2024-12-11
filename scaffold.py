import os
import yaml

config_file = os.getenv('CONFIG_FILE')

with open(config_file, 'r') as file:
    config_data = yaml.load(file, Loader=yaml.FullLoader)
    print(config_data)

for app in config_data['apps']:
    if app['appId'] == 'credit-bureau':
        app['appPort'] = 5001
        app['workDir'] = './services/credit-bureau'
        app['command'] = ['uvicorn', 'main:app', '--port', '5001']
    if app['appId'] == 'loan-broker':
        app['workDir'] = './services/loan-broker'
        app['command'] = ['uvicorn', 'main:app','--port', '5006']
    if app['appId'] == 'quote-aggregator':
        app['appPort'] = 5002
        app['workDir'] = './services/quote-aggregator'
        app['command'] = ['uvicorn', 'main:app', '--port', '5002']
    if app['appId'] == 'riverstone-bank':
        app['appPort'] = 5003
        app['workDir'] = './services/riverstone-bank'
        app['command'] = ['uvicorn', 'main:app', '--port', '5003']
    if app['appId'] == 'titanium-trust':
        app['appPort'] = 5004
        app['workDir'] = './services/titanium-trust'
        app['command'] = ['uvicorn', 'main:app','--port', '5004']
    if app['appId'] == 'union-vault':
        app['appPort'] = 5005
        app['workDir'] = './services/union-vault'
        app['command'] = ['uvicorn', 'main:app', '--port', '5005']

updated_data = {
    'project': config_data['project'],
    'apps': config_data['apps'],
    'appLogDestination': config_data.get('appLogDestination', '')
}

with open(config_file, 'w') as file:
    yaml.safe_dump(updated_data, file, default_flow_style=False, sort_keys=False)

print("Dev config file has been updated")