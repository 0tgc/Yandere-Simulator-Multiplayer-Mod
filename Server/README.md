# Yandere Simulator Multiplayer Server

Everything is username-based. No IPs are ever shown to players.

## Setup

```bash
pip install -r requirements.txt
python server.py
```

Port forward **7777 (TCP)** on your router to your PC. That's the only network setup needed — players never deal with IPs.

---

## How It Works

Players register a username once. After that the username IS their identity.

**Hosting a world:**
- Player calls `/host` with their username and a world name
- Their world appears in the lobby list under their username
- Other players join using the host's username — no IP needed

**Joining a world:**
- Player calls `/lobbies` to see open worlds (shows host username + world name)
- Player connects to `ws://server/join/{host_username}/{your_username}`
- Server relays all data between players — nobody's IP is ever exposed

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Claim a username (first launch only) |
| GET | `/check/{username}` | Is this username available? |
| POST | `/login` | Verify saved username on startup |
| GET | `/lobbies` | List all open worlds (usernames only) |
| POST | `/host` | Start hosting a world |
| DELETE | `/host/{username}` | Close your world |
| WS | `/join/{host}/{you}` | Join a world by host's username |

## Username Rules
- 4–16 characters
- Letters, numbers, underscores only
- Must be unique, permanent, no password
