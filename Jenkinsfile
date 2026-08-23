pipeline {
agent any

environment {
    IMAGE_NAME = "devops-task-platform-backend"
    IMAGE_TAG  = "ci"
    TEST_IMAGE = "devops-task-platform-test:ci"
    KUBECONFIG = "/var/jenkins_home/kubeconfig"
}

stages {

    stage('Checkout') {
        steps {
            checkout scm
        }
    }

    /*
     * ============================================================
     * TERRAFORM
     * ============================================================
     */

    stage('Terraform Validate') {
        steps {
            sh '''
                set -e

                echo "========================================"
                echo "       Terraform Files"
                echo "========================================"

                ls -la "${WORKSPACE}/terraform"

                echo "========================================"
                echo "       Terraform Format Check"
                echo "========================================"

                docker run --rm \
                  -v "${WORKSPACE}/terraform:/workspace" \
                  -w /workspace \
                  hashicorp/terraform:latest \
                  fmt -check

                echo "========================================"
                echo "       Terraform Validate"
                echo "========================================"

                docker run --rm \
                  -v "${WORKSPACE}/terraform:/workspace" \
                  -w /workspace \
                  hashicorp/terraform:latest \
                  validate

                echo "Terraform validation completed successfully."
            '''
        }
    }

    stage('Terraform Plan') {
        steps {
            sh '''
                set -e

                echo "========================================"
                echo "       Terraform Initialization"
                echo "========================================"

                docker run --rm \
                  -v "${WORKSPACE}/terraform:/workspace" \
                  -w /workspace \
                  hashicorp/terraform:latest \
                  init -backend=false

                echo "========================================"
                echo "       Terraform Plan"
                echo "========================================"

                docker run --rm \
                  -v "${WORKSPACE}/terraform:/workspace" \
                  -w /workspace \
                  hashicorp/terraform:latest \
                  plan

                echo "Terraform plan completed successfully."
            '''
        }
    }

    /*
     * ============================================================
     * ANSIBLE
     * ============================================================
     */

    stage('Ansible Syntax Check') {
        steps {
            sh '''
                set -e

                echo "========================================"
                echo "       Ansible Syntax Check"
                echo "========================================"

                docker run --rm \
                  -v "${WORKSPACE}/ansible:/workspace" \
                  -w /workspace \
                  cytopia/ansible:latest \
                  ansible-playbook \
                  --syntax-check \
                  playbooks/setup.yml

                echo "Ansible syntax check completed successfully."
            '''
        }
    }

    /*
     * ============================================================
     * BUILD TEST IMAGE
     * ============================================================
     */

    stage('Build Test Image') {
        steps {
            sh '''
                set -e

                echo "========================================"
                echo "       Building Test Image"
                echo "========================================"

                docker build \
                  -t ${TEST_IMAGE} \
                  ./app/backend

                echo "Test image built successfully."
            '''
        }
    }

    /*
     * ============================================================
     * RUN PYTEST
     * ============================================================
     */

    stage('Run Tests') {
        steps {
            sh '''
                set -e

                cleanup() {
                    echo "========================================"
                    echo "       Cleaning CI Resources"
                    echo "========================================"

                    docker rm -f ci-postgres 2>/dev/null || true
                    docker network rm ci-network 2>/dev/null || true
                }

                trap cleanup EXIT

                docker rm -f ci-postgres 2>/dev/null || true
                docker network rm ci-network 2>/dev/null || true

                echo "========================================"
                echo "       Creating CI Network"
                echo "========================================"

                docker network create ci-network

                echo "========================================"
                echo "       Starting PostgreSQL"
                echo "========================================"

                docker run -d \
                  --name ci-postgres \
                  --network ci-network \
                  -e POSTGRES_DB=devopsdb \
                  -e POSTGRES_USER=devopsuser \
                  -e POSTGRES_PASSWORD=devopspassword \
                  postgres:16-alpine

                echo "========================================"
                echo "       Waiting for PostgreSQL"
                echo "========================================"

                POSTGRES_READY=false

                for i in $(seq 1 30); do

                    if docker exec ci-postgres \
                        pg_isready \
                        -U devopsuser \
                        -d devopsdb > /dev/null 2>&1; then

                        echo "PostgreSQL is ready."

                        POSTGRES_READY=true

                        break
                    fi

                    echo "Waiting for PostgreSQL... attempt $i/30"

                    sleep 2
                done

                if [ "$POSTGRES_READY" != "true" ]; then

                    echo "PostgreSQL failed to become ready."

                    docker logs ci-postgres

                    exit 1
                fi

                echo "========================================"
                echo "       Testing PostgreSQL DNS"
                echo "========================================"

                docker run --rm \
                  --network ci-network \
                  postgres:16-alpine \
                  pg_isready \
                  -h ci-postgres \
                  -p 5432 \
                  -U devopsuser \
                  -d devopsdb

                echo "========================================"
                echo "       Running Pytest"
                echo "========================================"

                docker run --rm \
                  --network ci-network \
                  -e DB_HOST=ci-postgres \
                  -e DB_PORT=5432 \
                  -e DB_NAME=devopsdb \
                  -e DB_USER=devopsuser \
                  -e DB_PASSWORD=devopspassword \
                  ${TEST_IMAGE} \
                  python -m pytest

                echo "========================================"
                echo "       All Tests Passed"
                echo "========================================"
            '''
        }
    }

    /*
     * ============================================================
     * PRODUCTION IMAGE
     * ============================================================
     */

    stage('Build Production Image') {
        steps {
            sh '''
                set -e

                echo "========================================"
                echo "       Building Production Image"
                echo "========================================"

                docker build \
                  -t ${IMAGE_NAME}:${IMAGE_TAG} \
                  ./app/backend

                echo "========================================"
                echo "       Production Image"
                echo "========================================"

                docker images ${IMAGE_NAME}:${IMAGE_TAG}

                echo "Production image built successfully."
            '''
        }
    }

    /*
     * ============================================================
     * MINIKUBE
     * ============================================================
     */

    stage('Load Image to Minikube') {
        steps {
            sh '''
                set -e

                echo "========================================"
                echo "       Checking Image in Minikube"
                echo "========================================"

                docker exec minikube crictl images | \
                  grep ${IMAGE_NAME} || true

                echo "Minikube image check completed."
            '''
        }
    }

    /*
     * ============================================================
     * KUBERNETES - POSTGRESQL
     * ============================================================
     */

    stage('Deploy PostgreSQL') {
        steps {
            sh '''
                set -e

                echo "========================================"
                echo "       Deploying PostgreSQL"
                echo "========================================"

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply \
                  -f k8s/postgres-secret.yaml

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply \
                  -f k8s/postgres-pvc.yaml

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply \
                  -f k8s/postgres-deployment.yaml

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply \
                  -f k8s/postgres-service.yaml

                echo "PostgreSQL deployment completed."
            '''
        }
    }

    /*
     * ============================================================
     * KUBERNETES - BACKEND
     * ============================================================
     */

    stage('Deploy Backend') {
        steps {
            sh '''
                set -e

                echo "========================================"
                echo "       Deploying Backend"
                echo "========================================"

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply \
                  -f k8s/backend-deployment.yaml

                kubectl --kubeconfig=${KUBECONFIG} \
                  apply \
                  -f k8s/backend-service.yaml

                echo "Backend deployment completed."
            '''
        }
    }

    /*
     * ============================================================
     * KUBERNETES VERIFICATION
     * ============================================================
     */

    stage('Verify Deployment') {
        steps {
            sh '''
                set -e

                echo "========================================"
                echo "       Waiting for PostgreSQL"
                echo "========================================"

                kubectl --kubeconfig=${KUBECONFIG} \
                  rollout status \
                  deployment/postgres \
                  --timeout=120s

                echo "========================================"
                echo "       Waiting for Backend"
                echo "========================================"

                kubectl --kubeconfig=${KUBECONFIG} \
                  rollout status \
                  deployment/backend \
                  --timeout=120s

                echo "========================================"
                echo "       Kubernetes Pods"
                echo "========================================"

                kubectl --kubeconfig=${KUBECONFIG} \
                  get pods

                echo "========================================"
                echo "       Kubernetes Services"
                echo "========================================"

                kubectl --kubeconfig=${KUBECONFIG} \
                  get services

                echo "Kubernetes deployment verified successfully."
            '''
        }
    }

    /*
     * ============================================================
     * HEALTH CHECK
     * ============================================================
     */

    stage('Health Check') {
        steps {
            sh '''
                set -e

                echo "========================================"
                echo "       Backend Health Check"
                echo "========================================"

                kubectl --kubeconfig=${KUBECONFIG} \
                  exec deployment/backend -- \
                  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/health').read().decode())"

                echo "========================================"
                echo "       Database Health Check"
                echo "========================================"

                kubectl --kubeconfig=${KUBECONFIG} \
                  exec deployment/backend -- \
                  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/db-health').read().decode())"

                echo "Health checks completed successfully."
            '''
        }
    }
}

post {

    success {
        echo '========================================'
        echo 'CI/CD Pipeline completed successfully!'
        echo '========================================'
    }

    failure {
        echo '========================================'
        echo 'CI/CD Pipeline failed.'
        echo '========================================'
    }

    always {
        echo '========================================'
        echo 'Pipeline execution finished.'
        echo '========================================'
    }
}

}
