pipeline {
    agent any

    environment {
        RESOURCE_GROUP      = 'sol-rag-poc-rg'
        AKS_CLUSTER         = 'sol-rag-poc-aks'
        ACR_NAME            = 'solpocacr'
        ACR_LOGIN_SERVER    = "${ACR_NAME}.azurecr.io"
        IMAGE_NAME          = 'rag-pdf-chatbot'
        IMAGE_TAG           = 'latest'
        STORAGE_ACCOUNT     = 'solragstorageacct'
        FILE_SHARE_NAME     = 'solllamamodelshare'
        MOUNT_LOCAL_PATH    = '/home/mulusol/genai-rag-demo-aks/models/llama-model/'   // local folder where model file is kept
        CONTAINER_MOUNT_PATH= '/mnt/models/llama'    // mount path in container
        SECRET_NAME         = 'azure-secret'
        AZURE_CREDENTIALS_ID= 'azure-sp-credentials'
        GIT_REPO            = 'https://github.com/mulukelem/genai-rag-demo-aks.git'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: 'main']],
                    extensions: [[$class: 'CleanBeforeCheckout']],
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

        stage('Create Storage Account and File Share') {
            steps {
                script {
                    sh '''
                        # Create storage account if not exists
                        if ! az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP &>/dev/null; then
                          echo "Creating storage account..."
                          az storage account create \
                            --name $STORAGE_ACCOUNT \
                            --resource-group $RESOURCE_GROUP \
                            --sku Standard_LRS \
                            --kind StorageV2 \
                            --enable-large-file-share
                        fi

                        echo "Getting storage key..."
                        export AZURE_STORAGE_KEY=$(az storage account keys list \
                            --resource-group $RESOURCE_GROUP \
                            --account-name $STORAGE_ACCOUNT \
                            --query "[0].value" -o tsv)

                        echo "Creating file share..."
                        az storage share-rm create \
                            --resource-group $RESOURCE_GROUP \
                            --storage-account $STORAGE_ACCOUNT \
                            --name $FILE_SHARE_NAME

                        echo "Uploading model files..."
                        az storage file upload-batch \
                            --account-name $STORAGE_ACCOUNT \
                            --account-key $AZURE_STORAGE_KEY \
                            --destination $FILE_SHARE_NAME \
                            --source $MOUNT_LOCAL_PATH
                    '''
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

        stage('AKS Credentials and Secret') {
            steps {
                script {
                    sh '''
                        az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER --overwrite-existing

                        echo "Creating Kubernetes secret for Azure File Share..."
                        export STORAGE_ACCOUNT_KEY=$(az storage account keys list \
                            --resource-group $RESOURCE_GROUP \
                            --account-name $STORAGE_ACCOUNT \
                            --query "[0].value" -o tsv)

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

    post {
        success {
            echo "✅ Deployment complete!"
        }
        failure {
            echo "❌ Deployment failed. Please check the logs."
        }
    }
}

