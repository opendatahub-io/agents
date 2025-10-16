from utils.k8s import KubernetesProbe

import asyncio
import threading
from typing import Dict, Set

class Orchestrator:
    """
    Manages tasks for watching the cluster and processing
    identified issues.
    """

    def __init__(self, max_no_of_crews=1):
        self.k8s = KubernetesProbe()
        self.max_no_of_crews = max_no_of_crews
        self.sem = asyncio.Semaphore(max_no_of_crews)
        self.running = True

    async def _process_issue(self, issue):
        # TODO: Create a crew that can process the issue
        pass

    async def monitor_cluster(self):
        # Create a new thread that monitors events in the cluster
        watch_thread = threading.Thread(
            target=self.k8s.watch_events,
            daemon=True,
        )
        watch_thread.start()

        try:
            while self.running:
                # Wait for signal that issue(s) are available
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
            watch_thread.join()

        print("Exiting!")
