pipeline {
    agent any

    environment {
        VENV_DIR = 'venv'
        APP_PORT = '8000'
        PID_FILE = 'app.pid'
    }

    stages {
        stage('Checkout') {
            steps {
                echo '=== Checking out code from GitHub ==='
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo '=== Installing Dependencies ==='
                sh '''
                    rm -rf ${VENV_DIR}
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo '=== Running Unit Tests ==='
                withCredentials([string(credentialsId: 'MONGO_URI', variable: 'MONGO_URI')]) {
                    sh '''
                        . ${VENV_DIR}/bin/activate
                        export MONGO_URI="${MONGO_URI}"
                        pytest tests/ -v --tb=short || exit 1
                    '''
                }
            }
        }

        stage('Deploy to Staging') {
            steps {
                echo '=== Deploying to Staging Environment ==='

                withCredentials([
                    string(credentialsId: 'MONGO_URI', variable: 'MONGO_URI'),
                    string(credentialsId: 'SECRET_KEY', variable: 'SECRET_KEY')
                ]) {
                    sh '''
                        echo "=== Starting Deployment ==="

                        # Stop previous instance if running
                        if [ -f ${PID_FILE} ]; then
                            PID=$(cat ${PID_FILE})
                            if ps -p $PID > /dev/null 2>&1; then
                                echo "Stopping previous instance (PID: $PID)"
                                kill $PID 2>/dev/null || true
                                sleep 3
                            fi
                            rm -f ${PID_FILE}
                        fi

                        # Kill any process on port 8000
                        if lsof -Pi :${APP_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
                            echo "Killing process on port ${APP_PORT}"
                            kill -9 $(lsof -t -i:${APP_PORT}) 2>/dev/null || true
                            sleep 2
                        fi

                        # Activate venv and export secrets
                        . ${VENV_DIR}/bin/activate
                        export MONGO_URI="${MONGO_URI}"
                        export SECRET_KEY="${SECRET_KEY}"

                        # Start Flask app with Gunicorn
                        # CRITICAL: Use JENKINS_NODE_COOKIE to prevent Jenkins from killing the process
                        cd ${WORKSPACE}
                        JENKINS_NODE_COOKIE=dontKillMe nohup ${WORKSPACE}/${VENV_DIR}/bin/gunicorn -w 4 -b 0.0.0.0:${APP_PORT} app:app > app.log 2>&1 &
                        
                        echo $! > ${PID_FILE}

                        echo "Waiting for application to start..."
                        sleep 8

                        if ps -p $(cat ${PID_FILE}) > /dev/null 2>&1; then
                            echo "Application deployed successfully!"
                            echo "PID: $(cat ${PID_FILE})"
                        else
                            echo "Deployment failed!"
                            cat app.log
                            exit 1
                        fi
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                echo '=== Performing Health Check ==='
                sh '''
                    sleep 5
                    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${APP_PORT}/ || echo "000")

                    if [ "$HTTP_CODE" = "200" ]; then
                        echo "Health check PASSED! Application is running."
                        echo "Application URL: http://localhost:${APP_PORT}"
                    else
                        echo "Health check FAILED! HTTP Status: $HTTP_CODE"
                        echo "=== Application Log ==="
                        cat app.log
                        echo "=== End of Log ==="
                        exit 1
                    fi
                '''
            }
        }
    }

    post {
        success {
            echo '=== Pipeline Completed Successfully! ==='
            emailext (
                subject: "SUCCESS: Jenkins Pipeline - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                    <h2>Build Successful!</h2>
                    <p><strong>Job:</strong> ${env.JOB_NAME}</p>
                    <p><strong>Build Number:</strong> ${env.BUILD_NUMBER}</p>
                    <p><strong>Status:</strong> SUCCESS</p>
                    <p><strong>Application URL:</strong> http://35.179.76.28:${APP_PORT}</p>
                    <p>Check console output at: ${env.BUILD_URL}</p>
                """,
                to: 'sheikhramiz666@gmail.com',
                mimeType: 'text/html'
            )
        }

        failure {
            echo '=== Pipeline Failed! ==='
            sh '''
                if [ -f ${PID_FILE} ]; then
                    kill $(cat ${PID_FILE}) 2>/dev/null || true
                    rm -f ${PID_FILE}
                fi
            '''
            emailext (
                subject: "FAILURE: Jenkins Pipeline - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                    <h2>Build Failed!</h2>
                    <p><strong>Job:</strong> ${env.JOB_NAME}</p>
                    <p><strong>Build Number:</strong> ${env.BUILD_NUMBER}</p>
                    <p><strong>Status:</strong> FAILURE</p>
                    <p>Check console output at: ${env.BUILD_URL}</p>
                    <p>Please review the logs and fix the issues.</p>
                """,
                to: 'sheikhramiz666@gmail.com',
                mimeType: 'text/html'
            )
        }

        always {
            echo '=== Archiving Artifacts ==='
            archiveArtifacts artifacts: 'app.log', allowEmptyArchive: true
            echo '=== Build complete. Application remains running. ==='
        }
    }
}
