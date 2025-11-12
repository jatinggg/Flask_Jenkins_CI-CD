pipeline {
  agent any

  parameters {
    string(name: 'DEPLOY_HOST', defaultValue: '18.170.47.136', description: 'EC2 host for deployment (ip or dns)')
    string(name: 'NOTIFY_EMAIL', defaultValue: 'deepika2.ytb@gmail.com', description: 'Email to notify on build status')
  }

  environment {
    DEPLOY_USER = "ubuntu"
    DEPLOY_TARGET_BASE = "/var/www/html"
    SSH_CRED_ID = "ec2-ssh-key"     // folder-scoped SSH Username with private key credential id
    GITHUB_CRED_ID = "github-token"  // global secret text with GitHub PAT (for status updates if configured)
  }

  options {
    skipStagesAfterUnstable()
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '30'))
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        echo "Checked out branch: ${env.BRANCH_NAME} (commit: ${env.GIT_COMMIT ?: 'unknown'})"
      }
    }

    stage('Build') {
      steps {
        sh label: 'Create venv & install deps', script: """
          bash -lc 'set -euo pipefail
          python3 -m venv .venv || true
          . .venv/bin/activate
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          deactivate'
        """
      }
    }

    stage('Test') {
      steps {
        sh label: 'Run pytest (if present)', script: """
          bash -lc 'set -euo pipefail
          if [ -d .venv ]; then . .venv/bin/activate; fi
          if [ -d tests ] || ls test_*.py >/dev/null 2>&1; then
            pytest -q || (echo "Pytest failed" && exit 1)
          else
            echo "No tests found - skipping pytest"
          fi
          if [ -d .venv ]; then deactivate; fi'
        """
      }
    }

    stage('Package') {
      steps {
        script {
          // Use git archive for a stable snapshot (recommended)
          def rc = sh(script: """
            bash -lc 'set -euo pipefail
            rm -f build.tar.gz || true
            if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
              git archive --format=tar HEAD | gzip > build.tar.gz
            else
              tar --warning=no-file-changed -czf build.tar.gz --exclude=".venv" --exclude=".git" .
            fi
            ls -lh build.tar.gz
            '
          """, returnStatus: true)
          if (rc != 0) {
            error "Packaging failed with rc=${rc}"
          }
        }
        archiveArtifacts artifacts: 'build.tar.gz', fingerprint: true
      }
    }

    stage('Deploy') {
      when {
        anyOf { branch 'staging'; branch 'main' }
      }
      steps {
        script {
          env.APP_ENV = (env.BRANCH_NAME == 'main') ? "production" : "staging"
          env.TARGET_DIR = (env.BRANCH_NAME == 'main') ? "${env.DEPLOY_TARGET_BASE}" : "${env.DEPLOY_TARGET_BASE}/staging"
          echo "Deploying branch '${env.BRANCH_NAME}' -> ${env.TARGET_DIR} (APP_ENV=${env.APP_ENV})"
        }

        withCredentials([sshUserPrivateKey(credentialsId: "${env.SSH_CRED_ID}",
                                          keyFileVariable: 'SSH_KEY_FILE',
                                          usernameVariable: 'SSH_USER')]) {
          sh label: 'Upload and deploy to EC2', script: """
            bash -lc 'set -euo pipefail
            REMOTE=\"${SSH_USER}@${params.DEPLOY_HOST}\"
            KEY=\"${SSH_KEY_FILE}\"
            BUILD=\"build.tar.gz\"
            REMOTE_TMP=\"/home/${SSH_USER}/build.tar.gz\"
            TARGET_DIR=\"${env.TARGET_DIR}\"
            DEPLOY_BASE=\"${env.DEPLOY_TARGET_BASE}\"

            # ensure base exists and is owned by the deploy user
            ssh -o BatchMode=yes -o StrictHostKeyChecking=no -i \"${KEY}\" \"${REMOTE}\" \\
              \"sudo mkdir -p '${DEPLOY_BASE}' && sudo chown ${SSH_USER}:${SSH_USER} '${DEPLOY_BASE}'\"

            # copy artifact
            scp -o BatchMode=yes -o StrictHostKeyChecking=no -i \"${KEY}\" \"${BUILD}\" \"${REMOTE}:\${REMOTE_TMP}\"

            # extract, write env file and restart services
            ssh -o BatchMode=yes -o StrictHostKeyChecking=no -i \"${KEY}\" \"${REMOTE}\" bash -lc \\
              \"sudo mkdir -p \\\"\\\${TARGET_DIR}\\\" \\
               && sudo tar -xzf \\\"\\\${REMOTE_TMP}\\\" -C \\\"\\\${TARGET_DIR}\\\" --strip-components=0 \\
               && echo APP_ENV=${env.APP_ENV} | sudo tee \\\"\\\${TARGET_DIR}/.env\\\" >/dev/null \\
               && sudo chown -R ${SSH_USER}:www-data \\\"\\\${TARGET_DIR}\\\" \\
               && if sudo systemctl list-unit-files | grep -q '^flaskapp.service'; then sudo systemctl daemon-reload || true; sudo systemctl restart flaskapp || true; fi \\
               && sudo systemctl restart nginx || true\"

            echo "Deploy finished."
            '
          """
        }
      }
    }
  }

  post {
    success {
      echo "BUILD SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER} (branch: ${env.BRANCH_NAME})"
      // Send success email
      emailext (
        to: "${params.NOTIFY_EMAIL}",
        subject: "SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER} (${env.BRANCH_NAME})",
        body: """Build successful.

Job: ${env.JOB_NAME}
Build: ${env.BUILD_NUMBER}
Branch: ${env.BRANCH_NAME}
Commit: ${env.GIT_COMMIT ?: 'N/A'}
URL: ${env.BUILD_URL}
"""
      )
    }
    failure {
      echo "BUILD FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER} (branch: ${env.BRANCH_NAME})"
      // Send failure email with console link
      emailext (
        to: "${params.NOTIFY_EMAIL}",
        subject: "FAIL: ${env.JOB_NAME} #${env.BUILD_NUMBER} (${env.BRANCH_NAME})",
        body: """Build failed.

Job: ${env.JOB_NAME}
Build: ${env.BUILD_NUMBER}
Branch: ${env.BRANCH_NAME}
Commit: ${env.GIT_COMMIT ?: 'N/A'}
Console: ${env.BUILD_URL}console
"""
      )
    }
    cleanup {
      sh 'rm -f build.tar.gz || true'
    }
  }
}

