# YanSim Multiplayer

A MelonLoader mod that adds real-time multiplayer to Yandere Simulator.

## Still under development

One player hosts a world. Other players join it. The host's game state (NPCs, items, blood, corpses) is broadcast to all connected clients in real time. Clients see the exact same world — NPCs walk around, weapons appear/disappear, blood pools form, and dead bodies ragdoll — matching the host frame-by-frame.

- Host interacts with the world normally (pick up items, kill NPCs, etc.)
- Clients are spectators who can observe and chat
- PvP kills are supported (host can be killed by a client)

## Requirements

- Yandere Simulator (latest version)
- [MelonLoader](https://github.com/LavaGang/MelonLoader) v0.6+ (x64)

## Installation

1. Install MelonLoader into your Yandere Simulator folder
2. Download `YanSimMultiplayer.dll` from [Releases](https://github.com/0tgc/Yandere-Simulator-Multiplayer-Mod/releases/latest)
3. Copy the DLL into `{Game Folder}/Mods/`
4. Launch the game — a username prompt appears on the main menu

## Usage

1. Enter a username and claim it (one-time setup)
2. Click **Host a World** or **Browse Worlds** to find one to join
3. If hosting: the host loads into the school and plays normally
4. If joining: you connect as a player and see the host's world

### Controls

| Key | Action |
|---|---|
| F | PvP kill request (when holding a weapon near another player) |
| R | Respawn after death |
| T | Open chat |
| Tab | Toggle cursor (release from gameplay lock) |

## Building from source

Open `YanSimMultiplayer.csproj` in Visual Studio or run:

```
dotnet build -c Release
```

Requires .NET Framework 4.7.2 SDK and the game's `Managed` assemblies referenced.

## Server

The relay server is a Python FastAPI + WebSocket application in `Server/Server.py`. See its README for setup.

## License

MIT
