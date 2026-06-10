pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Create virtual environment') {
      steps {
        sh 'python3 -m venv .venv'
      }
    }

    stage('Install dependencies') {
      steps {
        sh '. .venv/bin/activate && pip install --upgrade pip'
        sh '. .venv/bin/activate && pip install -r requirements.txt'
      }
    }

    stage('Run tests') {
      steps {
        sh '. .venv/bin/activate && pytest'
      }
    }

    stage('Run ETL pipeline') {
      steps {
        sh '. .venv/bin/activate && python main.py'
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'output/*.parquet', allowEmptyArchive: true
    }
  }
}