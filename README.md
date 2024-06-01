1. Клонируешь репозиторий к себе
2. Создаешь окружение и накатываешь зависимости:
   ```bash
   python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt 
   ```
3. В корне проекта удаляешь папку tiktok-signature (если есть)
    ```bash
    rm -rf tiktok-signature
    ```
4. Клонируешь к себе сигнатуру с репозитория (из корня проекта)
   ```bash
   git clone https://github.com/carcabot/tiktok-signature.git
   ```
5. В файлах tiktok-signature/package.json и package-lock.json проверить зависимости:
   ```sh
       "playwright": "1.10.0",
       "playwright-chromium": "1.10.0"
   ```
6. Создаешь файл с переменными окружения
   ```bash
   cp .env.sample .env
   cp .env.sample dev.env
   ```
   .env нужно поправить
   ```env
   TT_SIGNATURE_URL=http://127.0.0.1:8080/signature
   CELERY_BROKER=redis://127.0.0.1:6379/0
   CELERY_BACKEND=redis://127.0.0.1:6379/0
   ```
   dev.env должен сразу выглядеть вот так
   ```env
   TT_SIGNATURE_URL=http://signature:8080/signature
   CELERY_BROKER_URL=redis://redis:6379/0
   FLOWER_PORT=8888
   CELERY_BROKER=redis://redis:6379/0
   CELERY_BACKEND=redis://redis:6379/0
   ```
   NOTE: в идеале нужно ```TIKTOK_MS_TOKEN``` добавить. Достается из куков при посещении тиктока. <br>
   Открываешь куки, ждешь полной загрузки страницы (токен изменится несколько раз).<br>
   Лучше добавить сразу несколько (разделитель - ;). ```TIKTOK_MS_TOKEN=msToken1;msToken2;msToken3```.<br>
   Нужны для работы библиотеки TikTokApi
7. Получаешь токен нового бота у <a href="https://t.me/BotFather">bot father</a> и закидываешь его в .env и dev.env ```BOT_TOKEN```
8. Для локально разработки запускаешь только redis, celery и tiktok-signature
   ```bash 
   docker compose -f docker-compose-dev.yml up --build 
   ```
9. Миграции (накатываются в SQLite)
   ```bash
   ./maange.py migrate 
   ```
10. Суперюзер
   ```bash
   ./manage.py createsuperuser 
   ```
11. Поправить исходный код библиотеки TikTokApi
   ```bash
   python3 post_install.py
   ```
12. Запускаешь бота
   ```bash
   ./manage.py run_bot
   ```
13. Запускаешь админку
   ```bash
   ./manage.py runserver
   ```

# линтеры
1. Установить хуки на коммит:
   ```pre-commit install```
2. Запустить вне коммита: 
   ```pre-commit run -a```

# NOTES
- Пайплайны (.github/workflow) на коммит в мастер, так что поаккуратнее, защиты никакой нет.
- Работать лучше в смежной ветке от мастера и кидать мне PRы.
- C .env файлами не очень хорошо все, но я честно не помню, чем я руководствовался, когда подобные вещи делал.
По факту:
dev.env - файл, с которого считывают переменные контейнеры (у них свои пути, т.к. они в рамках своего нетворка работают)
.env - файл, с которого считывают переменные бот и админка.
Я поправлю их вместе с докерфайлами позже.
