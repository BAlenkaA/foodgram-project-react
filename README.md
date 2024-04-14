# praktikum_new_diplom
# Foodgramm
## Дипломный проект курса Python-разработчик на Яндекс Практикум.

![Main Foodgram Workflow](https://github.com/BAlenkaA/foodgram-project-react/actions/workflows/main.yml/badge.svg?event=push)

В данном проекте происходит развертывание приложения на удаленном сервере с использованием Docker.
Foodgramm — сайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и
подписываться на публикации других авторов. Пользователям сайта также будет доступен сервис «Список покупок».
Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
## Для данного проекта использовались следующие технологии:
- Python 3.11
- Django 4.2.11
- Docker

## Для запуска проекта необходимо:
1. Скачать проект с репозитория на платформе GitHub
2. Развернуть виртуальное окружение, рекомендуемая версия python: python3 -m venv venv (python для ОС Windows, MacOS)
3. Установить зависимости из файла requirements.txt: pip install -r requirements.txt
4. Создать файл main.yml и описать в нем workflow.
5. Установить Docker и Docker Compose для Linux.
6. Подготовить файлы docker-compose.yml docker-compose.production.yml
7. Создать аккаунт в dokerhub https://hub.docker.com/, если его нет.
```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin
```
8. Создать папку проекта на удаленном сервере.
9. Получить и настроить SSL-сертификат.

## Как заполнить env:

- Локально в корне проекта создайте файл .env, в нем пропишите следующие константы:
  1. POSTGRES_USER
  2. POSTGRES_PASSWORD
  3. POSTGRES_DB
  4. DB_HOST
  5. DB_PORT
  6. SECRET_KEY
  7. DEBUG
  8. ALLOWED_HOSTS=127.0.0.1,localhost,ваш_домен
- В вашем гитхабе в проекте настройте Secret. Там необходимо прописать следующие :
  1. DOCKER_PASSWORD
  2. DOCKER_USERNAME
  3. HOST
  4. SSH_KEY
  5. TELEGRAM_TO
  6. TELEGRAM_TOKEN
  7. USER
## Контакты
Студент-разработчик Белинцева Алена alena@belintsev.ru
