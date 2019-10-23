// 参考：https://houchaowei.github.io/20190605-Jenkins%E8%87%AA%E5%8A%A8%E5%8C%96%E9%83%A8%E7%BD%B2%E4%B9%8B%E7%BC%96%E5%86%99Pipeline%E7%9A%84Groovy%E8%84%9A%E6%9C%AC/

def CDN_DIR = '/srv/dev/react'
node() {
    stage('Checkout'){
        sh "echo PROJECT = ${params.PROJECT}"
        sh "echo INSTALL = ${params.INSTALL}"
        sh "echo ENV = ${params.ENV}"
        sh "echo FORCE = ${params.FORCE}"
        sh "echo INIT = ${params.INIT}"
        sh "echo WORKSPACE = $WORKSPACE"
        sh "echo BUILD_ID = $BUILD_ID"
        sh 'pwd'
        sh "echo BUILD_NUMBER = $BUILD_NUMBER"
        sh "echo JOB_NAME = $JOB_NAME"
        sh "echo JOB_BASE_NAME = $JOB_BASE_NAME"
        sh "echo BUILD_TAG = $BUILD_TAG"
        sh "echo EXECUTOR_NUMBER = $EXECUTOR_NUMBER"
        sh "echo NODE_NAME = $NODE_NAME"
        sh "echo NODE_LABELS = $NODE_LABELS"
        sh "echo JENKINS_HOME = $JENKINS_HOME"
        sh "echo JENKINS_URL = $JENKINS_URL"
        sh "echo BUILD_URL = $BUILD_URL"
        sh "echo JOB_URL = $JOB_URL"
        git branch: 'dev-server', url: 'ssh://git@******/******.git'
        sh 'git status'
        sh 'git branch'
    }

    stage('Initialize'){
      if (params.INSTALL){
        sh "rm -rf node_modules"
        sh "npm i"
      }
    }

    stage('build'){
        sh "npm run build"
    }

    stage('Results') {
      sh "mkdir -p ${WORKSPACE}/archive"
      sh "mkdir -p ${WORKSPACE}/archive/${BUILD_ID}"
      sh "zip -r ${WORKSPACE}/archive/${BUILD_ID}/${JOB_NAME}-${BUILD_ID}.zip ${WORKSPACE}/dist/*"
      archiveArtifacts artifacts: 'archive/**/*.zip', onlyIfSuccessful: true
    }

    stage('Publish') {
        sh "mkdir -p /srv"
        sh "mkdir -p ${CDN_DIR}/${params.PROJECT}"
        sh "cp -r ${WORKSPACE}/dist/. ${CDN_DIR}/${params.PROJECT}/"
    }
}