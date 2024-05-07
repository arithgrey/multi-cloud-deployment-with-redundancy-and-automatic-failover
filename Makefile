#Aqui se encuentra la documentacion de instalación de istio -> https://istio.io/latest/docs/setup/getting-started/
ISTIO_VERSION := 1.21.2
TARGET_ARCH := x86_64

delete-minikube:
	@if command -v minikube &> /dev/null && minikube status &> /dev/null; then \
		echo "Minikube está instalado y corriendo. Eliminando..."; \
		minikube delete; \
		echo "Minikube eliminado exitosamente."; \
	else \
		echo "Minikube no está instalado o no está corriendo. No se requiere acción."; \
	fi

install-istio: delete-minikube start-minikube
	curl -L https://istio.io/downloadIstio | ISTIO_VERSION=$(ISTIO_VERSION) TARGET_ARCH=$(TARGET_ARCH) sh -
	cd istio-$(ISTIO_VERSION)/bin && export PATH="$(PWD):$$PATH" && istioctl version
	istioctl install --set profile=demo -y

install-demo: install-istio
	
	kubectl apply -f k8s
	@echo "_________  Servicios desplegados  __________"
	kubectl get services -n test
	@echo "_________  Pods __________"
	kubectl get pods -n test
	
	@echo "_________ Gateway  __________"

	kubectl get gateway -n test

	@echo "_________ Virtualservice  __________"
	kubectl get virtualservice -n test
	kubectl label namespace test istio-injection=enabled
	kubectl get namespace test -o yaml | grep istio-injection
	istioctl analyze --namespace test
	kubectl get svc istio-ingressgateway -n istio-system
	minikube service istio-ingressgateway -n istio-system --url
	kubectl port-forward service/hola-mundo 8080:80 -n test
	
apply:
	kubectl apply -f k8s
	istioctl analyze --namespace test
	kubectl get svc istio-ingressgateway -n istio-system
	kubectl port-forward service/hola-mundo 8080:80 -n test

port-forwar-server-1:

	@echo "________PUEDES VER EL SERVICIO EN:"
	@echo "http://localhost:8080/hola-mundo"
	@echo "http://localhost:8080/hola-mundo-nuevo"
	kubectl port-forward service/hola-mundo 8080:80 -n test
	

port-forwar-server-2:

	@echo "________PUEDES VER EL SERVICIO EN:"
	@echo "http://localhost:8081/hola-mundo"
	@echo "http://localhost:8081/hola-mundo-nuevo"
	kubectl port-forward service/hola-mundo 8081:80 -n test
	

deployments:
	@echo "_________  ISTIO  __________"
	kubectl get pods -n istio-system
	@echo "_________  Servicios desplegados  __________"
	kubectl get services -n test
	@echo "_________  Pods __________"
	kubectl get pods -n test
	@echo "_________ deployments __________"
	kubectl get deployments -n test
	@echo "_________ Gateway  __________"
	kubectl get gateway -n test
	@echo "_________ Virtualservice  __________"
	kubectl get virtualservice -n test

update-local-proxy:
	
	@echo "Se verifica configuración"
	nginx -t
	@echo "NGINX proxy configuration updated."
	@sudo systemctl restart nginx
	@echo "NGINX restarted."
	@sudo systemctl status nginx
	@echo "NGINX restarted."

test-response:
	@echo "Verificamos que responda en localhost"
	curl localhost
	
	@echo "Verificamos que responda en localhost / hola-mundo "
	curl http://localhost/hola-mundo

	@echo "Verificamos que responda en localhost / nuevo"
	curl http://localhost/hola-mundo-nuevo
	

#Esta tarea va después de minikube tunnel solo en el caso de ser usado
ingress-info:
	$(eval INGRESS_HOST := $(shell kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}'))
	$(eval INGRESS_PORT := $(shell kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].port}'))
	$(eval SECURE_INGRESS_PORT := $(shell kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="https")].port}'))
	$(eval GATEWAY_URL := $(INGRESS_HOST):$(INGRESS_PORT))

	@echo "Ingress Host: $(INGRESS_HOST)"
	@echo "Ingress Port: $(INGRESS_PORT)"
	@echo "Secure Ingress Port: $(SECURE_INGRESS_PORT)"
	@echo "Gateway URL: $(GATEWAY_URL)"


start-minikube:
#sudo apt-get update
#sudo apt-get install -y libvirt-daemon-system libvirt-clients qemu-kvm
	minikube start --driver=kvm2 --force
	@echo "Setting up kubectl alias..."
	@alias kubectl="minikube kubectl --"
	@echo "_________   Minikube started and kubectl alias configured successfully __________"

.PHONY: start-minikube delete-minikube
