"""Match-safe six-hour Quake Live service restart for minqlx."""
import subprocess
import threading
import time

import minqlx


class technical_restart(minqlx.Plugin):
    INTERVAL_SECONDS = 6 * 60 * 60
    POLL_SECONDS = 30
    WARNING_SECONDS = 30
    COUNTDOWN_WARNINGS_MINUTES = (15, 10, 5, 1)

    def __init__(self):
        super().__init__()
        self._due_at = time.monotonic() + self.INTERVAL_SECONDS
        self._pending = False
        self._countdown_warnings_sent = set()
        self._match_warning_sent = False
        self._safe_warning_sent = False
        self._restart_scheduled = False
        self._restart_started = False
        self._lock = threading.Lock()
        self.add_hook("game_end", self.handle_game_end)
        minqlx.get_logger().info("technical_restart: next technical restart in 6 hours")
        self._poll()

    @minqlx.delay(POLL_SECONDS)
    def _poll(self):
        try:
            self._send_countdown_warning()
            if not self._pending and time.monotonic() >= self._due_at:
                self._pending = True
                minqlx.get_logger().info("technical_restart: six-hour interval elapsed; waiting for a safe point")
            if self._pending:
                self._restart_if_safe()
        except Exception:
            minqlx.log_exception()
        finally:
            if not self._restart_started:
                self._poll()

    def _send_countdown_warning(self):
        remaining = self._due_at - time.monotonic()
        due_warnings = [
            minutes for minutes in self.COUNTDOWN_WARNINGS_MINUTES
            if minutes not in self._countdown_warnings_sent
            and remaining <= minutes * 60
        ]
        if not due_warnings:
            return

        minutes = min(due_warnings)
        self.msg(
            "^1WARNING:^7 Technical restart in {} minute{}. "
            "Active duels will finish first.".format(
                minutes, "" if minutes == 1 else "s"
            )
        )
        self._countdown_warnings_sent.update(
            value for value in self.COUNTDOWN_WARNINGS_MINUTES
            if value >= minutes
        )
        minqlx.get_logger().info(
            "technical_restart: %s-minute countdown warning sent",
            minutes,
        )

    def _restart_if_safe(self):
        try:
            game = self.game
            if game is None:
                return
            state = game.state
        except Exception:
            minqlx.get_logger().warning("technical_restart: cannot read game state; deferring restart")
            return

        if state in ("in_progress", "countdown"):
            self._restart_scheduled = False
            self._safe_warning_sent = False
            if not self._match_warning_sent:
                self.msg("Technical restart is due. It will wait for the current duel to finish.")
                self._match_warning_sent = True
                minqlx.get_logger().info("technical_restart: active game detected; restart deferred")
            return

        if not self._safe_warning_sent and not self._restart_scheduled:
            self.msg("Technical restart in 30 seconds.")
            self._safe_warning_sent = True
            self._restart_scheduled = True
            minqlx.get_logger().info("technical_restart: no active game; 30-second warning sent")
            self._restart_later()

    @minqlx.delay(WARNING_SECONDS)
    def _restart_later(self):
        if self._restart_started:
            return
        try:
            game = self.game
            state = game.state if game is not None else None
        except Exception:
            minqlx.get_logger().warning("technical_restart: cannot re-check game state; deferring restart")
            self._restart_scheduled = False
            self._safe_warning_sent = False
            return
        if state in ("in_progress", "countdown") or state is None:
            self._restart_scheduled = False
            self._safe_warning_sent = False
            self._restart_if_safe()
            return
        threading.Thread(target=self._launch_restart, name="ql-technical-restart", daemon=True).start()

    def handle_game_end(self, _data):
        if self._pending and not self._restart_started:
            minqlx.get_logger().info("technical_restart: match ended; restart will proceed at the next safe poll")

    def _launch_restart(self):
        with self._lock:
            if self._restart_started:
                return
            self._restart_started = True
        minqlx.get_logger().warning("technical_restart: restarting quakelive.service after the six-hour interval")
        try:
            result = subprocess.run(
                ["sudo", "-n", "/usr/bin/systemctl", "restart", "quakelive.service"],
                check=False,
                timeout=45,
            )
            if result.returncode:
                minqlx.get_logger().error("technical_restart: systemctl returned %s", result.returncode)
                self._restart_started = False
        except Exception:
            self._restart_started = False
            minqlx.log_exception()
