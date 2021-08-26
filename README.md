# Bigquery realtime data transfer framework
__*Purpose:*__

This tool is ideal when you need a realtime data synchronization between two Bigquery datasets. You dont have to wait for the scheduled data transfer to perform this action, instead this tool will trigger it immediately whenever there is a change in a source Dataset. This change could be:
  - update data in a table
  - Alter table schema
  - create new table

There are some other use cases where you may need this tool like manually trigger a scheduled query on demand, but it requires some chages in the source code and to the framework overall.

__*Prerequisites:*__

gcloud should be configured (cehck `gcloud config list`).

Bigquery transfer config should be already created manually and the name of the transfert config has to be in the form : **\<datasetSource>_transfert**.

__*STEPS:*__

In the SOURCE project, run a cloud shell instance, copy the content of this folder in the current working directory and perform the following steps:

1. In source project, check which FIRESTORE mode is enabled (Firestore native or Firestore in DATASTORE mode), if nothing is set we recommand to enable DATASTORE MODE (should be done manually)

2. Update env.yaml :
  - Set DATASETS_TO_TRANSFERT to the list of datasets you want to transfer and

  - Set REALTIME_DB_MODE to either FIRESTORE or DATASTORE

  - Set LOCATION_ID to the location of your DATA TRANSFER CONFIG (which is the location of your destination dataset)

  - Set DESTINATION PROJECT which is the project where you have created the transfer config.

3. Set DESTINATION_PROJECT in synchro-bq.sh

4. run "sh synchro-bq.sh"

**Notice**:

DESTINATION PROJECT is the project where you have created the transfer config.

LOCATION_ID is the location of your DATA TRANSFER CONFIG (which is the location of your destination dataset)

SOURCE PROJECT is the project where the source dataset(s) is/are located.

The last step of synchro-bq.sh will grant the cloud function serviceAccount bigquery.admin role to be able to run transfer config in the destination project.

DATASTORE (or FIRESTORE) is used to block multiple cloud function invocations due to pubsub push retries that may happen. This concept is known for the name **idempotency**, for more inspirations please refer to :
[https://cloud.google.com/blog/products/serverless/cloud-functions-pro-tips-building-idempotent-functions](https://cloud.google.com/blog/products/serverless/cloud-functions-pro-tips-building-idempotent-functions)
