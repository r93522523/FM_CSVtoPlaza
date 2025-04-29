from flask import Flask, jsonify, request
import csv, json, requests, os
import shutil
from pathlib import Path

app = Flask(__name__)
API_KEY = os.environ.get('ELSCommKey')

BATCH_SIZE = 2
def csv_to_json(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        batch = []
        for row in reader:
            item = { "itemId": row.get("BARCODE", "").strip(),
                "itemName": row.get("CMNM", "").strip(),
                "price": row.get("SLUNT", "").strip(),
                "properties": {
                    "CMBND": row.get("CMBND", "").strip(),
                    "SPC": row.get("SPC", "").strip(),
                    "Promo_id": row.get("Promo_id", "").strip(),
                    "Promo_text": row.get("Promo_text", "").strip(),
                    "Foodsafety": row.get("Foodsafety", "").strip(),
                    "FU_SPACE": row.get("FU_SPACE", "").strip() }}
            batch.append(item)
            if len(batch) == BATCH_SIZE:
                yield batch
                batch = []
        if batch:
            yield batch

tokenurl = "https://central-manager.familymart-tw-test.pcm.pricer-plaza.com/api/public/auth/v1/login"
apitoken = requests.get(tokenurl , auth=('api@familymart.com.tw','Api@familymart2025'))
token = apitoken.text[28:-2]
head = {"Authorization":"Bearer " + token, "Content-Type":"application/json"}
update_url = "https://apitest.familymart-tw-test.pcm.pricer-plaza.com/api/public/core/v1/items"

@app.route('/upload', methods=['POST'])
def upload_file():
    client_key = request.headers.get('ELSCommKey')
    if client_key != API_KEY:
        return jsonify({'message': 'Forbidden: Invalid API key'}), 403
    else:
        return jsonify({'message': 'Access granted!'})
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            save_path = os.path.join('/mnt/data', file.filename)
            file.save(save_path)
            results = []
            for batch in csv_to_json(save_path):
                response = requests.patch(update_url , json=batch, headers=head)
                results.append(batch)
            return jsonify({"status": "success", "results": results})

if __name__ == '__main__':
    app.run(debug=True)
