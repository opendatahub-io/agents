import logging

from utils.values import EXCLUDE_NAMESPACES, FLAG_STATES

from kubernetes import client, config

class KubernetesProbe:
    """
    Scans namespaces for pods in waiting and terminating state.

    The scanner excludes "kube-system", "kube-public", "kube-node-lease",
    and "local-path-storage" namespaces.

    Additionally, only the pods with the following statuses are flagged: 
    - "CrashLoopBackOff"
    - "ImagePullBackOff"
    - "ErrImagePull"
    - "CreateContainerConfigError"
    - "InvalidImageName"
    - "OOMKilled"
    - "Error"
    - "ContainerCannotRun"
    
    You can change the lists of excluded namespaces and flagged statuses in utils/values.py.
    """

    def __init__(self):
        self._setup_logging()
        self._init_k8s_client()

    def _setup_logging(self):
        """
        Setup basic logging, not production ready
        """
        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level="INFO", format=format)
        self.logger = logging.getLogger(__name__)

    def _init_k8s_client(self):
        """
        Authenticate using kube config file and return a V1 client
        """
        try:
            # Try in-cluster configuration
            config.load_incluster_config()
        except config.ConfigException:
            try:
                self.logger.info("Using default kubeconfig to authenticate")
                config.load_kube_config()
            except Exception as exp:
                err_message = "Could not initialize a kubernetes client"
                self.logger.error(err_message)
                raise RuntimeError(err_message)

        # Cnce authenticated, instantiate a K8s client
        self.client = client.CoreV1Api()

    def _scan_pod(self, pod):
        """
        Check for pods with containers in waiting and terminated states.
        Also check that the reason falls in the list of flaggable reasons. 
        """
        for container_status in pod.status.container_statuses:
            state = container_status.state
            if not state:
                continue

            # check if in terminated or waiting state
            if state.waiting or state.terminated:
                reason = state.waiting.reason
                if reason in FLAG_STATES:
                    return {
                        'pod': pod.metadata.name,
                        'namespace': pod.metadata.namespace,
                        'container': container_status.name,
                        'reason': reason,
                    }
        
        return None

    def scan_namespaces(self):
        """
        Scans namespaces for pods in waiting and terminating state.
        Return a list of issues, if any, and ones that are flaggable. 
        """
        issues = []
        try:
            namespaces = self.client.list_namespace()    
            for item in namespaces.items:
                namespace = item.metadata.name
                if namespace in EXCLUDE_NAMESPACES:
                    continue
                
                # List all pods in the namespace
                pods = self.client.list_namespaced_pod(namespace)

                # scan pods for known issues
                for pod in pods.items:
                    issue = self._scan_pod(pod)
                    if issue:
                        issues.append(issue)
        except Exception as exp:
            err_message = f"Error scanning pods in namespaces: {exp}"
            self.logger.error(err_message)
            raise RuntimeError(err_message)

        return issues
