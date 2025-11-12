pipeline {
  agent any

  parameters {
    string(name: 'DEPLOY_HOST', defaultValue: 'YOUR_EC2_IP_OR_HOST', description: 'EC2 host for deployment (ip or dns)')
  }

  environment {
    DEPLOY_USER = "ubuntu"
    DEPLOY_TARGET_BASE = "/var/www/html"
    SSH_CRED_ID = "ec2-ssh-key"    // credential id you will create in Jenkins
    APP_ENV = ''                  // set dynamically
  }

  options {
    skipStagesAfterUnstable()
    ansiColor('xterm')
    timestamps()
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
        sh '''
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
        sh '''
          . .venv/bin/activate
          if ls tests >/dev/null 2>&1 || ls test_*.py >/dev/null 2>&1; then
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
        sh '''
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
          APP_ENV = (env.BRANCH_NAME == 'main') ? "production" : "staging"
          def TARGET_DIR = (env.BRANCH_NAME == 'main') ? "${DEPLOY_TARGET_BASE}" : "${DEPLOY_TARGET_BASE}/staging"
          echo "Deploying ${env.BRANCH_NAME} to ${TARGET_DIR} (APP_ENV=${APP_ENV})"
        }

        withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CRED_ID, keyFileVariable: 'SSH_KEY_FILE', usernameVariable: 'SSH_USER')]) {
          sh """
            # ensure target exists and upload artifact
            ssh -o StrictHostKeyChecking=no -i "${SSH_KEY_FILE}" ${SSH_USER}@${params.DEPLOY_HOST} "sudo mkdir -p ${DEPLOY_TARGET_BASE} && sudo chown ${SSH_USER}:${SSH_USER} ${DEPLOY_TARGET_BASE}"
            scp -o StrictHostKeyChecking=no -i "${SSH_KEY_FILE}" build.tar.gz ${SSH_USER}@${params.DEPLOY_HOST}:/home/${SSH_USER}/build.tar.gz

            ssh -o StrictHostKeyChecking=no -i "${SSH_KEY_FILE}" ${SSH_USER}@${params.DEPLOY_HOST} "
              TARGET_DIR='${TARGET_DIR}'
              sudo mkdir -p \"\$TARGET_DIR\"
              sudo tar -xzf /home/${SSH_USER}/build.tar.gz -C \"\$TARGET_DIR\" --strip-components=0
              echo APP_ENV=${APP_ENV} | sudo tee \"\$TARGET_DIR/.env\"
              sudo chown -R ${SSH_USER}:www-data \"\$TARGET_DIR\"
              if sudo systemctl is-enabled --quiet flaskapp; then
                sudo systemctl daemon-reload || true
                sudo systemctl restart flaskapp || true
              fi
              sudo systemctl restart nginx || true
            "
          """
        }
      }
    }
  }

  post {
    success {
      echo "BUILD SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
    failure {
      echo "BUILD FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
  }
}
