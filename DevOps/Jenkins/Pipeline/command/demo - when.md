```bash
# 内置条件: （ when 仅用于stage内部 ）
# branch
# 　　当正在构建的分支与给出的分支模式匹配时执行，例如：when { branch 'master' }。请注意，这仅适用于多分支Pipeline

# environment
# 　　当指定的环境变量设置为给定值时执行，例如： when { environment name: 'DEPLOY_TO', value: 'production' }

# expression
# 　　当指定的Groovy表达式求值为true时执行，例如： when { expression { return params.DEBUG_BUILD } }

# not
# 　　当嵌套条件为false时执行。必须包含一个条件。例如：when { not { branch 'master' } }

# allOf
# 　　当所有嵌套条件都为真时执行。必须至少包含一个条件。例如：when { allOf { branch 'master'; environment name: 'DEPLOY_TO', value: 'production' } }

# anyOf
# 　　当至少一个嵌套条件为真时执行。必须至少包含一个条件。例如：when { anyOf { branch 'master'; branch 'staging' } }
```
#### when 指令
```javascript
pipeline {
    agent any
    stages {
        stage('Example Build') {
            steps {
                echo 'Hello World'
            }
        }
        stage('Example Deploy') {
            when {                                   < ---------------------------
                allOf {
                    branch 'production'
                    environment name: 'DEPLOY_TO', value: 'production'
                }
            }
            steps {
                echo 'Deploying'
            }
        }
    }
}
```
#### when 指令 2
```javascript
Jenkinsfile(Declarative Pipeline) pipeline {
    agent any stages {
        stage('Example Build') {
            steps {
                echo 'Hello World'
            }
        }
        stage('Example Deploy') {
            when {
                branch 'production'
            }
            steps {
                echo 'Deploying'
            }
        }
    }
}
Jenkinsfile(Declarative Pipeline) pipeline {
    agent any stages {
        stage('Example Build') {
            steps {
                echo 'Hello World'
            }
        }
        stage('Example Deploy') {
            when {
                branch 'production'environment name: 'DEPLOY_TO',
                value: 'production'
            }
            steps {
                echo 'Deploying'
            }
        }
    }
}
Jenkinsfile(Declarative Pipeline) pipeline {
    agent any stages {
        stage('Example Build') {
            steps {
                echo 'Hello World'
            }
        }
        stage('Example Deploy') {
            when {
                allOf {
                    branch 'production'environment name: 'DEPLOY_TO',
                    value: 'production'
                }
            }
            steps {
                echo 'Deploying'
            }
        }
    }
}
Jenkinsfile(Declarative Pipeline) pipeline {
    agent any stages {
        stage('Example Build') {
            steps {
                echo 'Hello World'
            }
        }
        stage('Example Deploy') {
            when {
                branch 'production'anyOf {
                    environment name: 'DEPLOY_TO',
                    value: 'production'environment name: 'DEPLOY_TO',
                    value: 'staging'
                }
            }
            steps {
                echo 'Deploying'
            }
        }
    }
}
Jenkinsfile(Declarative Pipeline) pipeline {
    agent any stages {
        stage('Example Build') {
            steps {
                echo 'Hello World'
            }
        }
        stage('Example Deploy') {
            when {
                expression {
                    BRANCH_NAME == ~ / (production | staging) /
                }
                anyOf {
                    environment name: 'DEPLOY_TO',
                    value: 'production'environment name: 'DEPLOY_TO',
                    value: 'staging'
                }
            }
            steps {
                echo 'Deploying'
            }
        }
    }
}
```