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
                    if exist "C:\\Tools\\gitleaks\\gitleaks.exe" (
                        "C:\\Tools\\gitleaks\\gitleaks.exe" git . --redact --exit-code 1
                    ) else (
                        "C:\\Users\\Anas\\AppData\\Local\\Microsoft\\WinGet\\Links\\gitleaks.exe" git . --redact --exit-code 1
                    )
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '''
                    python --version
                    python -m pip install --upgrade pip
                    python -m pip install -r requirements.txt
                    python -m pip install pytest pytest-cov pip-audit
                '''
            }
        }

        stage('Python Tests') {
            steps {
                bat 'python -m pytest --cov=app --cov-report=term --cov-report=xml:coverage.xml --junitxml=test-results.xml -p no:platformdirs'
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
                        set SONAR_TOKEN=%SONAR_AUTH_TOKEN%
                        "C:\\sonar-scanner-8.1.0.6389-windows-x64\\bin\\sonar-scanner.bat"
                    '''
                }
            }
        }

        stage('SonarQube Quality Gate') {
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

        stage('Dependency Vulnerability Scan') {
            steps {
                bat '''
                    python -m pip_audit -r requirements.txt --format json --output pip-audit-report.json
                    python -m pip_audit -r requirements.txt
                '''
            }

            post {
                always {
                    archiveArtifacts artifacts: 'pip-audit-report.json', allowEmptyArchive: true
                }
            }
        }

        stage('Docker Image Build') {
            steps {
                bat 'docker build -t %IMAGE_NAME%:%IMAGE_TAG% .'
            }
        }

        stage('Trivy Image Vulnerability Scan') {
            steps {
                bat '''
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache/ aquasec/trivy:latest image --severity HIGH,CRITICAL %IMAGE_NAME%:%IMAGE_TAG%
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache/ aquasec/trivy:latest image --vuln-type library --severity CRITICAL --exit-code 1 %IMAGE_NAME%:%IMAGE_TAG%
                '''
            }
        }

        stage('Docker Image Verification') {
            steps {
                bat 'docker image inspect %IMAGE_NAME%:%IMAGE_TAG%'
            }
        }
    }

    post {
        success {
            echo 'CloudOps Manager DevSecOps pipeline completed successfully!'
        }

        failure {
            echo 'Pipeline failed. Review the stage logs and security findings.'
        }

        always {
            echo 'CloudOps Manager CI pipeline execution finished.'
        }
    }
}

