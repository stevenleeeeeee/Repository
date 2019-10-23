```bash
# 参考：
# https://www.cnblogs.com/111testing/p/9721424.html
# https://www.jianshu.com/p/7a852d58d9a9

# pipeline 是一套运行于jenkins上的工作流框架
# 将原本独立运行于单个或多个节点的任务连接起来，实现单个任务难以完成的复杂流程编排与可视化。
# 是jenkins2.X最核心的特性，帮助jenkins实现从CI到CD与DevOps的转变

# 为什么使用Pipeline?:
# 1.代码:     以代码形式实现（pipeline脚本由groovy语言实现），通过被捡入源代码控制使团队能编译、审查和迭代其cd流程
# 2 可连续性: Jenkins重启或中断后都不会影响pipeline job
# 3.停顿:     可以选择停止并等待人工输入或者批准，然后在继续pipeline运行
# 4.多功能:   支持现实世界的复杂CD要求，包括fork、join子进程，循环和并行执行工作的能力
# 5.可扩展:   插件支持其DSL的自动扩展以及其插件集成的多个选项

# pipeline 支持两种语法
# 1.声明式: Declarative 
# 2.脚本式: Scripted pipeline 
```
#### Declarativ ( 声明式 pipeline )
```bash
# 声明式pipeline基本语法和表达式遵循groovy语法，但有以下例外：
# - 声明式pipeline必须包含在固定格式的 pipeline{} 块内
# - 每个声明语句必须独立一行，行尾无需使用分号
# - 块 "Blocks{}" 只能包含章节(Sections)、指令（Directives）、步骤(Steps)、或赋值语句
# - 属性引用语句被视为无参数方法调用。如: input()

# 块： Blocks{}
# - 由大括号括起来的语句： 如：Pipeline{}, Sections{}, parameters{}, script{}

# 章节：Sections
# - 通常包括一或多个指令或步骤、如：agent、post、stages、steps

# 指令：Directives
# - environment、options、 parameters、triggers、stage、tools、when

# 步骤：steps
# - 执行脚本式pipeline、如：script{}
```
#### Example for pipeline 
```js
Jenkinsfile (Declarative Pipeline)

pipeline {

    // 在任何可用的代理上执行流水线或阶段
    agent any 
    // 在提供了标签的 Jenkins 环境中可用的代理上执行流水线或阶段。例如: agent { label 'my-defined-label' }
    
    options {
        // 设置构建超时时间为1小时
        timeout(time:1, unit: 'HOURS')
        skipStagesAfterUnstable()
        buildDiscarder(logRotator(numToKeepStr: '5'))
        preserveStashes(5)
        retry(2)
    }

    parameters {

        // 定义参数化构建的参数（下列选项设置将在Jenkins的 Build with Parameters）
        choice(name:'PerformMavenRelease',choices:'False\nTrue',description:'desc')
        // password(name:'CredsToUse',defaultValue:'',description:'A password to build with')
        // string(name: 'DEPLOY_ENV', defaultValue: 'staging', description: '')
        // text(name: 'DEPLOY_TEXT', defaultValue: 'One\nTwo\nThree\n', description: '')
        // booleanParam(name: 'DEBUG_BUILD', defaultValue: true, description: '')
        // choice(name: 'CHOICES', choices: ['one', 'two', 'three'], description: '')
        // file(name: 'FILE', description: 'Some file to upload')

    }

    environment {
        SONAR_SERVER = 'http://xx.xx.xx.xx:9000'
        JAVA_HOME='/data/jdk'
    }    

    // 包含一系列一个或多个stage指令, stages部分是流水线描述的大部分"work"的位置
    // 建议stages至少包含一个stage指令用于连续交付过程的每个离散部分
    stages {
        stage('Example Build') {
            agent { 
                docker 'maven:3-alpine'     // 使用镜像在一个新建的容器中执行下面阶段的步骤
            } 
            steps {         // steps部分必须包含一个或多个步骤
                echo "${SONAR_SERVER}"
                echo "${JAVA_HOME}"
                echo "Hello ${params.DEPLOY_ENV}"
                echo "${params.PerformMavenRelease}"
                sh 'mvn --version' 
            } 
        } 
        stage('Example Test') {
            environment {   // 在一个 stage 中定义的 environment 指令只会将给定的环境变量应用于 stage 中的步骤
                AN_ACCESS_KEY = credentials('my-prefined-secret-text') 
            }
            agent { 
                node {
                    label 'my-defined-label'
                    customWorkspace '/some/other/path'
                }
            } 
            steps {
                echo 'Hello, JDK' sh 'java -version' 
            } 
        }
        stage('Example Deploy') {
            when {
                allOf {
                    branch 'production'
                    environment name: 'DEPLOY_TO', value: 'production'
                }
            }
            steps {
                echo 'Deploying'
            }
        } 
        stage() {
               script {     // 执行groovy脚本....
                    switch(env.JOB_NAME)
                    {
                        case "pipeline1":
                            url = 'git@url1.git'
                            branch = 'release'
                            break
                        case "pipeline2":
                            url = 'git@url2.git'
                            branch = 'master'
                            break
                        default:
                            echo "############ wrong pipeline name ############"
                            break
                    }
            }
        }
        stage('My test') {
            sh '''
            this is some bash commands .....
            '''
        }
    }

    stages {
        stage('Example') {
            input { 
                message "Should we continue?" 
                ok "Yes, we should." 
                submitter "alice,bob" 
                parameters {
                    string(name: 'PERSON', defaultValue: 'Mr Jenkins', description: 'Who should I say hello to?') 
                } 
            } 
            
            steps { 
                echo "Hello, ${PERSON}, nice to meet you." 
            } 
        } 
    }

    post {
        always {
            echo 'I will always say Hello again!' 
        }
    }
}

```