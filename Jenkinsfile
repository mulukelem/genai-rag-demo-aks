pipeline {
    agent any

    environment {
        RESOURCE_GROUP = 'rag-poc-rg'
        AKS_CLUSTER = 'rag-poc-aks'
        ACR_NAME = 'solpocacr'
        ACR_LOGIN_SERVER = "${ACR_NAME}.azurecr.io"
        IMAGE_NAME = 'rag-pdf-chatbot'
        IMAGE_TAG = 'latest'
        STORAGE_ACCOUNT = 'ragstorageacct'
        FILE_SHARE_NAME = 'llamamodelshare'
        AZURE_CREDENTIALS_ID = 'azure-sp-credentials'
    }

    stages {
        stage('Checkout Code') {
            steps {
                withCredentials([string(credentialsId: 'github-pat', variable: 'GIT_TOKEN')]) {
                    sh '''
                        git clone https://$GIT_TOKEN@github.com/mulukelem/genai-rag-demo-aks.git
                        cd genai-rag-demo-aks
                    '''
                }
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

        stage('Create Azure File Share') {
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
                            --account-key $AZURE_STORAGE_KEY
                    '''
                }
            }
        }

        stage('Deploy to AKS') {
            steps {
                sh '''
                    az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER --overwrite-existing

                    kubectl apply -f k8s/pv.yaml
                    kubectl apply -f k8s/pvc.yaml
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml
                '''
            }
        }
    }
}

