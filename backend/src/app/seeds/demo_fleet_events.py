from datetime import datetime, timedelta


def demo_fleet_event_data() -> list[dict[str, object]]:
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    return [
        {
            "title": "Port Battle Briefing",
            "category": "port_battle",
            "description": "Fleet briefing, role assignment and final supplies check before the battle window.",
            "location": "Fleet voice / target port",
            "start_at": now + timedelta(days=2, hours=19 - now.hour),
            "end_at": now + timedelta(days=2, hours=21 - now.hour),
            "all_day": False,
        },
        {
            "title": "Gunnery Training",
            "category": "training",
            "description": "Short practice block for arcs, chain shot timing and coordinated focus fire.",
            "location": "Training waters",
            "start_at": now + timedelta(days=5, hours=20 - now.hour),
            "end_at": now + timedelta(days=5, hours=22 - now.hour),
            "all_day": False,
        },
        {
            "title": "Fleet Farm Run",
            "category": "fleet_farm",
            "description": "Relaxed resource and XP farming round. Bring repair kits and cargo space.",
            "location": "Rally point announced in voice",
            "start_at": now + timedelta(days=8, hours=18 - now.hour),
            "end_at": now + timedelta(days=8, hours=21 - now.hour),
            "all_day": False,
        },
    ]
