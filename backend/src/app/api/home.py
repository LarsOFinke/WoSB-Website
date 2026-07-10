from fastapi import APIRouter

router = APIRouter()


@router.get("/home")
def get_home() -> dict[str, object]:
    return {
        "route": "/home",
        "title": "Royal Blackwater Vanguards",
        "subtitle": "A focused hub for community tools around World of Sea Battle.",
        "modules": [
            {
                "key": "builds",
                "title": "Build Manager",
                "status": "available",
            },
            {
                "key": "groups",
                "title": "Fleet Announcements",
                "status": "prototype",
            },
            {
                "key": "forum",
                "title": "Forum",
                "status": "prototype",
            },
            {
                "key": "guides",
                "title": "Guides",
                "status": "prototype",
            }
        ],
    }
