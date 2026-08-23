pipeline {
    agent any

    environment {
        IMAGE_NAME = "devops-task-platform-backend"
        IMAGE_TAG = "ci"
        KUBECONFIG = "/var/jenkins_home/kubeconfig"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
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
            echo '✅ CI/CD Pipeline completed successfully!'
        }

        failure {
            echo '❌ CI/CD Pipeline failed.'
        }
    }
}