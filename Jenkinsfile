def defaultBobImage = 'armdocker.rnd.ericsson.se/sandbox/adp-staging/adp-cicd/bob.2.0:1.5.2-0'
def bob = new BobCommand()
        .bobImage(defaultBobImage)
        .needDockerSocket(true)
        .toString()
def GIT_COMMITTER_NAME = 'lciadm100'
def GIT_COMMITTER_EMAIL = 'lciadm100@ericsson.com'
def failedStage = ''
def ruleset = 'ruleset2.0.yaml'
if(params.RELEASE=="true") {
    ruleset = 'ruleset.release2.0.yaml'
}

pipeline {
    agent {
        node {
            label 'Cloud-Native'
        }
    }
    options {
        timestamps()
        timeout(time: 1, unit: 'HOURS')
    }
    stages {
        stage('Inject Credential Files') {
            steps {
                withCredentials([file(credentialsId: 'lciadm100-docker-auth', variable: 'dockerConfig')]) {
                    sh "install -m 600 ${dockerConfig} ${HOME}/.docker/config.json"
                }
            }
        }
        stage('Prepare kubectl') {
          steps {
                writeFile file: '/tmp/kube.admin.conf', text: '''apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUZ5RENDQTdDZ0F3SUJBZ0lSQU9uSXdMZ1V0dnhCaDgyTTFnMVdMRWN3RFFZSktvWklodmNOQVFFTEJRQXcKYlRFTE1Ba0dBMVVFQmhNQ1UwVXhFakFRQmdOVkJBZ01DVk4wYjJOcmFHOXNiVEVTTUJBR0ExVUVCd3dKVTNSdgpZMnRvYjJ4dE1SRXdEd1lEVlFRS0RBaEZjbWxqYzNOdmJqRU5NQXNHQTFVRUN3d0VRMDVFUlRFVU1CSUdBMVVFCkF3d0xSVmRUSUZKdmIzUWdRMEV3SGhjTk1qQXdOVEUzTWpBek9UQTRXaGNOTkRVd05URXhNakF6T1RBNFdqQnQKTVFzd0NRWURWUVFHRXdKVFJURVNNQkFHQTFVRUNBd0pVM1J2WTJ0b2IyeHRNUkl3RUFZRFZRUUhEQWxUZEc5agphMmh2YkcweEVUQVBCZ05WQkFvTUNFVnlhV056YzI5dU1RMHdDd1lEVlFRTERBUkRUa1JGTVJRd0VnWURWUVFECkRBdEZWMU1nVW05dmRDQkRRVENDQWlJd0RRWUpLb1pJaHZjTkFRRUJCUUFEZ2dJUEFEQ0NBZ29DZ2dJQkFNQ2kKbDluczczYW9Cam9oRzhaSDlZeVhWNWQ4UUw5ZmlGRC96MThCcU9ZTGZtVFBlM01zMHJrcmdkUUJIMUdib1hNQwpJbzJoVFFERi9sMzJXWFlWcXpPU3BvUzhNdkR2MFNaRGFUNW1QeWdQZVozSU5ndmZwNldnZnV2VE9MUG1sWEY5CnRCaXdQSU9iMGh3RkxtOVQrTW5ISW5mbG0wZGJxYXhxT2ZsQ3ltbDBkSCtiQ1l3WmxKa1VXUXI1SThyUUxtN1MKSzBneXFYMHE1VTR5NTF6TnpZRlZmWWZFSGNTbDBnZEN3ekhOaDc0ekl4aktQRmxBbVNNVTRES1hURXBqdDQzTgpZR0tYUk9DWUtkZmlzVWRGQlhVTnhkNzVGMXNwWEVBblZUMlVVWk1ZelhidzRxR2NzUDhpUFVrUXBJUEU5aG16CllJMUpJOUVvaWJnajNOV0hxMGdzRTJIdUdOdDFoeVhpVmhGTytuYkw0L21iY250OUxuT2sra0txZXNlZVNSd08KLzVqTFJITTY4MVptdUwrTXFaSm4zR2FyY2xqNzRWMFVrbFc5ZUU0a3NTeVEzQ1hrN24vWWlBUXpTUWZkV0wwWgpWTHpiTkxEdC93QzVPRXBuUG5DbnhYUXJzVzlQRnlGeDNoWkV1a3FFMENzY0drK1NCL1R6YXNrb1pvTU0xV3JDCndITXEzNUxnN1BJWW9UNTZXaHFJeHFRSzBrNitBbkJORUc0d043ODdVOUlsbW1WdHlzdjFDbkVrMW5oU3A0MjgKSjBnWUZKZDltNUdGU3BIYk44NDE2OVRiZjlXNVBkMVV4andVc2JHMlVvOWkyQWZZYkxrYVZ4OVUvcHhtZmpkVwpYVnpPbjZCQ0liUlFjaVpSeVp2czE0ak1vaElOclBIYVRYOTM0VnJWQWdNQkFBR2pZekJoTUE4R0ExVWRFd0VCCi93UUZNQU1CQWY4d0RnWURWUjBQQVFIL0JBUURBZ0dHTUIwR0ExVWREZ1FXQkJSYmRqU1JLdlJxcW12NG8zM3kKVDk3ay9TQkkvREFmQmdOVkhTTUVHREFXZ0JSYmRqU1JLdlJxcW12NG8zM3lUOTdrL1NCSS9EQU5CZ2txaGtpRwo5dzBCQVFzRkFBT0NBZ0VBb2RHMzFjQUxQRzVOUkZkSVZMc2hOK2EyQzcyQVk4WnNVSEx6OERHOEpqb3ZVQ1VwCjlRL3NOSnB3eVY4WGtiTG91Wjh2WUdFRms3RUFzYWRIdkRDa0dqZ0lPVFI4NnlGdlJxbFkraVZ6Q2xYd0xpMlQKYWFodTQ4QnV0bVhqQlU4WjIxQkNySUF4aTg4Z01aUVQ3dkl0eHN4WG1iU1NmZHhFdDh1ek9ESUxEV0twU2lVagpEUzZmbmNCN1psNUlGWk9tbVhSaERieHEwbFl3RlZxOEQ5RXQ3QTM4UmhHUzQ3SVJXRTZDeFBNdldvSkREYjRKCkxKcmdVU0JEZWUrY0VwMUtQS1BwcUZpVjV1TE5hV2JJK1NaQkZnLzkwbTk5WlAxZWIxd0dhMmE2NjZCN2xnTVAKT2Z1S1llT1IySU9UclptQWJiTXMrOEthV2lHNHFlakFzaHROMDRQcDdEN2djdXJ5VTJlSGZKS0ZHeGhsMkNzbQpYQXFRdmMzM1NtN2xiVDN6VFlZUEphWXR6N1ZZMXNNL29vc1ozdk9JTGloVDZvYnJZeENRWElHeUpIMEFvSDg2CmJrSzNhSE9aWW5qS0dhaEZXb2xmcFdKeXpSaVZ1KytwQVpaVXU2VjJQM2RUakI3TVlOTG1LQmFlZnJRbVhNT1YKdEUxQnVFKy9yalNSNzhuTEc4a3dyVk1xZkxyRHRsK1JxcE9ET0oxdnpONHRxKzM2dTNHMnRJVEdoVTh1SlJPMApieS9QVGxMaFc5TUd4SWwzSTk3a2xZT2dMSXpVdWh4a3ZCZXgvUDVaMk1NaHJxS0N2TW9RZ1ZVclFjWHlYcGF6CjMyVVNKK1dYTzc5Ty83WVExM2lpTnlXQWZQQlBtWXpRR2k3OGVlR1dtWkc2L01ReHliTjJkL1AyMXFBPQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCi0tLS0tQkVHSU4gQ0VSVElGSUNBVEUtLS0tLQpNSUlFeWpDQ0FyS2dBd0lCQWdJUkFPbkl3TGdVdHZ4Qmg4Mk0xZzFXTEVnd0RRWUpLb1pJaHZjTkFRRUxCUUF3CmJURUxNQWtHQTFVRUJoTUNVMFV4RWpBUUJnTlZCQWdNQ1ZOMGIyTnJhRzlzYlRFU01CQUdBMVVFQnd3SlUzUnYKWTJ0b2IyeHRNUkV3RHdZRFZRUUtEQWhGY21samMzTnZiakVOTUFzR0ExVUVDd3dFUTA1RVJURVVNQklHQTFVRQpBd3dMUlZkVElGSnZiM1FnUTBFd0hoY05NakF3TlRFNE1ETTFNakl6V2hjTk16QXdOVEUyTURNMU1qSXpXakJzCk1Rc3dDUVlEVlFRR0V3SlRSVEVTTUJBR0ExVUVDQXdKVTNSdlkydG9iMnh0TVJJd0VBWURWUVFIREFsVGRHOWoKYTJodmJHMHhFVEFQQmdOVkJBb01DRVZ5YVdOemMyOXVNUTB3Q3dZRFZRUUxEQVJEVGtSRk1STXdFUVlEVlFRRApEQXByZFdKbGNtNWxkR1Z6TUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF2NWdhClhaR2hvVSs5MXFNUmp6aXdGWTNFeUZXZEpzbE1Yb1ZWbHdKSEkza09EWFZVcTJUNEhSd3N4cnUzeEVtVkcvQkcKMWpWcGFPR0JlWUMzNEhjeERvNVh3RURIazMvV0QyYmtxTllwUEswU3BBMXk1cUEzS2FGOUxCM05rRUdQU0tCZgphSUVOUVptV3pNN2RuZUtPM1p0V3RGUEZkeWF4WEp2d0kwaHR2cy81eExCM2tMWHZOdkRrRjVRQ0NIdXAxUU5kCmlBb3dmMnlQWmsyN3pmN1JiYysxUDlvZjcwRG5RY2k0T1A1K2g5Qis0cEJNamJ3MVRDQ1N0SE9LUzBEOForL0UKbFR0bUN0ajVTRVhodFJnd2JXQVhaNStyb1lhTnBjRjRVbVJ1TmNSWFlVSzhGOUtnOGFYYi94all6cUQ1c3dRRgp2TFAwZ1hmRUJMdVgycC9GU1FJREFRQUJvMll3WkRBU0JnTlZIUk1CQWY4RUNEQUdBUUgvQWdFQU1BNEdBMVVkCkR3RUIvd1FFQXdJQmhqQWRCZ05WSFE0RUZnUVVBUFgycHV1SXpvT012THhlNWJud1djaUE4dFF3SHdZRFZSMGoKQkJnd0ZvQVVXM1kwa1NyMGFxcHIrS045OGsvZTVQMGdTUHd3RFFZSktvWklodmNOQVFFTEJRQURnZ0lCQUF0cgpHbW1zcldvMFRmNUtPOU9JcEo0dlNLdEZNTUR6VWEvOEVIZHg4WG1TbXZxS2YrajE2TXg0cUFwaUE2ZHR4ODlJCjdSMlkrd2pKWWlMOGV0c2tQVGlLdGNuV0JDNEJzNUpZNTFsblhjenFnbG91cE5hTnNRV0FTOEZySldwU0xMU0kKTkU0anhEY1ZyajBuaG1KeEVUZ3FkSmRPVTByK2FtMXFmeHNKQ0dNa0tMVTgxaE12UHRnWFUrK01oVjVwOXhaQgpLdklLVHlHbnlGWnpUZ3BEWXdxU3doSTRhRmNieG1qcGkwMUtiaHFXZWJNSjVzOFVZZFFZSm4weWxSd2NzMTB5Cjd2MEQvcEhmREVRSzFFVnNhd0haTlZVaW9kRWw1VUFuTzBudWcwWDlzeFJmeGNQRmtOSmMwUk1UMFVJRFlWMnAKMnluM2pCZkZlWVhDazdiZURzVmpyZEw5NkR2aHd3V3UxNmpTZWlNc2lWdUpHYzZWNHRkZEF0VUVxenJFOGZwaApHS2F2eXh2dVJsemFPMnJURkw2ZUdSWkhtaWwrQ04vQ0sraWNRQWF4WWZmWnl6YVUwbUVydEtpUnlDOW93RUFOClAzc0trSS93RGJibmxkeHE5Wnp6Q0plclNFcFdHUi9HVExqR0t4cFV2NGRSR1RtWXVOZjU1ZVU4Zzk5YXdrdnMKTHc3SlFZeng3bVpacnVxclNQS3QrVHZCSkp2M0hMbVlTY09FTlk3VUJvMTliWTl1bFVnSHpGaDFtUVRDaCtmNgpiSUY3RUF5eGtnb2ZVeXVpbWQwVTJHaTZjd2ZPbGdFUFkzWW5oTVdxUExFMlhmbG5Hbk9pN1h1VFFDWFl2bGF1CktUQ28vZVJhcmQ1ZGNlSzZkb3A4NklhRFNpWEZiSVZlTnRPcHI1bnkKLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
    server: https://hahn183.k8s.gic.ericsson.se:6443
  name: hahn183
contexts:
- context:
    cluster: hahn183
    user: aispinn
  name: aispinn@hahn183
current-context: aispinn@hahn183
kind: Config
preferences: {}
users:
- name: aispinn
  user:
    token: eyJhbGciOiJSUzI1NiIsImtpZCI6IjZpZVhQWFVUNXhYaG1qdk5iM09BbWx1VHNaTF9ScGtacXBIaTdjaTI5dUEifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhaXNwaW5uLXRva2VuIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFpc3Bpbm4iLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiI4NTc5MjU5My00MjAxLTRhOTEtYmIyYS1mZDA1ZjgxOTU4NWEiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06YWlzcGlubiJ9.jCMawA7gYYkTpIMYk4f6UDc_OdiBABAUI4n6de--4rW1mppTYp0tzhB2TmTMstv23sVixli6miEYArXzC69EgA0wPXmdoyerpkC43rFnDxMMUiqE5F-TAJWMoWK4CDGxaIgfvL6gfB-EebmZmkJkZVbn-oVeeed4RpiG9vmtZdOcEgzWViz7IVFygSOM7TcNed7v5uElTjlZjVb8pCQt-udpZ4eicazqFztBWh2eu6xlFcM65orKRatxEzunwDrmu8nUE5APaDlGZjJZ3xsJW25nv3ssZ7kJPmgFt3Furk8QW76OzxTNrpVAwuG7b66YxB-5dvzlUnHotZOV12TiOA
'''
          }
        }
        stage('Prepare bob') {
            steps {
                sh 'git clean -xdff --exclude=.m2 --exclude=settings.xml'
                sh 'git submodule sync'
                sh 'git submodule update --init --recursive'
            }
        }
        stage('Bob Lint') {
             when { expression { (params.RELEASE!="true") } }
             steps {
                sh "${bob} -r ${ruleset} lint"
            }
        }
        stage('Helm Design Rules check') {
             when { expression { (params.RELEASE!="true") } }
             steps {
                 sh "${bob} -r ${ruleset} check-helm-dr || true"
             }
        }
        stage('Maven build ReplicaSync jars') {
             steps {
                 sh "${bob} -r ${ruleset} build-bragent-replica-sync"
             }
        }
        stage('Build Docker Image & Helm Chart') {
            steps {
                sh "${bob} -r ${ruleset} image"
            }
            post {
                failure {
                    sh "${bob} -r ${ruleset} remove-images"
                }
            }
        }
        stage('Push Docker Image & Helm Charts') {
            steps {
                sh "${bob} -r ${ruleset} push"
            }
            post {
                always {
                    sh "${bob} -r ${ruleset} remove-images"
                }
            }
        }
        stage('Grype Scan') {
            when { expression { (params.RELEASE!="true") } }
            steps {
                echo 'Running Grype Scan'
                sh "${bob} -r ${ruleset} grype-scan"
            }
        }
        stage('Trivy Scan') {
            when { expression { (params.RELEASE!="true") } }
            steps {
                echo 'Running Trivy Scan'
                sh "${bob} -r ${ruleset} trivy-inline-scan"
            }
        }
        stage('Xray Scan') {
            when { expression { (params.RELEASE!="true") } }
            steps {
                echo 'Fetching Xray Report'
                sh "${bob} -r ${ruleset} fetch-xray-report"
            }
        }
        stage('Generate VA Report') {
            when { expression { (params.RELEASE!="true") } }
            steps {
                script {
                    try {
                        sh "${bob} -r ${ruleset} generate-VA-report"
                        archiveArtifacts 'build/html/html-va-report/Vulnerability_Report.html'
                        publishHTML (target: [
                            allowMissing: false,
                            alwaysLinkToLastBuild: false,
                            keepAll: true,
                            reportDir: 'build/html/html-va-report/',
                            reportFiles: 'Vulnerability_Report.html',
                            reportName: "Full VA Scan Report"
                        ])
                    } catch (err) {
                        echo err.getMessage()
                    }
                }
            }
        }
        stage('Test Deploy') {
            when { expression { (params.RELEASE!="true") } }
            steps {
                echo 'Deploying....'
                sh "export KUBECONFIG=/tmp/kube.admin.conf && ${bob} -r ${ruleset} test-deployment"
            }
            post {
                always {
                    sh "mv output.html test_deploy_output.html"
                    sh "mv testdeploy.log test_deploy.log"
                    archiveArtifacts 'test_deploy_output.html'
                    archiveArtifacts 'test_deploy.log'
                }
            }
        }
        stage('BUR Test') {
            when { expression { (params.RELEASE!="true") } }
            steps {
                echo 'Starting BUR Test....'
                sh "export KUBECONFIG=/tmp/kube.admin.conf && ${bob} -r ${ruleset} bur-test"
            }
            post {
                failure {
                    script {
                        failedStage = env.STAGE_NAME
                    }
                }
                always {
                    sh "mv testdeploy.log bur_test.log"
                    archiveArtifacts 'bur_test_output.html'
                    archiveArtifacts 'bur_test.log'
                }
            }
        }
    }
}
// More about @Builder: http://mrhaki.blogspot.com/2014/05/groovy-goodness-use-builder-ast.html
import groovy.transform.builder.Builder
import groovy.transform.builder.SimpleStrategy
@Builder(builderStrategy = SimpleStrategy, prefix = '')
class BobCommand {
    def bobImage = 'bob.2.0:latest'
    def envVars = [:]
    def needDockerSocket = false
    String toString() {
        def env = envVars
                .collect({ entry -> "-e ${entry.key}=\"${entry.value}\"" })
                .join(' ')
        def cmd = """\
            |docker run
            |--init
            |--rm
            |--workdir \${PWD}
            |--user \$(id -u):\$(id -g)
            |-v \${PWD}:\${PWD}
            |-v /etc/group:/etc/group:ro
            |-v /etc/passwd:/etc/passwd:ro
            |-v \${HOME}/.m2:\${HOME}/.m2
            |-v \${HOME}/.docker:\${HOME}/.docker
            |${needDockerSocket ? '-v /var/run/docker.sock:/var/run/docker.sock' : ''}
            |${env}
            |\$(for group in \$(id -G); do printf ' --group-add %s' "\$group"; done)
            |--group-add \$(stat -c '%g' /var/run/docker.sock)
            |${bobImage}
            |"""
        return cmd
                .stripMargin()           // remove indentation
                .replace('\n', ' ')      // join lines
                .replaceAll(/[ ]+/, ' ') // replace multiple spaces by one
    }
}
