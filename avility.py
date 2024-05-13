import os
import subprocess
from config import cluster_names

class IstioInstaller:
    def __init__(self, istio_version="1.21.2", target_arch="x86_64"):
        self.istio_version = istio_version
        self.target_arch = target_arch

    def check_istio_installed(self):
        # Verificar si Istio ya está instalado
        if os.path.exists(f'istio-{self.istio_version}/bin/istioctl'):
            print(f"Istio version {self.istio_version} already installed.")
            return True
        else:
            return False

    def install_istio(self):
        if not self.check_istio_installed():
            os.system(f'curl -L https://istio.io/downloadIstio | ISTIO_VERSION={self.istio_version} TARGET_ARCH={self.target_arch} sh -')
            # Agregar Istio al PATH
            istio_path = os.path.join(os.getcwd(), f'istio-{self.istio_version}/bin')
            os.environ["PATH"] += os.pathsep + istio_path
            
            # Verificar la versión de Istio instalada
            subprocess.run(['istioctl', 'version'], check=True)
            
            # Verificar si los pods de Istio están en un estado "Running" o "Ready"
            try:
                subprocess.run(['kubectl', 'get', 'pods', '-n', 'istio-system'], check=True)
                print("Istio pods are running.")
            except subprocess.CalledProcessError as e:
                print(f"Error checking Istio pods: {e}")


class KubectlApply:
    def __init__(self, cluster_names):
        self.cluster_names = cluster_names

    def cluster_exists(self, cluster_name):
        try:
            subprocess.run(['kubectl', 'config', 'get-contexts', cluster_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False

    def create_cluster(self, cluster_name):
        if not self.cluster_exists(cluster_name):
            print(f"Clúster de Minikube '{cluster_name}' no existe ahora lo vamos a crear ...")
            try:
                subprocess.run(['minikube', 'start', '-p', cluster_name, '--force'], check=True)
                print(f"Clúster de Minikube '{cluster_name}' creado correctamente.")

            except subprocess.CalledProcessError as e:
                print(f"Error al crear el clúster de Minikube '{cluster_name}': {e}")


    def apply_to_cluster(self, cluster_name):
        if not self.cluster_exists(cluster_name):
            print(f"El clúster '{cluster_name}' no existe. Creando...")
            self.create_cluster(cluster_name)
        try:
            subprocess.run(['kubectl', 'config', 'use-context', cluster_name], check=True)
            subprocess.run(['istioctl', 'install', '--set', 'profile=demo','-y'], check=True)
            subprocess.run(['kubectl', '--context', cluster_name, 'apply', '-f', 'k8s'], check=True)
            print(f"Configuración aplicada correctamente en el clúster '{cluster_name}'.")
        except subprocess.CalledProcessError as e:
            print(f"Error al aplicar la configuración en el clúster '{cluster_name}': {e}")


    def apply_to_clusters(self):
        for name in self.cluster_names:
            print(f"Aplicando configuración en el clúster '{name}'...")
            self.apply_to_cluster(name)
    
    def applied_in_cluster(self):
        for name in self.cluster_names:
            print(f"Manifiestos aplicados en el clúster '{name}'...")
            try:
                subprocess.run(['kubectl', '--context', name, 'get', 'all', '-n', 'test'], check=True)
                subprocess.run(['minikube', 'service', 'hola-mundo', '--profile', name, '-n', 'test', '--url'], check=True)
                
            except subprocess.CalledProcessError as e:
                print(f"Error al obtener recursos en el clúster '{name}': {e}")

class AppDeployer:
    def __init__(self, istio_installer, kubernetes_manager):
        self.istio_installer = istio_installer
        self.kubernetes_manager = kubernetes_manager

    def deploy(self):
        # Instalar Istio en cada clúster
        self.istio_installer.install_istio()
        
        # Aplicar configuración de Kubernetes en cada clúster
        for cluster_name in self.kubernetes_manager.cluster_names:
            print(f"Deploying application in cluster '{cluster_name}'...")
            self.kubernetes_manager.apply_to_cluster(cluster_name)
        
        # Verificar si la configuración se aplicó correctamente en cada clúster
        self.kubernetes_manager.applied_in_cluster()
                    
def main():
    kubectl_apply = KubectlApply(cluster_names)
    istio_installer = IstioInstaller()
    app_deployer = AppDeployer(istio_installer, kubectl_apply)
    app_deployer.deploy()

if __name__ == "__main__":
    main()
