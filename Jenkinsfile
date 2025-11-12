pipeline {
  agent any

  parameters {
    string(name: 'DEPLOY_HOST', defaultValue: 'YOUR_EC2_IP_OR_HOST', description: 'EC2 host for deployment (ip or dns)')
  }

  environment {
    DEPLOY_USER = "ubuntu"
    DEPLOY_TARGET_BASE = "/var/www/html"
    SSH_CRED_ID = "ec2-ssh-key"    // create this SSH Username with private key credential in Jenkins
    APP_ENV = ""                   // will be set dynamically in the pipeline
  }

  options {
    skipStagesAfterUnstable()
    ansiColor('xterm')
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '30')) // keep last 30 builds
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        echo "Checked out branch ${env.BRANCH_NAME}"
      }
    }

    stage('Build') {
      steps {
        sh label: 'Create venv & install deps', script: '''
          python3 -m venv .venv || true
          . .venv/bin/activate
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          deactivate
        '''
      }
    }

    stage('Test') {
      steps {
        sh label: 'Run pytest (if present)', script: '''
          . .venv/bin/activate
          if [ -d tests ] || ls test_*.py >/dev/null 2>&1; then
            pytest -q || (echo "Pytest failed" && exit 1)
          else
            echo "No tests found - skipping pytest"
          fi
          deactivate
        '''
      }
    }

    stage('Package') {
      steps {
        sh label: 'Create package', script: '''
          rm -f build.tar.gz || true
          tar -czf build.tar.gz --exclude='.venv' --exclude='.git' .
          ls -lh build.tar.gz
        '''
        archiveArtifacts artifacts: 'build.tar.gz', fingerprint: true
      }
    }

    stage('Deploy') {
      when {
        anyOf {
          branch 'staging'
          branch 'main'
        }
      }
      steps {
        script {
          // set APP_ENV and TARGET_DIR dynamically and export to env for later usage
          env.APP_ENV = (env.BRANCH_NAME == 'main') ? "production" : "staging"
          def targetDir = (env.BRANCH_NAME == 'main') ? "${env.DEPLOY_TARGET_BASE}" : "${env.DEPLOY_TARGET_BASE}/staging"
          env.TARGET_DIR = targetDir
          echo "Deploying branch '${env.BRANCH_NAME}' to '${env.TARGET_DIR}' (APP_ENV=${env.APP_ENV})"
        }

        // Use the SSH credential (sshUserPrivateKey) from Jenkins Credentials
        withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CRED_ID,
                                          keyFileVariable: 'SSH_KEY_FILE',
                                          usernameVariable: 'SSH_USER')]) {
          // upload artifact and deploy on remote host
          sh label: 'Upload and deploy to EC2', script: """
            set -euo pipefail

            REMOTE=\"${SSH_USER}@${params.DEPLOY_HOST}\"
            KEY=\"${SSH_KEY_FILE}\"
            BUILD=\"build.tar.gz\"
            REMOTE_TMP=\"/home/${SSH_USER}/build.tar.gz\"
            TARGET_DIR='${TARGET_DIR}'
            DEPLOY_BASE='${DEPLOY_TARGET_BASE}'

            echo \"Ensuring target parent exists on remote: \${DEPLOY_BASE}\"
            ssh -o StrictHostKeyChecking=no -i \"${KEY}\" \"${REMOTE}\" \"sudo mkdir -p '${DEPLOY_BASE}' && sudo chown ${SSH_USER}:${SSH_USER} '${DEPLOY_BASE}'\"

            echo \"Copying package to remote...\"
            scp -o StrictHostKeyChecking=no -i \"${KEY}\" \"${BUILD}\" \"${REMOTE}:\${REMOTE_TMP}\"

            echo \"Extracting package on remote into \${TARGET_DIR} and setting APP_ENV=${APP_ENV}\"
            ssh -o StrictHostKeyChecking=no -i \"${KEY}\" \"${REMOTE}\" bash -lc \"
              sudo mkdir -p \\\"\${TARGET_DIR}\\\"
              sudo tar -xzf \\\"\${REMOTE_TMP}\\\" -C \\\"\${TARGET_DIR}\\\" --strip-components=0
              echo APP_ENV=${env.APP_ENV} | sudo tee \\\"\\\${TARGET_DIR}/.env\\\" >/dev/null
              sudo chown -R ${SSH_USER}:www-data \\\"\\\${TARGET_DIR}\\\"
              # If there is a systemd unit named 'flaskapp', restart it
              if sudo systemctl list-unit-files | grep -q '^flaskapp.service'; then
                sudo systemctl daemon-reload || true
                sudo systemctl restart flaskapp || true
              fi
              sudo systemctl restart nginx || true
            \"
            echo \"Deploy finished.\"
          """
        }
      }
    }
  }

  post {
    success {
      echo "BUILD SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER} (branch: ${env.BRANCH_NAME})"
      // optionally send email/notification here (emailext or mail)
    }
    failure {
      echo "BUILD FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER} (branch: ${env.BRANCH_NAME})"
      // optionally send email/notification here (emailext or mail)
    }
    cleanup {
      // keep workspace clean if desired
      sh 'rm -f build.tar.gz || true'
    }
  }
}
