from config import cluster_names
from avility import KubectlApply

def main():
    kubectl_apply = KubectlApply(cluster_names)
    kubectl_apply.applied_in_cluster()

if __name__ == "__main__":
    main()
