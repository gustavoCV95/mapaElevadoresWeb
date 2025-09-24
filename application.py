# application.py - Ponto de entrada para Elastic Beanstalk
from app import app

# Elastic Beanstalk procura por 'application'
application = app

if __name__ == "__main__":
    application.run()