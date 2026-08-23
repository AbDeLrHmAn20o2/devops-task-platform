```groovy
pipeline {
    agent any

    environment {
        IMAGE_NAME = "devops-task-platform-backend"
        IMAGE_TAG = "ci"
        TEST_IMAGE = "devops-task-platform-test:ci"
        KUBECONFIG = "/var/jenkins_home/kubeconfig"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Test Image') {
            steps {
                sh '''
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

                    docker network rm ci-network 2>/dev/null || true
                    docker network create ci-network

                    docker rm -f ci-postgres 2>/dev/null || true

                    docker run -d \
                      --name ci-postgres \
                      --network ci-network \
                      -e POSTGRES_DB=devopsdb \
                      -e POSTGRES_USER=devopsuser \
                      -e POSTGRES_PASSWORD=devopspassword \
                      postgres:16-alpine

                    echo "Waiting for PostgreSQL..."

                    for i in $(seq 1 30); do
                        if docker exec ci-postgres pg_isready \
                            -U devopsuser \
                            -d devopsdb > /dev/null 2>&1; then
                            echo "PostgreSQL is ready"
                            break
                        fi

                        if [ "$i" -eq 30 ]; then
                            echo "PostgreSQL failed to become ready"
                            docker logs ci-postgres
                            exit 1
                        fi

                        sleep 2
                    done

                    echo "Testing database DNS..."

                    docker run --rm \
                      --network ci-network \
                      postgres:16-alpine \
                      pg_isready \
                      -h ci-postgres \
                      -p 5432 \
                      -U devopsuser \
                      -d devopsdb

                    echo "Running pytest..."

                    docker run --rm \
                      --network ci-network \
                      -e DB_HOST=ci-postgres \
                      -e DB_PORT=5432 \
                      -e DB_NAME=devopsdb \
                      -e DB_USER=devopsuser \
                      -e DB_PASSWORD=devopspassword \
                      ${TEST_IMAGE} \
                      python -m pytest

                    echo "Tests completed successfully"

                    docker rm -f ci-postgres
                    docker network rm ci-network
                '''
            }

            post {
                always {
                    sh '''
                        docker rm -f ci-postgres 2>/dev/null || true
                        docker network rm ci-network 2>/dev/null || true
                    '''
                }
            }
        }

        stage('Build Production Image') {
            steps {
                sh '''
                    docker build \
                      -t ${IMAGE_NAME}:${IMAGE_TAG} \
                      ./app/backend
                '''
            }
        }

        stage('Load Image to Minikube') {
            steps {
                sh '''
                    docker exec minikube crictl images | grep ${IMAGE_NAME} || true
                '''
            }
        }

        stage('Deploy PostgreSQL') {
            steps {
                sh '''
                    kubectl --kubeconfig=${KUBECONFIG} apply -f k8s/postgres-secret.yaml
                    kubectl --kubeconfig=${KUBECONFIG} apply -f k8s/postgres-pvc.yaml
                    kubectl --kubeconfig=${KUBECONFIG} apply -f k8s/postgres-deployment.yaml
                    kubectl --kubeconfig=${KUBECONFIG} apply -f k8s/postgres-service.yaml
                '''
            }
        }

        stage('Deploy Backend') {
            steps {
                sh '''
                    kubectl --kubeconfig=${KUBECONFIG} apply -f k8s/backend-deployment.yaml
                    kubectl --kubeconfig=${KUBECONFIG} apply -f k8s/backend-service.yaml
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    kubectl --kubeconfig=${KUBECONFIG} rollout status deployment/postgres --timeout=120s
                    kubectl --kubeconfig=${KUBECONFIG} rollout status deployment/backend --timeout=120s

                    kubectl --kubeconfig=${KUBECONFIG} get pods
                    kubectl --kubeconfig=${KUBECONFIG} get services
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    kubectl --kubeconfig=${KUBECONFIG} exec deployment/backend -- \
                      python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/health').read().decode())"

                    kubectl --kubeconfig=${KUBECONFIG} exec deployment/backend -- \
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
    }
}
```
