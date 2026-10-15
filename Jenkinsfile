```groovy
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

        stage('Gitleaks Secret Scan') {
            steps {
                bat '''
                    "C:\\Users\\Anas\\AppData\\Local\\Microsoft\\WinGet\\Links\\gitleaks.exe" git . --redact --exit-code 1
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '''
                    python --version
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

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    bat '''
                        "C:\\sonar-scanner-8.1.0.6389-windows-x64\\bin\\sonar-scanner.bat" ^
                        -Dsonar.token=%SONAR_AUTH_TOKEN%
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        def qualityGate = waitForQualityGate()

                        if (qualityGate.status != 'OK') {
                            error "SonarQube Quality Gate failed: ${qualityGate.status}"
                        }
                    }
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
            echo 'Pipeline failed. Review the stage logs.'
        }

        always {
            echo 'CloudOps Manager CI pipeline finished.'
        }
    }
}
```