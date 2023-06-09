## 📰 Unofficial Emias Polling Telegram Bot
> Unofficial bot that helps to automate the process of checking available appointments to doctors.
Instead of opening website every 15 minutes in the hope that an appointment with a doctor was freed, just set the reminder and bot will ping you.

### ✨ Features
- Setting polling interval
- Showing available specialists info and choosing one from them to remind
- Multiple users support using async requests
- Simple to add custom strings resources
- Roles system
- Auto-appointment


### 💾 Commands
- `/start`
- `/help`
- `/notify`
- [Admin] `/admin add`
- [Admin] `/admin remove`
- [Admin] `/whitelist add`
- [Admin] `/whitelist remove`

### 📦 Stack
- Python
- [Telebot API](https://pypi.org/project/pyTelegramBotAPI/)
- json
- requests
- asyncio
- logging

### 🚀 Setup
- Clone repository
- Add `config.json` with bot token: 
```json
{
    "token": "YOUR_TOKEN",
    "strings_path": "YOUR_PATH",
    "logs_path": "YOUR_PATH"
}
```
- Add yourself to admins/whitelist list and start `main.py`

### ✅ TODO
- [ ] Wrap code with try & catch blocks
- [ ] Make caching
- [ ] Make `/stop` command
- [ ] Choosing a day and time of auto-appointment
