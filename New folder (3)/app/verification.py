import json

def verify_data(form_json_path, extracted_json_path):
    with open(form_json_path, 'r') as form_file, open(extracted_json_path, 'r') as extracted_file:
        form_data = json.load(form_file)
        extracted_data = json.load(extracted_file)

    mismatches = {}
    for key, value in form_data.items():
        if key in extracted_data and form_data[key] != extracted_data[key]:
            mismatches[key] = {"form_value": value, "extracted_value": extracted_data[key]}
    
    return mismatches
