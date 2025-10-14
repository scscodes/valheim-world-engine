# Server-Side Telemetry Plugin Concepts

**Status:** Ideation Phase
**Purpose:** Document server-side BepInEx plugin concepts for managed lloesche/valheim-server instances
**Requirement:** Must work with vanilla clients (no client-side mods required)

---

## Overview

Server-side BepInEx plugins that run on dedicated servers to provide rich telemetry, analytics, and automation without requiring players to install any mods. All functionality is transparent to vanilla clients.

**Key Principle:** Server knows everything about the game state - we just need to export it.

---

## Use Cases

### 1. Player Location Tracking

**Data Captured:**
- Real-time player positions (x, y, z coordinates)
- Current biome
- Health/stamina status
- AFK detection
- Movement patterns

**Applications:**
- Live player dashboard ("Where are my friends?")
- Activity heatmaps
- Exploration coverage analysis
- Death location history
- Safety zones analysis (where do players spend time?)
- AFK detection for server management

**Implementation Approach:**
```csharp
void Update() {
    foreach (Player player in Player.GetAllPlayers()) {
        Vector3 pos = player.transform.position;
        var data = new {
            name = player.GetPlayerName(),
            steamId = player.GetPlayerID(),
            position = new { x = pos.x, y = pos.y, z = pos.z },
            biome = Heightmap.FindBiome(pos),
            health = player.GetHealth(),
            isDead = player.IsDead(),
            timestamp = DateTime.UtcNow
        };
        ExportToAPI("/telemetry/player_position", data);
    }
}
```

**Export Frequency:** 5-10 second intervals (configurable)

---

### 2. Chat Logging & Analysis

**Data Captured:**
- Chat messages (Say, Shout, Whisper)
- Sender information
- Sender position when message sent
- Timestamp
- Message type

**Applications:**
- Chat history & search
- Moderation logging
- Keyword alerts ("help!", "boss", "stuck")
- Communication analytics
- Discord integration
- Toxicity detection
- Community sentiment analysis

**Implementation Approach:**
```csharp
void Awake() {
    On.Chat.OnNewChatMessage += OnChatMessage;
}

void OnChatMessage(orig, self, go, senderID, pos, type, user, text) {
    orig(self, go, senderID, pos, type, user, text); // Call original

    var chatData = new {
        sender = user,
        message = text,
        type = type.ToString(),
        position = pos,
        timestamp = DateTime.UtcNow
    };

    ExportToAPI("/telemetry/chat", chatData);

    // Check for alert keywords
    if (text.Contains("help", StringComparison.OrdinalIgnoreCase)) {
        TriggerAlert(chatData);
    }
}
```

**Export Frequency:** Real-time (chat is low-frequency naturally)

---

### 3. Game Events Monitoring

**Events to Track:**
- Player deaths (location, cause, items lost)
- Boss defeats (which boss, time taken, participants)
- Portal usage (source/destination tracking)
- Building events (structures placed/destroyed)
- Resource gathering (trees, ore, plants)
- Raid events (start/end, outcome)
- Ship/cart usage
- Skill progression milestones
- World day/night cycle
- Weather events

**Applications:**
- Server timeline/history
- Boss progression tracking
- Economic analysis (resource flow)
- Achievement system
- Community milestones
- Death statistics ("Most dangerous biome")
- Portal network visualization

**Implementation Approach:**
```csharp
// Death tracking
void OnPlayerDeath(Player player) {
    var deathData = new {
        player = player.GetPlayerName(),
        position = player.transform.position,
        biome = Heightmap.FindBiome(player.transform.position),
        cause = player.GetLastDamageSource(),
        itemsLost = GetDroppedItems(player),
        timestamp = DateTime.UtcNow
    };
    ExportToAPI("/telemetry/death", deathData);
}

// Boss defeat tracking
void OnBossDefeated(Character boss) {
    var bossData = new {
        bossName = boss.GetHoverName(),
        position = boss.transform.position,
        participants = GetNearbyPlayers(boss.transform.position, 100f),
        timestamp = DateTime.UtcNow
    };
    ExportToAPI("/telemetry/boss_defeat", bossData);
}
```

---

### 4. Server Health & Performance

**Metrics to Track:**
- Active player count
- Server uptime
- World day number
- FPS/TPS (if accessible)
- Memory usage
- Event queue length
- Network statistics

**Applications:**
- Server monitoring dashboard
- Performance alerts
- Capacity planning
- Crash detection & recovery

---

## Plugin Architecture

### Proposed Structure

```
etl/experimental/bepinex-server-telemetry/
├── src/
│   ├── ServerTelemetry/
│   │   ├── ServerTelemetry.csproj
│   │   ├── ServerTelemetryPlugin.cs          # Main plugin
│   │   ├── Exporters/
│   │   │   ├── PlayerLocationExporter.cs
│   │   │   ├── ChatExporter.cs
│   │   │   ├── EventExporter.cs
│   │   │   └── ApiClient.cs                  # HTTP client for backend
│   │   ├── Models/
│   │   │   ├── PlayerPosition.cs
│   │   │   ├── ChatMessage.cs
│   │   │   └── GameEvent.cs
│   │   └── Config/
│   │       └── TelemetryConfig.cs
├── plugins/                                   # Compiled DLLs
├── config/
│   └── ServerTelemetry.cfg
├── docker/
│   └── docker-compose.yml                     # lloesche/valheim-server integration
└── README.md
```

### Configuration File Example

```ini
[General]
ApiEndpoint = http://your-backend:8000/api/v1/telemetry
ApiKey = your-secret-key
ServerIdentifier = valheim-server-01

[PlayerTracking]
Enabled = true
UpdateInterval = 5.0
TrackPositions = true
TrackHealth = true
TrackBiome = true

[ChatLogging]
Enabled = true
LogPrivateMessages = false
AlertKeywords = help,stuck,boss,raid

[EventTracking]
Enabled = true
TrackDeaths = true
TrackBosses = true
TrackBuilding = true
TrackPortals = true

[Performance]
BatchSize = 50
BatchInterval = 10.0
RetryAttempts = 3
```

---

## Backend Integration

### FastAPI Endpoints (Extension to Adaptive Sampling Client)

```python
# Add to etl/experimental/adaptive-sampling-client/backend/

@router.post("/telemetry/player_position")
async def receive_player_position(data: PlayerPosition):
    """Receive and store player position updates"""
    await db.player_positions.insert_one(data.dict())
    await websocket_manager.broadcast({
        "type": "player_update",
        "data": data.dict()
    })
    return {"status": "received"}

@router.post("/telemetry/chat")
async def receive_chat_message(message: ChatMessage):
    """Log chat message and check for alerts"""
    await db.chat_messages.insert_one(message.dict())

    # Check for keyword alerts
    if any(kw in message.text.lower() for kw in ALERT_KEYWORDS):
        await send_discord_alert(message)

    return {"status": "logged"}

@router.post("/telemetry/event")
async def receive_game_event(event: GameEvent):
    """Track game events (deaths, bosses, etc.)"""
    await db.game_events.insert_one(event.dict())

    # Update statistics
    await update_server_stats(event)

    return {"status": "processed"}

@router.get("/telemetry/players/live")
async def get_live_players(server_id: str):
    """Get current player positions and status"""
    # Return recent player positions (last 30 seconds)
    return await db.player_positions.find({
        "server_id": server_id,
        "timestamp": {"$gte": datetime.now() - timedelta(seconds=30)}
    }).to_list(length=100)
```

---

## Dashboard Concepts

### Live Player Map
- Overlay player positions on world map
- Show current biome, health status
- Click player for details/history
- Heatmap of activity over time

### Chat Monitor
- Real-time chat feed
- Search/filter by player, keyword, time
- Moderation actions
- Alert notifications

### Server Timeline
- Chronological event log
- Boss defeats, deaths, milestones
- Filterable by event type
- Export to JSON/CSV

### Analytics Dashboard
- Player activity graphs
- Popular biomes/areas
- Death statistics
- Resource gathering trends
- Server health metrics

---

## Privacy & Security Considerations

### Data Collection
- **Position tracking**: Consider opt-out mechanism
- **Chat logging**: Disclose in server rules
- **Event tracking**: Generally acceptable (public game state)

### Data Storage
- Implement retention policies (auto-delete old data)
- Encrypt sensitive data (player IDs, chat)
- Access controls on dashboard

### GDPR Compliance
- Right to access (players can request their data)
- Right to deletion (purge player data on request)
- Transparent disclosure of tracking

---

## Performance Considerations

### Plugin Impact
- Batch exports every N seconds (not per-event)
- Async HTTP calls (don't block game thread)
- Configurable update rates
- Graceful degradation if backend unavailable

### Network Impact
- JSON compression
- Rate limiting
- Retry with exponential backoff
- Local caching if backend unreachable

### Server Load
- Minimal - only serialization and HTTP calls
- Most processing happens in backend
- No impact on vanilla clients

---

## Deployment with lloesche/valheim-server

### Docker Compose Integration

```yaml
version: "3"
services:
  valheim:
    image: lloesche/valheim-server
    container_name: valheim-server
    environment:
      SERVER_NAME: "My Tracked Server"
      WORLD_NAME: "TrackedWorld"
      SERVER_PASS: "secret"
      SERVER_PUBLIC: "1"
      # BepInEx already supported by lloesche image
    volumes:
      - ./valheim_data:/config
      - ./bepinex/plugins:/config/bepinex/plugins
      - ./bepinex/config:/config/bepinex/config
    ports:
      - "2456-2458:2456-2458/udp"

  backend:
    build: ./etl/experimental/adaptive-sampling-client/backend
    container_name: valheim-backend
    environment:
      DATABASE_URL: "mongodb://mongo:27017"
    ports:
      - "8000:8000"
    depends_on:
      - mongo

  mongo:
    image: mongo:6
    container_name: valheim-mongo
    volumes:
      - ./mongo_data:/data/db
```

---

## Implementation Priority

### Phase 1: Foundation
1. Basic plugin structure
2. API client for backend communication
3. Configuration system
4. Player position tracking

### Phase 2: Core Features
1. Chat logging
2. Death tracking
3. Boss defeat tracking
4. Basic dashboard

### Phase 3: Advanced Features
1. Resource tracking
2. Building events
3. Portal network
4. Advanced analytics

### Phase 4: Polish
1. Performance optimization
2. Dashboard enhancements
3. Alert system
4. Discord integration

---

## Related Documentation

- [BepInEx Plugin Development](https://docs.bepinex.dev/)
- [Valheim Modding Wiki](https://valheim.fandom.com/wiki/Modding)
- [lloesche/valheim-server](https://github.com/lloesche/valheim-server-docker)

---

## Status & Next Steps

**Current Status:** Ideation complete, awaiting implementation decision

**Blockers:** None - all concepts are proven viable

**Next Steps:**
1. Complete world screenshot plugin (higher priority)
2. Create basic ServerTelemetry plugin structure
3. Implement player position tracking as proof-of-concept
4. Test with lloesche/valheim-server
5. Extend with additional telemetry features

**Timeline Estimate:**
- Basic plugin: 2-4 hours
- Core features: 1-2 days
- Full implementation: 1 week
- Dashboard: 1-2 weeks

---

**Questions to Address Before Implementation:**

1. Which telemetry features are most valuable for MVP?
2. Database choice for backend (MongoDB, PostgreSQL, TimescaleDB)?
3. Real-time dashboard requirements (WebSockets vs polling)?
4. Privacy policy and data retention requirements?
5. Discord integration priority?

---

**Last Updated:** 2025-10-14
**Author:** Claude Code
**Related:** `docs/WORLD_SCREENSHOT_PLUGIN.md` (to be created)
