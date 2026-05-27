<div align="center">

# 🎀 YanSim Multiplayer

**A free-roam multiplayer mod for Yandere Simulator**

*Built with MelonLoader · Username-based · No IPs ever exposed*

---

![Status](https://img.shields.io/badge/status-in%20development-red?style=flat-square)
![MelonLoader](https://img.shields.io/badge/MelonLoader-0.6.x-magenta?style=flat-square)
![Unity](https://img.shields.io/badge/Unity-IL2CPP-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-pink?style=flat-square)

</div>

---

## 📖 What Is This?

YanSim Multiplayer is a MelonLoader mod that adds free-roam online multiplayer to Yandere Simulator. Players can host or join worlds and run around the school together in real time.

**Key design goals:**
- 🙈 **No IPs.** Everything is done through usernames. Players never see or type an IP address.
- 🎀 **No accounts.** Just pick a username once. No passwords, no email — it's yours permanently.
- 🌐 **Server-relayed.** All game data routes through a central server. No peer-to-peer, no port forwarding for players.

---

## ✨ Features

- **Username system** — claim a unique username on first launch (4–16 chars). Saved locally, auto-login from then on.
- **World browser** — see all open worlds with host name and player count. Click Join. That's it.
- **Host a world** — name your world, load into the school, done. Others can join from the browser.
- **Real-time sync** — positions and animations synced at 20Hz through the server relay.
- **Yandere Sim themed UI** — dark crimson IMGUI overlay that fits the game's aesthetic.
- **Auto-cleanup** — if the host disconnects, the world closes and all players are notified.

---

## 🖼 How It Looks

```
┌─────────────────────────────────────────────┐
│          🎀  Multiplayer                     │
│  Logged in as  FantasySpark                  │
│                         [Host a World] [↺]   │
│─────────────────────────────────────────────│
│  Yandere Hangout                             │
│  Hosted by  FantasySpark  •  3/8 players    │
│                                    [ Join ]  │
│─────────────────────────────────────────────│
│  Club Chaos                                  │
│  Hosted by  SakuraChan   •  1/8 players     │
│                                    [ Join ]  │
└─────────────────────────────────────────────┘
```

---

## 🗂 Project Structure

```
YanSimMultiplayer/
├── YanSimMultiplayer.csproj
└── src/
    ├── ModMain.cs                    # MelonLoader entry point & scene handling
    ├── Config.cs                     # Saves username locally between sessions
    ├── Network/
    │   ├── ServerAPI.cs              # HTTP: register, login, lobbies, host
    │   └── RelayClient.cs            # WebSocket: real-time position sync
    ├── UI/
    │   ├── UIManager.cs              # Themed IMGUI skin
    │   ├── ProfileSetupScreen.cs     # First-launch username creation screen
    │   └── LobbyBrowserScreen.cs     # World browser, host & join UI
    ├── Multiplayer/
    │   ├── SyncData.cs               # Network message types
    │   ├── PlayerPuppet.cs           # Remote player visual (capsule + name label)
    │   └── PlayerManager.cs          # Spawns puppets, broadcasts our position
    └── Patches/
        └── MainMenuPatch.cs          # Injects the Multiplayer button into the main menu
```

---

## ⚙️ Setup

### Prerequisites

- [Yandere Simulator](https://yanderesimulator.com/) installed
- ![MelonLoader 0.6.x](https://github.com/LavaGang/MelonLoader/releases/download/v0.7.3/MelonLoader.Installer.exe) installed into the game and run once
- [.NET 6 SDK](https://dotnet.microsoft.com/) to build the mod

> **Note:** This mod requires a running server to connect to.
> The server is hosted separately — ask the mod's server operator for the address.

---

### 1 — Configure

Open `src/Config.cs` and fill in the server address you were given:

```csharp
public const string SERVER_URL = "http://SERVER_ADDRESS:7777";
public const string WS_URL     = "ws://SERVER_ADDRESS:7777";
```

Open `YanSimMultiplayer.csproj` and set your Yandere Simulator install path:

```xml
<GAME_PATH>C:\PATH\TO\Yandere Simulator</GAME_PATH>
```

---

### 2 — Build

```bash
dotnet build
```

The compiled DLL is automatically copied to the game's `Mods/` folder.

---

### 3 — First Launch

Open Yandere Simulator. A username setup screen will appear:

1. Type a username *(4–16 chars · letters, numbers, underscores)*
2. Availability is checked live as you type
3. Hit **Claim Username** — it's yours permanently, no password needed
4. Every launch after that you're logged in automatically

---

### 4 — Playing

- Click **Multiplayer** on the main menu
- **To host:** click *Host a World* → name your world → *Start Hosting* → load into school
- **To join:** pick any world from the list → *Join* → load into school
- Other players appear as pink capsules with floating name labels above them

---

## 🔧 Troubleshooting

<details>
<summary><b>The Multiplayer button doesn't appear in the main menu</b></summary>

The mod clones an existing menu button to create the Multiplayer button. If it doesn't show up, the button search might not match the game's actual button labels.

Open `src/Patches/MainMenuPatch.cs` and update this line to include a label one of the game's buttons actually has:

```csharp
if (label.Contains("start") || label.Contains("new game") || label.Contains("play"))
```

</details>

<details>
<summary><b>Players aren't visible / puppets don't appear</b></summary>

The mod finds the local player by searching for a GameObject named `"Yandere"`. If the game uses a different name, update this constant in `src/Multiplayer/PlayerManager.cs`:

```csharp
private const string PLAYER_GO_NAME = "Yandere";
```

To find the real name, temporarily add this to `OnSceneWasLoaded` in `ModMain.cs`:

```csharp
foreach (var go in UnityEngine.Object.FindObjectsOfType<UnityEngine.GameObject>())
    LoggerInstance.Msg(go.name);
```

Then check the MelonLoader console for the player object's name.

</details>

<details>
<summary><b>Multiplayer doesn't activate when loading into school</b></summary>

The mod detects the school scene by its name. Add this temporary log to find the real scene name:

```csharp
public override void OnSceneWasLoaded(int buildIndex, string sceneName)
{
    LoggerInstance.Msg($"Scene: {sceneName}");
    // ...
}
```

Then update the scene name checks in `ModMain.cs` to match.

</details>

<details>
<summary><b>Can't connect / username screen never finishes</b></summary>

The server address in `Config.cs` may be wrong or the server may be offline. Double-check the address with whoever is hosting the server.

</details>

---

## 🤝 Contributing

Pull requests are welcome! If you've found the real internal names for:
- The player GameObject (`"Yandere"`?)
- The school scene name (`"School"`?)
- The main menu scene name (`"MainMenu"`?)

Please open a PR or issue to set them as defaults — it'll save everyone the troubleshooting step.

---

## ⚠️ Disclaimer

This is a fan-made mod and is not affiliated with YandereDev or the official Yandere Simulator project. Use at your own risk.

---

<div align="center">

Made with 🎀 by the community

</div>
