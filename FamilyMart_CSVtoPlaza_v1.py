from flask import Flask, jsonify, request
import csv, json, requests, os
import shutil
from pathlib import Path

app = Flask(__name__)

BATCH_SIZE = 10000
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

@app.route('/upload_toPlaza', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Missing file'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            save_path = os.path.join(r'/mnt/data', file.filename)
            file.save(save_path)

            done_folder = os.path.join(r'/mnt/data', 'done')
            os.makedirs(done_folder, exist_ok=True)
            done_path = os.path.join(done_folder, file.filename)
            shutil.copy(save_path, done_path)
            
            results = []
            for batch in csv_to_json(save_path):
                response = requests.patch(update_url , json=batch, headers=head)
                results.append(batch)
            os.remove(save_path)
            return jsonify({"status": "success", "results": f"{file.filename} is uploaded"})
        else:
            return jsonify({'error': 'No CSV file found'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
