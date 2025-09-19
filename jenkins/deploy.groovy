def downloadSecrets() {

    sh """
        cd /var/jenkins_home/wiseone/secrets
        git pull jenkins main
        cd ${WORKSPACE}
    """
}

def bumpVersion() {

    def versionConfig = load '/var/jenkins_home/wiseone/secrets/backbone-cis/version'
    def version = versionConfig.app_version

    def versionParts = version.split(/\./) as String[]

    def major = versionParts[0].toInteger()
    def minor = versionParts[1].toInteger()
    def patch = versionParts[2].toInteger()

    patch++

    def newVersion = "${major}.${minor}.${patch}"

    sh """
        cat <<EOT > /var/jenkins_home/wiseone/secrets/backbone-cis/version
[
    app_version: "${newVersion}",
    build_number: "${env.BUILD_NUMBER}"
]
"""

    sh """
        cd /var/jenkins_home/wiseone/secrets

        git commit -a -m "Bumped backbone-cis version"
        git push jenkins main

        cd ${WORKSPACE}
    """
    

    return newVersion
}

def build() {

    def version = this.bumpVersion()

    echo "Building backbone-cis app..."

    // Set version number which will be persisted to the actual image
    sh """
        cat <<EOT > ./version.properties
app_version="${version}"
build_number="${env.BUILD_NUMBER}"
"""

    // Build new version
    sh "docker build -f Dockerfile.prod -t wiseoneai/backbone-cis:${version} ."

    // Build as latest?
    sh "docker build -f Dockerfile.prod -t wiseoneai/backbone-cis:latest ."
}

def push() {

    def versionConfig = load '/var/jenkins_home/wiseone/secrets/backbone-cis/version'
    def version = versionConfig.app_version

    echo "Pushing backbone-cis image to DockerHub..."

    // Log in to Docker Hub
    withCredentials([usernamePassword(credentialsId: 'DOCKERHUB', passwordVariable: 'DOCKERHUB_PASSWORD', usernameVariable: 'DOCKERHUB_USERNAME')]) {
        sh "docker login -u ${DOCKERHUB_USERNAME} -p ${DOCKERHUB_PASSWORD}"
    }

    // Push new version image to Docker Hub
    sh "docker push wiseoneai/backbone-cis:${version}"

    // Push as latest
    sh "docker push wiseoneai/backbone-cis:latest"

    // Logout of Docker Hub
    sh 'docker logout'

    //slackSend message: ":white_check_mark: Wiseone.ai A new backbone-cis version has been built and pushed: '${version}'. This new version is now the 'latest'!"
}

def generateConfiguration(environmentName, sequenceId) {   

    // Start the app.yml configuration
    sh "cat /var/jenkins_home/wiseone/secrets/backbone-cis/${environmentName}.yml > app.yml"
    sh 'echo "" >> app.yml'
    sh 'echo "" >> app.yml'

    // Append backbone-database configuration (not needed for now)
    /* sh "cat /var/jenkins_home/wiseone/secrets/backbone-database/${environmentName}.yml >> app.yml"
    sh 'echo "" >> app.yml'
    sh 'echo "" >> app.yml' */

    sh """            
            cat <<EOT >> ./app.yml
nodeInfo:
    env: '${environmentName}'
    id: 'backbone_cis_${sequenceId}'
    name: 'backbone-cis-${sequenceId}'
    sequenceId: ${sequenceId}
"""

    // Generate .env file
    sh "cat /var/jenkins_home/wiseone/secrets/backbone-cis/${environmentName}.env > .env"
}

def deployService(environmentName, sequenceId, publicIp, port, version, testAndNotify, successMessage) {

    def nodeFQDN = this.getNodeFQDN(environmentName, sequenceId)
    
    echo "Deploying ${nodeFQDN} version ${version} on node with IP ${publicIp}"

    // Generate the configuration needed for this deployment
    this.generateConfiguration(environmentName, sequenceId)

    sshagent(['jenkins_rsa']) {

        withCredentials([usernamePassword(credentialsId: 'DOCKERHUB', passwordVariable: 'DOCKERHUB_PASSWORD', usernameVariable: 'DOCKERHUB_USERNAME')]) {

            // Ensure the app directory
            sh """
                ssh -o StrictHostKeyChecking=no root@${publicIp} <<EOT

                mkdir -p app/backbone-cis
                cd app/backbone-cis

            """

            sh """
                scp -o StrictHostKeyChecking=no app.yml root@${publicIp}:/root/app/backbone-cis/app.yml
                scp -o StrictHostKeyChecking=no docker-compose-prod.yml root@${publicIp}:/root/app/backbone-cis/docker-compose.yml
                scp -o StrictHostKeyChecking=no .env root@${publicIp}:/root/app/backbone-cis/.env
                scp -o StrictHostKeyChecking=no /var/jenkins_home/wiseone/secrets/backbone-cis/agent-config.yml root@${publicIp}:/root/app/backbone-cis/agent-config.yml
                scp -o StrictHostKeyChecking=no /var/jenkins_home/wiseone/secrets/backbone-cis/logging-config.yml root@${publicIp}:/root/app/backbone-cis/logging-config.yml

                ssh -o StrictHostKeyChecking=no root@${publicIp} <<EOT

                echo "" >> /root/app/backbone-cis/.env
                echo "APP_VERSION=${version}" >> /root/app/backbone-cis/.env
                echo "PORT=${port}" >> /root/app/backbone-cis/.env

                docker login -u ${DOCKERHUB_USERNAME} -p ${DOCKERHUB_PASSWORD}
                docker pull wiseoneai/backbone-cis:${version}
                docker logout

                cd /root/app/backbone-cis
                docker-compose down
                docker-compose up -d
            """
        }
    }

    // Test
    if(testAndNotify) {
        def testSuccess = this.testService(environmentName, sequenceId, version, 15)

        if(testSuccess == true) {
            //slackSend message: ":white_check_mark: Wiseone.ai Successfully deployed ${environmentName} server: ${nodeFQDN} with version '${version}', build number ${BUILD_NUMBER}!"                                            
        } else {
            //slackSend message: ":x: Wiseone.ai Unable to update ${environmentName} server: ${nodeFQDN} to version '${version}'! I will double check..."

            // Retry test
            if(this.testService(environmentName, sequenceId, version, 15) == true) {
                //slackSend message: ":white_check_mark: Wiseone.ai Successfully deployed ${environmentName} server: ${nodeFQDN} second time around, with version '${version}', build number ${BUILD_NUMBER}!"
            } else {
                //slackSend message: ":x: Wiseone.ai Still unable to get in contact with server: ${nodeFQDN}! Please start a manual investigation as to what might be wrong!"

                currentBuild.result = 'ABORTED'
                error("ERROR: Wiseone.ai ${environmentName} ${nodeFQDN} was deployed, but does not respond with a valid response code or version number!")
            }
            
        }
    }
}

def testService(environmentName, sequenceId, version, delay) {
    return this.testService(environmentName, sequenceId, version, delay, "https")
}

def testService(environmentName, sequenceId, version, delay, protocol) {

    def nodeFQDN = this.getNodeFQDN(environmentName, sequenceId)

    if(version == "latest") {
        def versionConfig = load '/var/jenkins_home/wiseone/secrets/backbone-cis/version'
        version = versionConfig.app_version
    }

    // Default the protocol to https
    if(protocol == "" || protocol == null) {
        protocol = "https"
    }
    
    if(delay) {
        echo "Waiting for ${nodeFQDN} docker container to spin up..."
        sleep delay
    }

    def response = httpRequest url: "${protocol}://${nodeFQDN}/version", validResponseCodes: "100:599"
    println("Status: "+response.status)
    println("Content: "+response.content)

    if(response.status == 200 && response.content.contains(version)) {
        return true
    }

    return false
}

def deployAllServices(environmentName, nodeSequenceId, version, successMessage) {

    def config = load "/var/jenkins_home/wiseone/secrets/backbone-cis/config.groovy"
    def nodesConfig = config.nodes

    echo "Initiated backbone-cis deployment of node '${nodeSequenceId}' in ${environmentName}"
    
    def nodesList = nodesConfig[environmentName]    
    
    nodesList.each { serverNode ->

        def sequenceId = serverNode.key
        def nodeIPs = serverNode.value

        if(nodeSequenceId == "all" || nodeSequenceId == "${sequenceId}") {
            // Deploy
            echo "Deploying ${environmentName} node ${sequenceId} with IP: ${nodeIPs.public_ip}"

            this.deployService(environmentName, sequenceId, nodeIPs.public_ip, config.port, version, false, successMessage)
        }
        
    }

    if(nodeSequenceId == "all") {
        //slackSend message: ":white_check_mark: Wiseone.ai Successfully deployed all ${environmentName} backbone-cis servers with version '${version}'!"
    }
}

def getNodeFQDN(environmentName, nodeSequenceId) {

    def nodeFQDN = "backbone-cis-${nodeSequenceId}.wiseone.ai"

    if(environmentName == "staging") {
        nodeFQDN = "backbone-cis-staging-${nodeSequenceId}.wiseone.ai"
    }

    return nodeFQDN
}

return this