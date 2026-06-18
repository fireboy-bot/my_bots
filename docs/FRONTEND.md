# Frontend (`frontend/src`)

React + Vite клиент web-версии Chislyandia.

## Главный роутинг

Файл: `frontend/src/App.jsx`

Текущие роуты:

- `/game/menu/:userId`
- `/game/worlds/:userId`
- `/game/task/:userId/:worldId`
- `/game/boss/:userId/:bossId`
- `/game/castle/:userId`
- `/game/bank/:userId`
- `/game/shop/:userId`
- `/game/shop/artifacts/:userId`
- `/game/shop/alchemy/:userId`
- `/game/profile/:userId`
- `/game/secret-room/:userId`
- `/game/inventory/:userId`

Спец-кейс: если `bossId === "true_lord"`, роут открывает `TrueLordScreen`.

## Ключевые экраны

- `MenuScreen` — главный вход в web-режим.
- `WorldsScreen` — карта островов, пост-гейм миров и боссов.
- `TaskScreen` — основной забег задач.
- `BossScreen` — обычные боссы (островные/финальный/хранители).
- `TrueLordScreen` — отдельный эпический бой Истинного Владыки.
- `ProfileScreen` — профиль игрока.
- `InventoryScreen` — инвентарь (расходники/трофеи/артефакты/секретные).
- `SecretRoomScreen` — тайная комната.
- `CastleScreen`, `BankScreen`, `ShopScreen`, `ArtifactsScreen`, `AlchemyScreen` — экономика.

## API-адаптер

Файл: `frontend/src/adapters/botAdapter.js`

Frontend работает только через адаптер.
Новые запросы добавляются сначала сюда, потом используются экранами.

Ключевые методы:

- `getWorlds`, `startLevel`
- `getBosses`, `startBoss`, `exitBoss`
- `checkAnswer`
- `trueLordHint`
- `getPlayerProfile`
- `getInventory`
- `getSecretRoom`, `exploreSecretRoom`, `answerSecretPuzzle`

## UI-события

- `GameEventOverlay` — level up, победа острова, победа босса, победа финального, абсолютная победа.
- `FloatingNav` — единая навигация назад/меню.

## Правило обновления доки

Если добавлен новый экран/роут:

1. обновить `docs/FRONTEND.md`,
2. если есть новые API-запросы — обновить `docs/WEB_API_SERVER.md`.
