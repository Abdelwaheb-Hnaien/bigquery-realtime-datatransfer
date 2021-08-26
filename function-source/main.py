from google.cloud import bigquery_datatransfer, bigquery_datatransfer_v1
from google.cloud import datastore, firestore
from google.protobuf.timestamp_pb2 import Timestamp
import base64
import json
import os
import time
import requests

# with pip install the following requirements
#requests
#google-cloud
#google-cloud-bigquery-datatransfer
#protobuf
#google-cloud-datastore

#provide destination project infos:
DESTINATION_PROJECT_ID  = os.environ['DESTINATION_PROJECT_ID']
LOCATION_ID = os.environ['LOCATION_ID']
REALTIME_DB_MODE = os.environ['REALTIME_DB_MODE']

# datasets to watch (to transfert)
DATASETS_TO_TRANSFERT = json.loads(os.environ['DATASETS_TO_TRANSFERT'])

def insert_into_datastore(receiveTimestamp,datastore_client):
    task_key = datastore_client.key("Event")
    # Prepares the new entity
    task = datastore.Entity(key=task_key)
    task["receiveTimestamp"] = receiveTimestamp
    datastore_client.put(task)

def get_record_datastore(receiveTimestamp,datastore_client):
    query = datastore_client.query(kind="Event")
    query.add_filter("receiveTimestamp", "=", receiveTimestamp)
    results = list(query.fetch())
    return (results)

def insert_into_firestore(receiveTimestamp,firestore_client):
    doc_ref = firestore_client.collection(u'Event').document()
    doc_ref.set({
        u'receiveTimestamp': receiveTimestamp,
    })


def get_record_firestore(receiveTimestamp,firestore_client):
    existing_timestamps = firestore_client.collection(u'Event').where(u'receiveTimestamp', u'==', receiveTimestamp).get()
    return (existing_timestamps)

def run_transfer(event, context):
    #print("This Function was triggered by messageId {} published at {}".format(context.event_id, context.timestamp))

    # Get receiveTimestamp, the unique identifier of the message
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    pubsub_json = json.loads(pubsub_message)
    receiveTimestamp = pubsub_json['receiveTimestamp']

    # Check if this message has already triggered the function
    if (REALTIME_DB_MODE == "DATASTORE"):
        datastore_client = datastore.Client()
        res = get_record_datastore(receiveTimestamp,datastore_client)
    if (REALTIME_DB_MODE == "FIRESTORE"):
        firestore_client = firestore.Client()
        res = get_record_firestore(receiveTimestamp,firestore_client)

    print(len(res))
    if (len(res)>=1):
      print("----> block many execution retries due to pubsub multiple msg push !!")
      return

    # If it is the first time then insert it into Datastore
    if (REALTIME_DB_MODE == "DATASTORE"):
        insert_into_datastore(receiveTimestamp,datastore_client)
    if (REALTIME_DB_MODE == "FIRESTORE"):
        insert_into_firestore(receiveTimestamp,firestore_client)

    # Get DATASET_ID from Pub/Sub message payload
    dataset_id = pubsub_json['resource']['labels']['dataset_id']

    # Proceed only if DATASET_ID is to transfert
    if ( dataset_id in DATASETS_TO_TRANSFERT):
       print("--->  detect change on dataset {} ".format(dataset_id))
       # List all bq transfert in destination project
       transfer_client = bigquery_datatransfer_v1.DataTransferServiceClient()
       parent = transfer_client.common_location_path(DESTINATION_PROJECT_ID, LOCATION_ID)

       print("---> listing all transfert config in destination project")
       configs = transfer_client.list_transfer_configs(parent=parent)

       #iterate over transfer configs to find the one that matchs  "transfert-{dataset_id}"
       for config in configs:
         if (config.display_name == dataset_id+"_transfert"):
             # Wait two minutes until dataset update process finish
             print("---> function has identified the right transfert for dataset {} ".format(dataset_id))
             print("---> waiting some time before running transfert")
             time.sleep(300)
             now = time.time()
             seconds = int(now)
             nanos = int((now - seconds) * 10**9)
             start_time = Timestamp(seconds=seconds, nanos=nanos)
             request = bigquery_datatransfer_v1.types.StartManualTransferRunsRequest({"parent": config.name, "requested_run_time": start_time})
             print("---> run transfert")
             try:
                response = transfer_client.start_manual_transfer_runs(request, timeout=360)
             except:
                print("--> ERROR, Either there is a new request while transfert is in pending state or api is unreachable")
             else:
                print("---> getting transfert status")
                print(response)

    else :
        print("---> No action to do on Dataset {}".format(dataset_id))
