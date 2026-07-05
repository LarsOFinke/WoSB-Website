from fastapi import APIRouter

router = APIRouter()


@router.get("/home")
def get_home() -> dict[str, object]:
    return {
        "route": "/home",
        "title": "WoSB Community Hub",
        "subtitle": "A focused hub for community tools around World of Sea Battle.",
        "modules": [
            {
                "key": "builds",
                "title": "Build Manager",
                "status": "available",
            },
            {
                "key": "groups",
                "title": "Group Management",
                "status": "prototype",
            }
        ],
    }
