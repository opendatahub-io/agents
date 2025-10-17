from utils.k8s import KubernetesProbe

import asyncio
import logging
import signal
import threading
from typing import Dict, Set

class Orchestrator:
    """
    Manages tasks for watching the cluster and processing
    identified issues.
    """

    def __init__(self, max_no_of_crews=1):
        self._setup_logging()

        self.k8s = KubernetesProbe()
        self.max_no_of_crews = max_no_of_crews
        self.sem = asyncio.Semaphore(max_no_of_crews)
        self.running = True

        # Add signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _setup_logging(self):
        """
        Setup basic logging, not production ready
        """
        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level="INFO", format=format)
        self.logger = logging.getLogger(__name__)

    def _signal_handler(self, signum, frame):
        """
        Start the shutdown sequence:
        1. Clear issues queue immediately to unblock event watcher
        2. Set has_issues event to unblock the main event loop
        """
        signame = signal.Signals(signum).name
        self.logger.info(f"Received shutdown signal {signame} ({signum}). Shutting down...")

        # Clear queue to unblock and signal event watcher to shutdown
        self.k8s.running = False
        self.k8s.issues.shutdown(immediate=True)

        # Set has_issues event to unblock the main event loop
        self.running = False
        self.k8s.has_issues.set()

    async def _process_issue(self, issue):
        # TODO: Create a crew that can process the issue
        pass

    async def monitor_cluster(self):
        # Create a new thread that monitors events in the cluster
        watch_thread = threading.Thread(target=self.k8s.watch_events)
        watch_thread.start()

        try:
            while self.running:
                # Wait for signal that issue(s) are available
                # Also used to initiate the shutdown process
                self.k8s.has_issues.wait()

                # Process next available issue
                issue = self.k8s.next_issue()
                if issue:
                    print(f"Received issue: {issue}")
                    # FIXME: Create a crew that can process the issue
                    # crew_task = asyncio.create_task(self._process_issue(issue))

        except Exception as exp:
            raise exp
        finally:
            self.logger.info("Waiting for watch thread to terminate...")
            watch_thread.join(timeout=20)
            if watch_thread.is_alive():
                self.logger.warning("Watch thread did not terminate gracefully within timeout")
            else:
                self.logger.info("Watch thread terminated successfully")

        self.logger.info("Exiting!")
