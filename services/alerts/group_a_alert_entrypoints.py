"""Group A alert composition; no CLI, scheduler, or credential loader."""

from services.alerts.group_a_delivery import deliver_group_a_cycle, deliver_group_a_image_cycle
from services.alerts.group_a_slack import send_group_a_slack
from services.alerts.group_a_watch import dispatch_group_a_alert, terminal_failure
from services.alerts.group_a_watch_cycle import QueueEventEvidence, WatchCycleResult


def deliver_watcher_alert(release, cursor_path, observation, *, cfg):
    """Deliver from one already collected, protected watcher cycle."""
    if type(observation) is not WatchCycleResult or type(observation.queue_events) is not QueueEventEvidence:
        raise ValueError("tracked_group_a_observation_required")
    return deliver_group_a_cycle(
        cursor_path, release, observation.report, observed_ms=observation.queue_events.observed_ms,
        queue_events=observation.queue_events, cfg=cfg, send_alert=send_group_a_slack,
    )


def deliver_terminal_alert(release, instance, *, cfg):
    """One direct attempt for an exact OnFailure instance, without replay."""
    finding = terminal_failure(release, instance)
    return dispatch_group_a_alert(release, finding, cfg=cfg, send_alert=send_group_a_slack)


def deliver_watcher_image_alert(release, directory_fd, observation, *, cfg):
    if type(observation) is not WatchCycleResult or type(observation.queue_events) is not QueueEventEvidence:
        raise ValueError("tracked_group_a_observation_required")
    return deliver_group_a_image_cycle(
        directory_fd, release, observation.report, observed_ms=observation.queue_events.observed_ms,
        queue_events=observation.queue_events, cfg=cfg, send_alert=send_group_a_slack,
    )
