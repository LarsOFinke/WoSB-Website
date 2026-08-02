from __future__ import annotations


OPERATION_MESSAGES = {
    "backup.configuration.deleted": """🔐 **Backup Configuration Removed**
Requested by: **{actor.display_name}**
Status: queued for the protected host runner
Reference: `{resource.id}`
🔗 [Open backup administration]({resource.url})""",
    "backup.configuration.updated": """🔐 **Backup Configuration Changed**
Action: `{data.action}`
Requested by: **{actor.display_name}**
Status: queued for the protected host runner
Reference: `{resource.id}`
🔗 [Open backup administration]({resource.url})""",
    "backup.restore.requested": """🚨 **Database Restore Requested**
Backup reference: `{data.backup_id}`
Requested by: **{actor.display_name}**
Status: awaiting protected host approval
🔗 [Review backup status]({resource.url})""",
    "backup.run.requested": """💾 **Application Backup Requested**
Requested by: **{actor.display_name}**
Status: queued for the protected host runner
Includes: database, uploads and encrypted recovery bundle
🔗 [Review backup status]({resource.url})""",
}


__all__ = ["OPERATION_MESSAGES"]
