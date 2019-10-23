```bash
# triggers指令定义了Pipeline自动化触发的方式。
# 对于与源代码集成的Pipeline，如GitHub或BitBucket，triggers可能不需要基于webhook的集成也已经存在。
# 目前只有两个可用的触发器：cron和pollSCM。
```
#### triggers指令
```javascript
pipeline {
    agent any
    
    options {
        timeout(time:1, unit: 'HOURS')
    }
    
    parameters {
        choice(name:'PerformMavenRelease',choices:'False\nTrue',description:'desc')
     //   password(name:'CredsToUse',defaultValue:'',description:'A password to build with')
    }
    
    environment {
        SONAR_SERVER = 'http://172.16.230.171:9000'
        JAVA_HOME='/data/jdk'
    }
    
　　 triggers {
　　　　  cron('H 4/* 0 0 1-5')
    }

    stages {
        stage('sonarserver') {
            steps {
                echo "${SONAR_SERVER}"
            }
        }
        stage('javahome') {
            steps {
                echo "${JAVA_HOME}"
            }
        }
        stage('get parameters') {
            steps {
                echo "${params.PerformMavenRelease}"
            }
        }        
    }
}
```