pipeline {
    agent any
    
    environment {
        SONAR_SERVER = 'http://172.16.230.171:9000'
    }
    
    stages {
        stage('Example') {
            steps {
                echo "${SONAR_SERVER}"
            }
        }
    }
}