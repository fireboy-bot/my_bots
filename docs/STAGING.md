# Staging — Timeweb VPS

**Сервер:** `timeweb-vps` → `147.45.225.173` (SSH alias в `~/.ssh/config`)  
**Путь:** `/opt/chislyandia`  
**URL:** http://147.45.225.173/game/menu/331113480

## Деплой с Windows

```powershell
cd C:\Users\Fireboy\Dev\Projects\Chislyandia
powershell -ExecutionPolicy Bypass -File .\scripts\deploy-staging.ps1
```

## Ручной прогон после деплоя

- [ ] http://147.45.225.173/api/health → `ok`
- [ ] Меню → задачи → +/- баланс
- [ ] Банк вклад/снятие

## Сервисы на VPS

| Сервис | Команда |
|--------|---------|
| API | `systemctl status chislyandia-api` |
| Nginx | `systemctl status nginx` |
| Логи API | `journalctl -u chislyandia-api -f` |

## Переменные

На сервере `/opt/chislyandia/.env` — копируется с локальной машины при деплое (не в git).
