# Staging — Timeweb VPS

| | |
|--|--|
| SSH | `timeweb-vps` → `147.45.225.173` |
| Путь на сервере | `/opt/chislyandia` |
| Демо | http://147.45.225.173/game/menu/331113480 |

## Деплой

```powershell
cd C:\Users\Fireboy\Dev\Projects\Chislyandia
.\scripts\deploy-staging.ps1
```

Скрипт: сборка фронта → архив → upload → `deploy/remote-setup.sh`.

## Сервисы на VPS

| Сервис | Проверка |
|--------|----------|
| API | `systemctl status chislyandia-api` |
| Nginx | `systemctl status nginx` |
| Логи API | `journalctl -u chislyandia-api -f` |

Переменные: `/opt/chislyandia/.env` (копируется при деплое, не в git).

## Smoke после деплоя

```text
GET  http://147.45.225.173/api/health
GET  http://147.45.225.173/api/game/worlds/331113480
GET  http://147.45.225.173/api/inventory/331113480
GET  http://147.45.225.173/images/true_lord_calm.jpg
```

Проверить hash бандла в `index.html` (должен меняться после деплоя).

## Ручной чеклист UI

- [ ] Меню, банк, замок, алхимия
- [ ] Карта миров → остров → задачи
- [ ] Босс (обычный)
- [ ] Профиль, инвентарь
- [ ] Тайная комната (если разблокирована)
- [ ] Истинный Владыка: `/game/boss/331113480/true_lord` (нужны 3 хранителя)

## Nginx

Конфиг: `deploy/nginx-chislyandia.conf`

- `/api/` → Flask :5000
- `/assets/` → `frontend/dist`
- `/images/` → `images/` (аватары боссов)
- `/` → SPA `index.html`
