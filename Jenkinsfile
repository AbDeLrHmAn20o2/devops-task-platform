pipeline {
agent any

```
environment {
    IMAGE_NAME = "devops-task-platform-backend"
    IMAGE_TAG  = "ci"
    TEST_IMAGE = "devops-task-platform-test:ci"
    KUBECONFIG = "/var/jenkins_home/kubeconfig"
}

stages {

    stage('Terraform Validate') {
        steps {
            sh '''
                set -e

                echo "=== Terraform Files ==="
                ls -la terraform

                echo "=== Terraform Format Check ==="

                docker run --rm \
                  -v "$WORKSPACE:/workspace" \
                  -w /workspace/terraform \
                  hashicorp/terraform:latest \
                  fmt -check

                echo "=== Terraform Init ==="

                docker run --rm \
                  -v "$WORKSPACE:/workspace" \
                  -w /workspace/terraform \
                  hashicorp/terraform:latest \
                  init -backend=false

                echo "=== Terraform Validate ==="

                docker run --rm \
                  -v "$WORKSPACE:/workspace" \
                  -w /workspace/terraform \
                  hashicorp/terraform:latest \
                  validate
            '''
        }
    }

    stage('Terraform Plan') {
        steps {
            sh '''
                set -e

                echo "=== Terraform Plan ==="

                docker run --rm \
                  -v "$WORKSPACE:/workspace" \
                  -w /workspace/terraform \
                  hashicorp/terraform:latest \
                  plan
            '''
        }
    }

    stage('Ansible Syntax Check') {
        steps {
            sh '''
                set -e

                echo "=== Ansible Files ==="
                ls -la ansible
                ls -la ansible/playbooks

                echo "=== Ansible Syntax Check ==="

                docker run --rm \
                  -v "$WORKSPACE/ansible:/workspace" \
                  -w /workspace \
                  cytopia/ansible:latest \
                  ansible-playbook \
                  --syntax-check \
                  playbooks/setup.yml
            '''
        }
    }

    stage('Build Test Image') {
        steps {
            sh '''
                set -e

                echo "=== Building Test Image ==="

                docker build \
                  -t ${TEST_IMAGE} \
                  ./app/backend
            '''
        }
    }

    stage('Run Tests') {
        steps {
            sh '''
                set -e

                cleanup() {
                    echo "=== Cleaning CI resources ==="
                    docker rm -f ci-postgres 2>/dev/null || true
                    docker network rm ci-network 2>/dev/null || true
                }

                trap cleanup EXIT

                docker rm -f ci-postgres 2>/dev/null || true
                docker network rm ci-network 2>/dev/null || true

                echo "=== Creating CI network ==="

                docker network create ci-network

                echo "=== Starting PostgreSQL ==="

                docker run -d \
                  --name ci-postgres \
                  --network ci-network \
                  -e POSTGRES_DB=devopsdb \
                  -e POSTGRES_USER=devopsuser \
                  -e POSTGRES_PASSWORD=devopspassword \
                  postgres:16-alpine

                echo "=== Waiting for PostgreSQL ==="

                POSTGRES_READY=false

                for i in $(seq 1 30); do

                    if docker exec ci-postgres \
                        pg_isready \
                        -U devopsuser \
                        -d devopsdb > /dev/null 2>&1; then

                        echo "PostgreSQL is ready"

                        POSTGRES_READY=true

                        break
                    fi

                    echo "Waiting for PostgreSQL... attempt $i/30"

                    sleep 2
                done

                if [ "$POSTGRES_READY" != "true" ]; then
                    echo "PostgreSQL failed to become ready"
                    docker logs ci-postgres
                    exit 1
                fi

                echo "=== Testing PostgreSQL DNS ==="

                docker run --rm \
                  --network ci-network \
                  postgres:16-alpine \
                  pg_isready \
                  -h ci-postgres \
                  -p 5432 \
                  -U devopsuser \
                  -d devopsdb

                echo "=== Running pytest ==="

                docker run --rm \
                  --network ci-network \
                  -e DB_HOST=ci-postgres \
                  -e DB_PORT=5432 \
                  -e DB_NAME=devopsdb \
                  -e DB_USER=devopsuser \
                  -e DB_PASSWORD=devopspassword \
                  ${TEST_IMAGE} \
                  python -m pytest

                echo "=== Tests passed ==="
            '''
        }
    }

    stage('Build Production Image') {
        steps {
            sh '''
                set -e

                echo "=== Building Production Image ==="

                docker build \
                  -t ${IMAGE_NAME}:${IMAGE_TAG} \
                  ./app/backend

                echo "=== Production Image Built ==="

                docker images ${IMAGE_NAME}:${IMAGE_TAG}
            '''
        }
    }

    stage('Load Image to Minikube') {
        steps {
            sh '''
                set -e

                echo "=== Checking Image in Minikube ==="

                docker exec minikube crictl images | \
                  grep ${IMAGE_NAME} || true
            '''
        }
    }

    stage('Deploy PostgreSQL') {
        steps {
            sh '''
                set -e

                echo "=== Deploying PostgreSQL ==="

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply -f k8s/postgres-secret.yaml

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply -f k8s/postgres-pvc.yaml

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply -f k8s/postgres-deployment.yaml

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply -f k8s/postgres-service.yaml
            '''
        }
    }

    stage('Deploy Backend') {
        steps {
            sh '''
                set -e

                echo "=== Deploying Backend ==="

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply -f k8s/backend-deployment.yaml

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply -f k8s/backend-service.yaml
            '''
        }
    }

    stage('Verify Deployment') {
        steps {
            sh '''
                set -e

                echo "=== Waiting for PostgreSQL Rollout ==="

                kubectl --kubeconfig=${KUBECONFIG} \
                  rollout status deployment/postgres \
                  --timeout=120s

                echo "=== Waiting for Backend Rollout ==="

                kubectl --kubeconfig=${KUBECONFIG} \
                  rollout status deployment/backend \
                  --timeout=120s

                echo "=== Kubernetes Pods ==="

                kubectl --kubeconfig=${KUBECONFIG} \
                  get pods

                echo "=== Kubernetes Services ==="

                kubectl --kubeconfig=${KUBECONFIG} \
                  get services
            '''
        }
    }

    stage('Health Check') {
        steps {
            sh '''
                set -e

                echo "=== Backend Health Check ==="

                kubectl --kubeconfig=${KUBECONFIG} \
                  exec deployment/backend -- \
                  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/health').read().decode())"

                echo "=== Database Health Check ==="

                kubectl --kubeconfig=${KUBECONFIG} \
                  exec deployment/backend -- \
                  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/db-health').read().decode())"
            '''
        }
    }
}

post {
    success {
        echo 'CI/CD Pipeline completed successfully!'
    }

    failure {
        echo 'CI/CD Pipeline failed.'
    }

    always {
        echo 'Pipeline execution finished.'
    }
}
```

}
