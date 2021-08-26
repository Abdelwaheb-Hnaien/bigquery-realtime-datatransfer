#!/bin/bash

# Destination project where to find Bq-transfers
DESTINATION_PROJECT="<destination-project-id>"

# Enable cloud build api
echo -e "\e[5m\e[32m\e[1m--> enabling cloud build API\e[25m\e[0m"
gcloud services enable cloudbuild.googleapis.com
sleep 10

# Pub/sub topic
echo -e "\e[5m\e[32m\e[1m--> Creating Pub/Sub topic\e[25m\e[0m"
gcloud pubsub topics create dataset_update_topic

# logging sinks
echo -e "\e[5m\e[32m\e[1m--> Creating logging sink\e[25m\e[0m"
gcloud logging sinks create dataset_update_logSink pubsub.googleapis.com/projects/$GOOGLE_CLOUD_PROJECT/topics/dataset_update_topic --log-filter 'resource.type="bigquery_dataset" AND ((protoPayload.methodName="google.cloud.bigquery.v2.JobService.InsertJob" AND protoPayload.authorizationInfo.permission="bigquery.tables.updateData") OR protoPayload.methodName="google.cloud.bigquery.v2.TableService.InsertTable" OR protoPayload.methodName="google.cloud.bigquery.v2.TableService.PatchTable") AND severity!=ERROR'

# Cloud function
echo -e "\e[5m\e[32m\e[1m--> Deploying Cloud function\e[25m\e[0m"
gcloud functions deploy run_transfer --region=europe-west1 --runtime=python38 --timeout 540s --trigger-topic=dataset_update_topic --env-vars-file env.yaml --entry-point run_transfer  --source=function-source

# IAM role binding
# Grant the logging sink serviceAccount pubsub.publisher role
echo -e "\e[5m\e[32m\e[1m--> Binding IAM roles in the current project\e[25m\e[0m"
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member="$(gcloud logging sinks describe dataset_update_logSink | tail -1 | cut -d\   -f2)" --role="roles/pubsub.publisher"

# Grant the cloud function serviceAccount datastore.owner role
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member="serviceAccount:$GOOGLE_CLOUD_PROJECT@appspot.gserviceaccount.com" --role="roles/datastore.owner"

echo -e "\e[5m\e[32m\e[1m--> Binding IAM roles in the destination project\e[25m\e[0m"
# Grant the cloud function serviceAccount bigquery.admin role to be able to run transfer config
gcloud projects add-iam-policy-binding $DESTINATION_PROJECT --member="serviceAccount:$GOOGLE_CLOUD_PROJECT@appspot.gserviceaccount.com" --role="roles/bigquery.admin"
