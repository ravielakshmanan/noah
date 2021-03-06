import os
import csv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud import storage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = './noah_credentials.json'

# dataset available from Cloud Storage Bucket (4966273 lines)
file_path = "./iri_dataset.csv"
file_name = "iri_dataset.csv"
collection_name = "precipitation_data"
# file_path = "./iri_data.csv"
# collection_name = "precipitation_test"

def download_iri_data_from_gc():
  client = storage.Client()
  bucket = client.get_bucket('noah-water.appspot.com')
  blob = bucket.blob(file_name)
  blob.download_to_filename(file_name)
  print('Blob {} downloaded to {}.'.format(file_name,file_name))

def batch_data(iterable, n=1):
    l = len(iterable)
    for i in range(0, l, n):
      yield iterable[i:min(i + n, l)]

def get_data_from_store(store):
  doc_ref = store.collection(collection_name).limit(5)
  return doc_ref

def put_data_to_store(store):
  data = []
  headers = []
  print("Preparing to read CSV...")
  with open(file_path) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            for header in row:
                headers.append(header)
            line_count += 1
        else:
            obj = {}
            for idx, item in enumerate(row):
                obj[headers[idx]] = item
            data.append(obj)
            line_count += 1
  # print(f'Processed {line_count} lines.')
  print("Processed {} lines.".format(line_count))

  for batched_data in batch_data(data, 499):
    item_count = 0
    batch = store.batch()
    for data_item in batched_data:
        doc_ref = store.collection(collection_name).document()
        batch.set(doc_ref, data_item)
        item_count += 1
    batch.commit()
    # print(f'Processed {item_count} lines.')
    print("Processed {} lines.".format(item_count))

  print("Done!")

# nohup python data_model.py > my_output.log &
# Fetch CSV from cloud storage
# download_iri_data_from_gc()

# Use a service account
cred = credentials.Certificate(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
firebase_admin.initialize_app(cred)

db = firestore.client()
print("Inserting data into Firestore...")
put_data_to_store(db)

print("Fetching data from Firestore...")
df = get_data_from_store(db)

try:
  docs = df.get()
  for doc in docs:
      print(u'Doc Data:{}'.format(doc.to_dict()))
except google.cloud.exceptions.NotFound:
  print(u'Missing data')