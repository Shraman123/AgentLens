from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from supabase import create_client
from analyzer import analyze_conversations_batch
from alerts import send_failure_alert
import os
import logging

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
FAILURE_RATE_THRESHOLD = 20  # alert if failure rate exceeds this %

scheduler = AsyncIOScheduler()

async def run_analysis_for_all_projects():
    """Auto-analyze all unanalyzed conversations and send alerts if needed."""
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        projects = sb.table("projects").select("id,name,user_id").execute()
        if not projects.data:
            return

        for project in projects.data:
            pid = project["id"]

            # get unanalyzed conversations
            result = sb.table("conversations").select("*")\
                .eq("project_id", pid)\
                .eq("analyzed", False)\
                .limit(100).execute()

            conversations = result.data or []
            if conversations:
                results = await analyze_conversations_batch(conversations)
                for r in results:
                    sb.table("conversations").update({
                        "intent": r.get("intent"),
                        "sentiment": r.get("sentiment"),
                        "is_failure": r.get("is_failure", False),
                        "failure_reason": r.get("failure_reason"),
                        "analyzed": True
                    }).eq("id", r["id"]).execute()

                logger.info(f"Auto-analyzed {len(results)} conversations for {project['name']}")

            # check failure rate and send alert if needed
            all_convs = sb.table("conversations").select("is_failure,user_message,failure_reason")\
                .eq("project_id", pid).execute()

            convs = all_convs.data or []
            total = len(convs)
            if total < 10:
                continue  # not enough data yet

            failures = sum(1 for c in convs if c.get("is_failure"))
            failure_rate = round(failures / total * 100, 1)

            if failure_rate > FAILURE_RATE_THRESHOLD:
                # get user email
                try:
                    user = sb.auth.admin.get_user_by_id(project["user_id"])
                    if user and user.user:
                        top_failures = [c for c in convs if c.get("is_failure")][:5]
                        await send_failure_alert(
                            to_email=user.user.email,
                            project_name=project["name"],
                            failure_rate=failure_rate,
                            total=total,
                            failures=failures,
                            top_failures=top_failures
                        )
                except Exception as e:
                    logger.error(f"Could not get user email: {e}")

    except Exception as e:
        logger.error(f"Scheduler error: {e}")


def start_scheduler():
    scheduler.add_job(
        run_analysis_for_all_projects,
        trigger=IntervalTrigger(hours=1),
        id="auto_analysis",
        name="Auto Analysis + Alerts",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started — auto-analysis + alerts every 1 hour")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
