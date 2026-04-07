import csv
import json
import os

def validate_csv(file_path):
    errors = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        expected_cols = len(header)
        
        ids = set()
        
        for i, row in enumerate(reader, start=2):
            # Check column count
            if len(row) != expected_cols:
                errors.append(f"Line {i}: Expected {expected_cols} columns, found {len(row)}")
            
            # Check ID uniqueness
            if len(row) > 0:
                job_id = row[0]
                if job_id in ids:
                    errors.append(f"Line {i}: Duplicate ID '{job_id}'")
                ids.add(job_id)
            
            # Check Payload JSON if it exists
            if len(row) > 9:
                payload_str = row[9]
                if payload_str:
                    try:
                        json.loads(payload_str)
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {i}: Malformed JSON in Payload column: {str(e)}")
            
    return errors

if __name__ == "__main__":
    csv_path = r'c:\Users\remot\Documents\SmartApply-dev\input\sample_jobs.csv'
    if os.path.exists(csv_path):
        validation_errors = validate_csv(csv_path)
        if validation_errors:
            print(f"Found {len(validation_errors)} errors:")
            for err in validation_errors[:20]: # Show first 20
                print(err)
            if len(validation_errors) > 20:
                print(f"... and {len(validation_errors) - 20} more.")
        else:
            print("No structural errors found in CSV.")
    else:
        print(f"File not found: {csv_path}")
