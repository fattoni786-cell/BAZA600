# Деплой БАЗЫ №600

## Главное правило

Пользовательскую базу, логи, `.env` и локальный `config.py` не выкладываем в открытый доступ.

Что должно остаться только на сервере:

- `runtime/baza_users.db`
- `data/baza_users.db`, если используешь старый локальный путь
- `.env`
- `config.py`
- `*.log`
- `logs/`
- `backups/`

Перед публикацией проверь:

```bash
python scripts/pre_release_check.py
```

Если проверка ругается на локальные медиа-пути вроде `C:/Users/...`, сначала загрузи их в Telegram и замени на `file_id`:

```bash
python scripts/upload_local_media_to_telegram.py
```

Скрипт отправит файлы первому админу из `config_baze/admins.py`, сохранит `file_id` в JSON и сделает бэкап старых файлов в `backups/`.

Если когда-нибудь база уже была добавлена в git, убери её из индекса, но не удаляй файл с диска:

```bash
git rm --cached data/baza_users.db
git rm --cached -r logs backups runtime
```

## Переменные окружения

Создай на сервере `.env` по примеру `.env.example`:

```bash
BOT_TOKEN=...
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash-lite
BAZA_DB_PATH=runtime/baza_users.db
```

`BAZA_DB_PATH` отделяет пользовательскую базу от кода. Для продакшена лучше держать её в `runtime/`.

## Быстрый запуск на VPS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p runtime logs backups
python bot.py
```

## Автоперезапуск через systemd

Создай файл:

```bash
sudo nano /etc/systemd/system/baza600.service
```

Пример:

```ini
[Unit]
Description=Baza 600 Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/opt/baza600
ExecStart=/opt/baza600/.venv/bin/python /opt/baza600/bot.py
Restart=always
RestartSec=5
Environment=BOT_TOKEN=put_token_here
Environment=GEMINI_API_KEY=put_gemini_key_here
Environment=GEMINI_MODEL=gemini-2.5-flash-lite
Environment=BAZA_DB_PATH=/opt/baza600/runtime/baza_users.db

[Install]
WantedBy=multi-user.target
```

Включить:

```bash
sudo systemctl daemon-reload
sudo systemctl enable baza600
sudo systemctl start baza600
sudo systemctl status baza600
```

Логи:

```bash
journalctl -u baza600 -f
```

Перезапуск после обновления:

```bash
git pull
source .venv/bin/activate
pip install -r requirements.txt
python scripts/pre_release_check.py
sudo systemctl restart baza600
```

## Если деплоишь не на Linux

Для Windows можно запускать через Task Scheduler или NSSM, но для публичного бота проще и стабильнее VPS на Linux с `systemd`.
