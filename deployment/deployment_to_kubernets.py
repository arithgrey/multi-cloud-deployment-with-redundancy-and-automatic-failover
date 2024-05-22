import os
import re
import shutil
from dotenv import dotenv_values
from extractor import EnvConfigurator

class DeploymentGenerator:
    def __init__(self, env_file=".env_conf"):
        self.env_vars = self.load_env_vars(env_file)

    def load_env_vars(self, env_file):
        try:
            return dotenv_values(env_file)
        except Exception as e:
            print(f"Error loading environment variables from {env_file}: {e}")
            exit(1)

    def load_template(self, template_file):
        try:
            with open(template_file, "r") as template:
                return template.read()
        except Exception as e:
            print(f"Error loading template file {template_file}: {e}")
            exit(1)

    def find_and_replace_variables(self, content):
        pattern = r"\$\{(\w+)\}"
        replaced_content = re.sub(pattern, lambda x: self.env_vars.get(x.group(1), x.group(0)), content)
        return replaced_content

    def generate_deployment(self, input_dir="../.ci/k8s", output_dir="k8s", output_file="deploy.yaml"):
        output_content = ""

        try:
            # Crea el directorio de salida si no existe
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Crea el directorio de plantillas si no existe
            if not os.path.exists(input_dir):
                os.makedirs(input_dir)

            # Itera sobre los archivos en el directorio de entrada
            for filename in os.listdir(input_dir):
                input_file = os.path.join(input_dir, filename)
                if os.path.isfile(input_file):
                    template_content = self.load_template(input_file)
                    replaced_content = self.find_and_replace_variables(template_content)
                    output_content += replaced_content.strip() + "\n\n"

            # Escribe el contenido en el archivo de salida
            output_path = os.path.join(output_dir, output_file)
            with open(output_path, "w") as output:
                output.write(output_content.strip("\n---\n"))

            print(f"Deployment file '{output_file}' generated successfully in '{output_dir}' directory.")

            # Copiar archivos desde k8s_base a ../.ci/local/k8s
            for filename in os.listdir('k8s_base'):
                src = os.path.join('k8s_base', filename)
                dst = os.path.join(output_dir, filename)
                shutil.copy(src, dst)
                print(f"File '{filename}' copied successfully from 'k8s_base' to '{output_dir}' directory.")

            # Aplicar los manifiestos usando kubectl apply -f
            self.apply_manifests(output_dir)

        except Exception as e:
            print(f"Error generating deployment file: {e}")
            exit(1)

    def apply_manifests(self, manifest_dir):
        try:
            for filename in os.listdir(manifest_dir):
                manifest_file = os.path.join(manifest_dir, filename)
                if os.path.isfile(manifest_file) and filename.endswith(".yaml"):
                    os.system(f"kubectl apply -f {manifest_file}")
                    print(f"Applied manifest '{manifest_file}' successfully.")
        except Exception as e:
            print(f"Error applying manifests: {e}")
            exit(1)

if __name__ == "__main__":
    yaml_file = '../.ci/pipe/azure-pipelines_beta.yaml'
    env_config_file = '.env_conf'
    configurator = EnvConfigurator(yaml_file, env_config_file)
    configurator.configure_environment()

    generator = DeploymentGenerator()
    generator.generate_deployment()
