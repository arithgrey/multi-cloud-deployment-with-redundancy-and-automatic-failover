cluster_name = 
name_space = devops


# Define la regla validate_setup
validate_setup:
	@echo "Validating setup..."
	@echo "----------------------------------------"
	kubectl get pods -n istio-system --context ${cluster_name}
	kubectl --context ${cluster_name} get all -n ${name_space}
	gcloud container clusters describe multi-k8s --region=us-central1 --project=findep-calidad-uat-mx --format="value(endpoint)"
	@echo "----------------------------------------"

# Define la regla uninstall_istio para desinstalar Istio
uninstall_istio:
	@echo "Uninstalling Istio from the cluster ${cluster_name}..."
	istioctl uninstall --context=${cluster_name} --purge -y
	kubectl --context=${cluster_name} delete namespace istio-system --ignore-not-found
	CRDS=$(kubectl --context=${cluster_name} get crd | grep 'istio.io' | awk '{print $$1}') && if [ -n "$$CRDS" ]; then echo "$$CRDS" | xargs -n1 kubectl --context=${cluster_name} delete crd; else echo "No Istio CRDs found"; fi
	@echo "Istio has been successfully uninstalled from the cluster ${cluster_name}."

# Define la regla install_istio para instalar Istio
install_istio:
	@echo "Installing Istio in the cluster ${cluster_name}..."

	# Crear el namespace "devops" si no existe
	kubectl --context=${cluster_name} create namespace ${name_space} --dry-run=client -o yaml | kubectl apply -f -
	
	# Instalar Istio con la inyección automática habilitada
	istioctl install --set profile=default -y --context=${cluster_name}

	# Aplicar etiquetas de inyección automática en los namespaces "default" y "devops"
	kubectl label namespace default istio-injection=enabled --context=${cluster_name}
	kubectl label namespace ${name_space} istio-injection=enabled --overwrite --context=${cluster_name}
	
	@echo "Waiting for Istio Ingress Gateway IP..."
	@ISTIO_INGRESS_IP=""
	while [ -z "$$ISTIO_INGRESS_IP" ]; do \
		echo "Waiting for external IP..."; \
		sleep 10; \
		ISTIO_INGRESS_IP=$$(kubectl --context=${cluster_name} get svc istio-ingressgateway -n istio-system -o=jsonpath='{.status.loadBalancer.ingress[0].ip}'); \
	done

	kubectl get svc istio-ingressgateway -n istio-system --context=${cluster_name}

get_ingress_ip:
	@echo "Istio Ingress Gateway IP"
	kubectl get svc istio-ingressgateway -n istio-system --context=${cluster_name}

get_injection_enabled:
	@echo "Namespaces with automatic sidecar injection enabled in Istio:"
	kubectl get namespaces --context=${cluster_name} -l istio-injection=enabled -o=jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}'

get_injected_services:
	@echo "Microservices injected by Istio in namespace ${name_space}:"
	kubectl get pods -n ${name_space} --context=${cluster_name} -o=jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' -l istio-injection=enabled
	
	@echo "Microservices injected by Istio in namespace default:"
	kubectl get pods -n default --context=${cluster_name} -o=jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' -l istio-injection=enabled

get_istio_proxy_status:
	istioctl proxy-status

get_url_example_service:
	@GATEWAY_IP=$$(kubectl get svc istio-ingressgateway -n istio-system -o=jsonpath='{.status.loadBalancer.ingress[0].ip}'); \
	GATEWAY_PORT=$$(kubectl get svc istio-ingressgateway -n istio-system -o=jsonpath='{.spec.ports[?(@.name=="http2")].port}'); \
	echo "URL del microservicio: http://$$GATEWAY_IP:$$GATEWAY_PORT/hola-mundo"

deploy_example:
	kubectl delete -f example.yaml --ignore-not-found=true
	@echo "Deploy example"
	kubectl apply -f example.yaml
	kubectl apply -f istio-gateway.yaml
	kubectl apply -f istio-ingressgateway.yaml
	

deploy_kiali:
	@echo "Deploy config kiali"
	kubectl apply -f /home/jmedranos/istio-1.22.0/samples/addons
	kubectl rollout status deployment/kiali -n istio-system
	kubectl apply -f kiali/

get_kiali_url:
	#@sleep 10 # Esperar unos segundos para que se asigne la IP externa
	@GATEWAY_IP=$$(kubectl get svc istio-ingressgateway -n istio-system -o=jsonpath='{.status.loadBalancer.ingress[0].ip}'); \
	if [ -z "$$GATEWAY_IP" ]; then \
		echo "La IP del IngressGateway aún no está disponible. Intente de nuevo en unos minutos."; \
	else \
		echo "URL de Kiali: http://$$GATEWAY_IP:15029/kiali"; \
	fi

istio_analized:
	@echo "Verificando que no haya problemas con la configuración ..."
	istioctl analyze

validate_mesh:
	@echo "Verificando que este disponible el Gateway"
	kubectl get gateway -n istio-system --context=${cluster_name}
	kubectl get virtualservice -n ${name_space}
	kubectl get virtualservice -n default
	@echo "Se verifica que este recibiendo solicitudes"
	kubectl logs -l app=istio-ingressgateway -n istio-system
	
