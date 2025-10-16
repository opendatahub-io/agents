EXCLUDE_NAMESPACES = ["kube-system", "kube-public", "kube-node-lease", "local-path-storage"]
FLAG_STATES = [
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "CreateContainerConfigError",
    "InvalidImageName",
    "OOMKilled",
    "Error",
    "ContainerCannotRun",
]
