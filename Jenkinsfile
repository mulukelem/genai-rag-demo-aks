pipeline {
    agent any

    environment {
        RESOURCE_GROUP      = 'sol-rag-poc-rg'
        AKS_CLUSTER         = 'sol-rag-poc-aks'
        ACR_NAME            = 'solpocacr'
        ACR_LOGIN_SERVER    = "${ACR_NAME}.azurecr.io"
        IMAGE_NAME          = 'sol-rag-pdf-chatbot'
        IMAGE_TAG           = 'latest'
        STORAGE_ACCOUNT     = 'solragstorageacct'
        FILE_SHARE_NAME     = 'solllamamodelshare'
        SECRET_NAME         = 'azure-secret'
        AZURE_CREDENTIALS_ID= 'azure-sp-credentials'
        GIT_REPO            = 'https://github.com/mulukelem/genai-rag-demo-aks.git' // Your repo URL
        LOCAL_MODEL_PATH    = 'models/llama-model' // Adjust if your local path is different
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

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG .
                '''
            }
        }

        stage('Push to ACR') {
            steps {
                sh '''
                    az acr login --name $ACR_NAME
                    docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG
                '''
            }
        }

        stage('Create Azure File Share & Upload Model') {
            steps {
                withCredentials([azureServicePrincipal(
                    credentialsId: "${AZURE_CREDENTIALS_ID}",
                    subscriptionIdVariable: 'AZ_SUBSCRIPTION_ID',
                    clientIdVariable: 'AZ_CLIENT_ID',
                    clientSecretVariable: 'AZ_CLIENT_SECRET',
                    tenantIdVariable: 'AZ_TENANT_ID'
                )]) {
                    sh '''
                        export AZURE_STORAGE_KEY=$(az storage account keys list \
                            --resource-group $RESOURCE_GROUP \
                            --account-name $STORAGE_ACCOUNT \
                            --query "[0].value" -o tsv)

                        az storage share create \
                            --name $FILE_SHARE_NAME \
                            --account-name $STORAGE_ACCOUNT \
                            --account-key $AZURE_STORAGE_KEY || true

                        az storage file upload-batch \
                            --destination $FILE_SHARE_NAME \
                            --source $LOCAL_MODEL_PATH \
                            --account-name $STORAGE_ACCOUNT \
                            --account-key $AZURE_STORAGE_KEY
                    '''
                }
            }
        }

        stage('Create K8s Secret for FileShare Access') {
            steps {
                withCredentials([azureServicePrincipal(
                    credentialsId: "${AZURE_CREDENTIALS_ID}",
                    subscriptionIdVariable: 'AZ_SUBSCRIPTION_ID',
                    clientIdVariable: 'AZ_CLIENT_ID',
                    clientSecretVariable: 'AZ_CLIENT_SECRET',
                    tenantIdVariable: 'AZ_TENANT_ID'
                )]) {
                    sh '''
                        export STORAGE_ACCOUNT_KEY=$(az storage account keys list \
                            --resource-group $RESOURCE_GROUP \
                            --account-name $STORAGE_ACCOUNT \
                            --query "[0].value" -o tsv)

                        az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER --overwrite-existing

                        kubectl create secret generic $SECRET_NAME \
                          --from-literal=azurestorageaccountname=$STORAGE_ACCOUNT \
                          --from-literal=azurestorageaccountkey=$STORAGE_ACCOUNT_KEY \
                          --dry-run=client -o yaml | kubectl apply -f -
                    '''
                }
            }
        }

        stage('Deploy to AKS') {
            steps {
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

