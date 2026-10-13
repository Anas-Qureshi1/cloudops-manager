pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        IMAGE_NAME = 'cloudops-manager'
        IMAGE_TAG = 'ci'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '''
                    python --version
                    python -m pip install --upgrade pip
                    python -m pip install -r requirements.txt
                    python -m pip install pytest
                '''
            }
        }

        stage('Run Tests') {
            steps {
                bat 'python -m pytest -v --junitxml=test-results.xml'
            }

            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'test-results.xml'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t %IMAGE_NAME%:%IMAGE_TAG% .'
            }
        }

        stage('Verify Docker Image') {
            steps {
                bat 'docker image inspect %IMAGE_NAME%:%IMAGE_TAG%'
            }
        }
    }

    post {
        success {
            echo 'CloudOps Manager CI pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed. Review the stage logs to identify the problem.'
        }

        always {
            echo 'CloudOps Manager CI pipeline finished.'
        }
    }
}