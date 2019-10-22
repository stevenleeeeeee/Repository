```bash
# script步骤需要一个script Pipeline，并在声明性Pipeline中执行
# 对于大多数场景，声明Pipeline中的script步骤不是必须的，但它可以提供一个有用的“escape hatch”
# 量大的或者复杂的script块应该转移到共享库中
# Scripted Pipeline是一个基于Groovy构建的，通用、高效的DSL。
# 由Groovy语言提供的大多数功能都提供给Scripted Pipeline的用户，这意味着它是一个非常富有表现力和灵活性的工具
# 可以通过这些工具来创建持续构建的Pipeline
```
#### script 指令
```js
Jenkinsfile(Declarative Pipeline) pipeline {
    agent any stages {
        stage('Example') {
            steps {
                echo 'Hello World'

                script {
                    def browsers = ['chrome', 'firefox']
                    for (int i = 0; i < browsers.size(); ++i) {
                        echo "Testing the ${browsers[i]} browser"
                    }
                }

            }
        }
    }
}

// Scripted Pipeline从顶部顺序执行，与Jenkinsfile Groovy或其他语言中的大多数传统Scripted一样。
// 因此，提供流量控制取决于Groovy表达式，例如 if/else条件，例如：
Jenkinsfile(Scripted Pipeline) node {
    stage('Example') {
        if (env.BRANCH_NAME == 'master') {
            echo 'I only execute on the master branch'
        } else {
            echo 'I execute elsewhere'
        }
    }
}

// 可以管理Scripted Pipeline流控制的另一种方式是使用Groovy的异常处理支持。
// 当步骤由于任何原因而导致异常时。处理错误行为必须使用Groovy 中的try/catch/finally块，例如：
Jenkinsfile(Scripted Pipeline) node {
    stage('Example') {
        try {
            sh 'exit 1'
        } catch(exc) {
            echo 'Something failed, I should sound the klaxons!'
            throw
        }
    }
}
```
