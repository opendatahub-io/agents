from utils.k8s import KubernetesProbe

import asyncio
from typing import Dict, Set

class Orchestrator:
    """
    Manages tasks for watching the cluster and processing
    identified issues.
    """

    def __init__(self, max_tasks=3):
        self.k8s = KubernetesProbe()
        self.max_tasks = max_tasks
        self.sem = asyncio.Semaphore(max_tasks)
        self.running = True

    async def _process_issue(self, issue):
        # TODO: Create a crew that can process the issue
        pass

    async def monitor_cluster(self):
        # Create a new task that monitors events in the cluster
        watch_task = asyncio.create_task(self.k8s.watch_events())

        try:
            while self.running:
                # Get next issue from the queue
                issue = await self.k8s.next_issue()
                if issue:
                    print(f"Received issue: {issue}")
                    # FIXME: Create a crew that can process the issue
                    # crew_task = asyncio.create_task(self._process_issue(issue))
        except Exception as exp:
            raise exp
        finally:
            watch_task.cancel()
