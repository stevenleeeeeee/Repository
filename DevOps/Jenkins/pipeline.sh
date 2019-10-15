node { 
   // 拉取代码
   stage('Git Checkout') { 
        checkout([$class: 'GitSCM', branches: [[name: '$branch']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '8db1da0a-bcf7-43c5-b98d-a711d6119933', url: 'git@192.168.31.70:/home/git/tomcat-java-demo.git']]])   // 代码编译
   }
   stage('Maven Build') {
        sh '''
        export JAVA_HOME=/usr/local/jdk
        /usr/local/maven/bin/mvn clean package -Dmaven.test.skip=true
        '''
   }
   // 项目打包到镜像并推送到镜像仓库
   stage('Build and Push Image') {
sh '''
REPOSITORY=192.168.31.70/library/tomcat-java-demo:${branch}
cat > Dockerfile << EOF
FROM lizhenliang/tomcat
MAINTAINER www.ctnrs.com
RUN rm -rf /usr/local/tomcat/webapps/*
ADD target/*.war /usr/local/tomcat/webapps/ROOT.war
EOF
docker build -t $REPOSITORY .
docker login 192.168.31.70 -u admin -p Harbor12345
docker push $REPOSITORY
'''
   }
   // 部署到Docker主机
   stage('Deploy to Docker') {
        sh '''
        REPOSITORY=192.168.31.70/library/tomcat-java-demo:${branch}
        docker rm -f tomcat-java-demo |true
        docker pull $REPOSITORY
        docker container run -d --name tomcat-java-demo -p 88:8080 $REPOSITORY
        '''
   }
}