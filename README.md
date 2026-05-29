# YanSim Multiplayer

A MelonLoader mod that adds real-time multiplayer to Yandere Simulator.

## How it works

One player hosts a world. Other players join it. Clients see NPCs following their daily schedules (walking to class, sitting at desks, patrolling hallways) using local schedule data, while the host's game state syncs items, blood, corpses, and player positions in real time.

- Host plays the game normally — NPCs react, routines run, rival events trigger
- Clients observe the same world with NPCs moving autonomously via their schedule data
- PvP kills are supported (host can be killed by a client)
- Player appearances (hair, uniform, colors) are synced

## Requirements

- Yandere Simulator (latest version)
- [MelonLoader](https://github.com/LavaGang/MelonLoader) v0.7+ (x64)

## Installation

1. Install MelonLoader into your Yandere Simulator folder
2. Download `YanSimMultiplayer.dll` from [Releases](https://github.com/0tgc/Yandere-Simulator-Multiplayer-Mod/releases/latest)
3. Copy the DLL into `{Game Folder}/Mods/`
4. Launch the game — a username prompt appears on the main menu

## Usage

1. Enter a username and claim it (one-time setup)
2. Click **Host a World** or **Browse Worlds** to find one to join
3. If hosting: the host loads into the school and plays normally
4. If joining: Senpai customization screen appears, then you enter the school as a client

### Controls

| Key | Action |
|---|---|
| F | PvP kill request (when holding a weapon near another player) |
| R | Respawn after death |
| Z | Open chat |

## Building from source

```
dotnet build -c Release
```

Requires .NET Framework 4.7.2 SDK and the game's `Managed` assemblies.

## Server

The relay server is a Python FastAPI + WebSocket application in `Server/Server.py`.

## License

MIT
