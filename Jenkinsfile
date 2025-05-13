pipeline {
    agent any

    environment {
        RESOURCE_GROUP = 'rag-poc-rg'
        AKS_CLUSTER = 'rag-poc-aks'
        ACR_NAME = 'solpocacr'
        ACR_LOGIN_SERVER = "${ACR_NAME}.azurecr.io"
        IMAGE_NAME = 'rag-pdf-chatbot'
        IMAGE_TAG = 'latest'
        STORAGE_ACCOUNT = 'solragstorageacct'
        FILE_SHARE_NAME = 'llamamodelshare'
        AZURE_CREDENTIALS_ID = 'azure-sp-credentials'
        GIT_REPO = 'https://github.com/mulukelem/genai-rag-demo-aks.git'
        SECRET_NAME = 'azure-secret'
        STORAGE_ACCOUNT_KEY = ''
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: 'main']],
                    extensions: [
                        [$class: 'CleanBeforeCheckout'],
                        [$class: 'CloneOption', depth: 1, shallow: true]
                    ],
                    userRemoteConfigs: [[
                        url: "${GIT_REPO}",
                        credentialsId: 'github-pat'
                    ]]
                ])
                sh 'echo "✅ Code checkout completed"'
            }
        }

        stage('Azure Login') {
            steps {
                withCredentials([azureServicePrincipal(
                    credentialsId: "${AZURE_CREDENTIALS_ID}",
                    subscriptionIdVariable: 'AZ_SUBSCRIPTION_ID',
                    clientIdVariable: 'AZ_CLIENT_ID',
                    clientSecretVariable: 'AZ_CLIENT_SECRET',
                    tenantIdVariable: 'AZ_TENANT_ID'
                )]) {
                    sh '''
                        az login --service-principal \
                            -u $AZ_CLIENT_ID \
                            -p $AZ_CLIENT_SECRET \
                            --tenant $AZ_TENANT_ID
                        az account set --subscription $AZ_SUBSCRIPTION_ID
                    '''
                }
            }
        }

        stage('Create ACR and File Share') {
            steps {
                script {
                    // Create storage account and file share
                    sh """
                        az storage account create \
                            --name $STORAGE_ACCOUNT \
                            --resource-group $RESOURCE_GROUP \
                            --sku Standard_LRS

                        export AZURE_STORAGE_KEY=\$(az storage account keys list \
                            --resource-group $RESOURCE_GROUP \
                            --account-name $STORAGE_ACCOUNT \
                            --query "[0].value" -o tsv)

                        az storage share create \
                            --name $FILE_SHARE_NAME \
                            --account-name $STORAGE_ACCOUNT \
                            --account-key \$AZURE_STORAGE_KEY
                    """
                }
            }
        }

        stage('Build and Push Docker Image') {
            steps {
                sh '''
                    docker build -t $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG .
                    az acr login --name $ACR_NAME
                    docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG
                '''
            }
        }

        stage('Deploy to AKS with CSI Volume') {
            steps {
                script {
                    // Get Azure storage account key
                    env.STORAGE_ACCOUNT_KEY = sh(
                        script: "az storage account keys list --resource-group $RESOURCE_GROUP --account-name $STORAGE_ACCOUNT --query '[0].value' -o tsv",
                        returnStdout: true
                    ).trim()

                    // Authenticate and prepare AKS
                    sh """
                        az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER --overwrite-existing
                        kubectl create secret generic $SECRET_NAME \
                          --from-literal=azurestorageaccountname=$STORAGE_ACCOUNT \
                          --from-literal=azurestorageaccountkey=$STORAGE_ACCOUNT_KEY \
                          --dry-run=client -o yaml | kubectl apply -f -
                    """

                    // Apply manifests
                    sh '''
                        kubectl apply -f k8s/pv.yaml
                        kubectl apply -f k8s/pvc.yaml
                        kubectl apply -f k8s/deployment.yaml
                        kubectl apply -f k8s/service.yaml
                    '''
                }
            }
        }
    }
}

