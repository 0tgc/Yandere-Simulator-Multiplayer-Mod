import asyncio
import json
import re
import sqlite3
import threading
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# ─────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 7777
DB_PATH = "yansim.db"

console = Console()

# ─────────────────────────────────────────────
#  In-memory state
#
#  lobbies[host_username] = {
#    "world_name": str,
#    "host":       str,          ← same as key
#    "max_players": int,
#    "players":    [username, ...],
#    "created_at": str,
#  }
#
#  connections[host_username][player_username] = WebSocket
# ─────────────────────────────────────────────
lobbies:     dict[str, dict]              = {}
connections: dict[str, dict[str, WebSocket]] = {}

server_logs: list[str] = []
MAX_LOGS = 14


def log(msg: str, style: str = "white"):
    ts = datetime.now().strftime("%H:%M:%S")
    server_logs.append(f"[dim]{ts}[/dim] [{style}]{msg}[/{style}]")
    if len(server_logs) > MAX_LOGS:
        server_logs.pop(0)


# ─────────────────────────────────────────────
#  Database
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username   TEXT PRIMARY KEY,
            created_at TEXT,
            last_seen  TEXT
        )
    """)
    conn.commit()
    conn.close()


def db_exists(username: str) -> bool:
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return row is not None


def db_register(username: str):
    now = datetime.now().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO users (username, created_at, last_seen) VALUES (?, ?, ?)",
        (username, now, now),
    )
    conn.commit()
    conn.close()


def db_touch(username: str):
    conn = get_db()
    conn.execute(
        "UPDATE users SET last_seen = ? WHERE username = ?",
        (datetime.now().isoformat(), username),
    )
    conn.commit()
    conn.close()


def db_user_count() -> int:
    conn = get_db()
    n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return n


# ─────────────────────────────────────────────
#  Validation
# ─────────────────────────────────────────────
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")


def validate_username(username: str) -> str:
    username = username.strip()
    if len(username) < 4:
        raise HTTPException(400, "Username must be at least 4 characters.")
    if len(username) > 16:
        raise HTTPException(400, "Username must be at most 16 characters.")
    if not USERNAME_RE.match(username):
        raise HTTPException(
            400, "Only letters, numbers, and underscores are allowed."
        )
    return username


def require_known(username: str):
    if not db_exists(username):
        raise HTTPException(403, f'Username "{username}" is not registered.')


# ─────────────────────────────────────────────
#  App
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log("Server started — port 7777", "green")
    yield
    log("Server stopped", "yellow")


app = FastAPI(title="YanSim Multiplayer Server", lifespan=lifespan)


# ── Request models ───────────────────────────
class RegisterBody(BaseModel):
    username: str

class LoginBody(BaseModel):
    username: str

class HostBody(BaseModel):
    host_username: str
    world_name: str
    max_players: int = 8


# ─────────────────────────────────────────────
#  Auth  (username only, no passwords)
# ─────────────────────────────────────────────
@app.post("/register")
def register(body: RegisterBody):
    """
    First-time setup. Player picks a username.
    Saved permanently — they never have to pick again.
    """
    username = validate_username(body.username)
    if db_exists(username):
        log(f'Taken username attempt: "{username}"', "red")
        raise HTTPException(409, "That username is already taken. Try another one.")
    db_register(username)
    log(f'Registered "{username}"', "cyan")
    return {"success": True, "username": username}


@app.get("/check/{username}")
def check(username: str):
    """Live availability check while the player is typing."""
    try:
        username = validate_username(username)
    except HTTPException as e:
        return {"available": False, "valid": False, "reason": e.detail}
    return {"available": not db_exists(username), "valid": True}


@app.post("/login")
def login(body: LoginBody):
    """
    Called on every launch after the first.
    Client sends the saved username; server confirms it still exists.
    """
    username = validate_username(body.username)
    require_known(username)
    db_touch(username)
    log(f'"{username}" connected', "green")
    return {"success": True, "username": username}


# ─────────────────────────────────────────────
#  Lobbies  (identified by host username only)
# ─────────────────────────────────────────────
@app.get("/lobbies")
def list_lobbies():
    """
    Returns every open world.
    Response contains only usernames and world info — zero IPs.
    """
    return {
        "worlds": [
            {
                "host":        data["host"],
                "world_name":  data["world_name"],
                "players":     data["players"],          # list of usernames
                "player_count": len(data["players"]),
                "max_players": data["max_players"],
            }
            for data in lobbies.values()
        ]
    }


@app.post("/host")
def host_world(body: HostBody):
    """
    Register a new hosted world under the host's username.
    Only one world per username at a time.
    """
    username = validate_username(body.host_username)
    require_known(username)

    if username in lobbies:
        raise HTTPException(409, "You are already hosting a world. Close it first.")

    lobbies[username] = {
        "host":        username,
        "world_name":  body.world_name.strip()[:32] or f"{username}'s World",
        "max_players": max(2, min(body.max_players, 16)),
        "players":     [],
        "created_at":  datetime.now().isoformat(),
    }
    log(f'"{username}" is now hosting "{lobbies[username]["world_name"]}"', "magenta")
    return {"success": True, "host": username}


@app.delete("/host/{host_username}")
def close_world(host_username: str):
    """Host manually closes their world."""
    username = validate_username(host_username)
    if username not in lobbies:
        raise HTTPException(404, "No active world found for that username.")
    world_name = lobbies[username]["world_name"]
    _destroy_lobby(username)
    log(f'"{username}" closed world "{world_name}"', "yellow")
    return {"success": True}


# ─────────────────────────────────────────────
#  WebSocket relay
#  ws://server/join/{host_username}/{your_username}
#
#  Players join using the HOST'S USERNAME as the address.
#  The server relays all packets — neither side ever
#  sees the other's IP.
# ─────────────────────────────────────────────
@app.websocket("/join/{host_username}/{player_username}")
async def join_world(
    ws: WebSocket, host_username: str, player_username: str
):
    # ── Guards ──────────────────────────────
    if host_username not in lobbies:
        await ws.close(code=4004, reason="World not found.")
        return

    lobby = lobbies[host_username]

    if not db_exists(player_username):
        await ws.close(code=4001, reason="Unknown username.")
        return

    if len(lobby["players"]) >= lobby["max_players"]:
        await ws.close(code=4003, reason="World is full.")
        return

    if player_username in lobby["players"]:
        await ws.close(code=4002, reason="Already connected.")
        return

    # ── Accept ──────────────────────────────
    await ws.accept()

    lobby["players"].append(player_username)
    connections.setdefault(host_username, {})[player_username] = ws

    log(f'"{player_username}" joined "{lobby["world_name"]}" (host: {host_username})', "green")

    # Tell everyone someone joined
    await _broadcast(host_username, {
        "type":     "player_joined",
        "username": player_username,
        "players":  lobby["players"],   # full updated list of usernames
    })

    # ── Relay loop ──────────────────────────
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            # Tag with sender, relay to everyone else
            msg["from"] = player_username
            await _broadcast(host_username, msg, exclude=player_username)

    except WebSocketDisconnect:
        await _player_left(host_username, player_username)


# ─────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────
async def _player_left(host_username: str, player_username: str):
    if host_username not in lobbies:
        return

    lobby = lobbies[host_username]

    if player_username in lobby["players"]:
        lobby["players"].remove(player_username)

    if host_username in connections:
        connections[host_username].pop(player_username, None)

    log(f'"{player_username}" left "{lobby["world_name"]}"', "yellow")

    # If the HOST disconnected, close the whole world
    if player_username == host_username:
        log(f'Host "{host_username}" disconnected — closing world', "red")
        await _broadcast(host_username, {
            "type":   "world_closed",
            "reason": "The host left.",
        })
        _destroy_lobby(host_username)
    else:
        await _broadcast(host_username, {
            "type":     "player_left",
            "username": player_username,
            "players":  lobby["players"],
        })


def _destroy_lobby(host_username: str):
    lobbies.pop(host_username, None)
    connections.pop(host_username, None)


async def _broadcast(host_username: str, message: dict, exclude: str | None = None):
    conns = connections.get(host_username, {})
    dead  = []
    payload = json.dumps(message)
    for uname, sock in conns.items():
        if uname == exclude:
            continue
        try:
            await sock.send_text(payload)
        except Exception:
            dead.append(uname)
    for uname in dead:
        conns.pop(uname, None)
        if host_username in lobbies and uname in lobbies[host_username]["players"]:
            lobbies[host_username]["players"].remove(uname)


# ─────────────────────────────────────────────
#  Rich live dashboard
# ─────────────────────────────────────────────
def build_dashboard() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="logs", size=16),
    )
    layout["body"].split_row(
        Layout(name="worlds", ratio=3),
        Layout(name="stats",  ratio=1),
    )

    # Header
    layout["header"].update(Panel(
        Text("🎀  YanSim Multiplayer Server", style="bold magenta", justify="center"),
        style="magenta",
    ))

    # Worlds table
    tbl = Table(box=box.SIMPLE_HEAVY, expand=True)
    tbl.add_column("Host",       style="bold cyan",  min_width=12)
    tbl.add_column("World Name", style="bold white")
    tbl.add_column("Players",    justify="center",   width=10)
    tbl.add_column("Who's In",   style="dim")

    for data in lobbies.values():
        who = ", ".join(data["players"]) or "—"
        tbl.add_row(
            data["host"],
            data["world_name"],
            f'{len(data["players"])} / {data["max_players"]}',
            who,
        )

    layout["worlds"].update(Panel(tbl, title="[bold]Active Worlds[/bold]", border_style="blue"))

    # Stats
    total_online = sum(len(d["players"]) for d in lobbies.values())
    s = Text()
    s.append("Registered Users\n", style="dim")
    s.append(f"{db_user_count()}\n\n", style="bold cyan")
    s.append("Open Worlds\n", style="dim")
    s.append(f"{len(lobbies)}\n\n", style="bold magenta")
    s.append("Players Online\n", style="dim")
    s.append(f"{total_online}\n\n", style="bold green")
    s.append("Port\n", style="dim")
    s.append(f"{PORT}\n", style="bold yellow")

    layout["stats"].update(Panel(s, title="[bold]Stats[/bold]", border_style="green"))

    # Logs
    log_text = Text()
    for entry in server_logs:
        log_text.append_text(Text.from_markup(entry + "\n"))

    layout["logs"].update(Panel(log_text, title="[bold]Log[/bold]", border_style="dim"))

    return layout


def _dashboard_loop():
    with Live(build_dashboard(), refresh_per_second=2, screen=False) as live:
        while True:
            live.update(build_dashboard())
            threading.Event().wait(0.5)


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=_dashboard_loop, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="error")
