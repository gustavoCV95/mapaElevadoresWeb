# application.py
import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path para garantir que 'app' seja encontrado
# Isso é uma precaução extra, embora o PYTHONPATH no .ebextensions já deva cuidar disso.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.factory import create_app

# O Elastic Beanstalk espera um objeto "application" na raiz do módulo
application = create_app()

# Opcional: Se você ainda usa app_new.py para execução local, pode deixá-lo.
# Mas para o deploy no EB, 'application.py' é o que importa.