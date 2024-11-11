import os
import re
import boto3
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AWS credentials
aws_access_key_id = os.getenv("AWS_ACCESS")
aws_secret_access_key = os.getenv("AWS_SECRET_KEY")

# Initialize Textract and Comprehend clients
textract_client = boto3.client(
    'textract',
    region_name='us-east-1',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

comprehend_client = boto3.client(
    'comprehend',
    region_name='us-east-1',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

def extract_text_from_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"The file {image_path} does not exist.")
    
    with open(image_path, 'rb') as image_file:
        image_bytes = image_file.read()
    
    textract_response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
    extracted_text = ''
    for item in textract_response.get('Blocks', []):
        if item.get('BlockType') == 'LINE':
            extracted_text += item.get('Text', '') + '\n'
    return extracted_text

# Processing for Passport
def process_passport(extracted_text):
    comprehend_response = comprehend_client.detect_entities(Text=extracted_text, LanguageCode='en')
    df = pd.DataFrame(comprehend_response['Entities'])

    passport_number_pattern = re.compile(r'\b[A-Z]\d{7}\b')
    nationality_pattern = re.compile(r'\b(INDIAN|IND)\b', re.IGNORECASE)
    dob_pattern = re.compile(r'\b\d{2}/\d{2}/\d{4}\b')
    place_of_birth_pattern = re.compile(r'\b(?:PRAYAGRAJ|[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b')
    place_of_issue_pattern = re.compile(r'\b(?:SINGAPORE|[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b')

    doi_keywords = ["date of issue", "issued on", "doi"]
    doe_keywords = ["date of expiry", "expires on", "doe"]

    def identify_entity(row):
        text = row['Text']
        surrounding_text = extracted_text[row['BeginOffset']-50:row['EndOffset']+50].lower()
        if passport_number_pattern.search(text):
            return 'PASSPORT_NUMBER'
        elif nationality_pattern.search(text):
            return 'NATIONALITY'
        elif place_of_birth_pattern.search(text):
            return 'PLACE_OF_BIRTH'
        elif place_of_issue_pattern.search(text):
            return 'PLACE_OF_ISSUE'
        elif any(keyword in surrounding_text for keyword in doi_keywords):
            return 'DATE_OF_ISSUE'
        elif any(keyword in surrounding_text for keyword in doe_keywords):
            return 'DATE_OF_EXPIRY'
        elif dob_pattern.search(text):
            return 'DATE_OF_BIRTH'
        else:
            return 'OTHER'

    df['Type'] = df.apply(identify_entity, axis=1)
    df = df[['Score', 'Type', 'Text', 'BeginOffset', 'EndOffset']]
    
    detected_entities = {
        "PASSPORT_NUMBER": None,
        "NATIONALITY": None,
        "PLACE_OF_BIRTH": None,
        "PLACE_OF_ISSUE": None,
        "DATE_OF_ISSUE": None,
        "DATE_OF_EXPIRY": None,
        "DATE_OF_BIRTH": None
    }

    for _, row in df.iterrows():
        if row['Type'] in detected_entities and detected_entities[row['Type']] is None:
            detected_entities[row['Type']] = row['Text']
    
    return df.to_dict(orient='records')

# Processing for Identity Card
def process_identity_card(extracted_text):
    comprehend_response = comprehend_client.detect_entities(Text=extracted_text, LanguageCode='en')
    df = pd.DataFrame(comprehend_response['Entities'])

    card_number_pattern = re.compile(r'\b[SFG]\d{7}[A-Z]?\b')
    race_pattern = re.compile(r'\b(INDIAN|CHINESE|MALAY|OTHER)\b', re.IGNORECASE)
    dob_pattern = re.compile(r'\b\d{2}-\d{2}-\d{4}\b')
    sex_pattern = re.compile(r'\b(M|F)\b')
    location_pattern = re.compile(r'\b(INDIA|MALAYSIA|SINGAPORE|[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b')
    phone_pattern = re.compile(r'\+?\d[\d -]{8,}\d')
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    website_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+|www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    postal_code_pattern = re.compile(r'\b\d{6}\b')

    comprehend_response = comprehend_client.detect_entities(Text=extracted_text, LanguageCode='en')
    df = pd.DataFrame(comprehend_response['Entities'])
    def identify_entity(row):
        text = row['Text']
        if row['Type'] in ['PERSON', 'ORGANIZATION']:
            return row['Type']
        elif card_number_pattern.search(text):
            return 'IDENTITY_CARD_NUMBER'
        elif race_pattern.search(text):
            return 'RACE'
        elif dob_pattern.search(text):
            return 'DATE_OF_BIRTH'
        elif sex_pattern.search(text):
            return 'SEX'
        elif location_pattern.search(text):
            return 'LOCATION'
        elif phone_pattern.search(text):
             return 'PHONE_NUMBER'
        elif email_pattern.search(text):
             return 'EMAIL'
        elif website_pattern.search(text):
             return 'WEBSITE'
        elif postal_code_pattern.search(text):
             return 'POSTAL_CODE'
        else:
            return 'OTHER'

    df['Type'] = df.apply(identify_entity, axis=1)
    df = df[['Score', 'Type', 'Text', 'BeginOffset', 'EndOffset']]

    
    
    detected_entities = {
        "IDENTITY_CARD_NUMBER": None,
        "NAME": None,
        "RACE": None,
        "DATE_OF_BIRTH": None,
        "SEX": None,
        "LOCATION": None,
        'PHONE_NUMBER':None,
        'EMAIL':None,
        'WEBSITE':None,
        'POSTAL_CODE':None
    }

    for _, row in df.iterrows():
        if row['Type'] in detected_entities and detected_entities[row['Type']] is None:
            detected_entities[row['Type']] = row['Text']
    
    return df.to_dict(orient='records')

# Processing for Aadhaar Card
def process_aadhar_card(extracted_text):
    comprehend_response = comprehend_client.detect_entities(Text=extracted_text, LanguageCode='en')
    df = pd.DataFrame(comprehend_response['Entities'])

    aadhar_number_pattern = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b')
    vid_number_pattern = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b')
    dob_pattern = re.compile(r'\b\d{2}/\d{2}/\d{4}\b')
    gender_pattern = re.compile(r'\b(MALE|FEMALE)\b', re.IGNORECASE)
    name_pattern = re.compile(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b')

    comprehend_response = comprehend_client.detect_entities(Text=extracted_text, LanguageCode='en')
    df = pd.DataFrame(comprehend_response['Entities'])

    def identify_entity(row):
        text = row['Text'].strip()
        if vid_number_pattern.search(text):
            return 'VID_NUMBER'
        elif aadhar_number_pattern.search(text):
            return 'AADHAR_NUMBER'
        elif dob_pattern.search(text):
            return 'DATE_OF_BIRTH'
        elif gender_pattern.search(text):
            return 'GENDER'
        elif name_pattern.search(text):
            return 'NAME'
        else:
            return 'OTHER'

    df['Type'] = df.apply(identify_entity, axis=1)
    df = df[['Score', 'Type', 'Text', 'BeginOffset', 'EndOffset']]
    
    detected_entities = {
        "VID_NUMBER": None,
        "AADHAR_NUMBER": None,
        "DATE_OF_BIRTH": None,
        "GENDER": None,
        "NAME": None
    }

    for _, row in df.iterrows():
        if row['Type'] in detected_entities and detected_entities[row['Type']] is None:
            detected_entities[row['Type']] = row['Text']
    
    return df.to_dict(orient='records')

# Processing for Payment Receipt
def process_payment_receipt(extracted_text):
    company_pattern = re.compile(r'Optd by:\s*(.*)', re.IGNORECASE)
    item_price_pattern = re.compile(r'([A-Za-z\s]+\[?[A-Za-z\s]*\]?)\s*(\d+\.\d{2})')
    subtotal_pattern = re.compile(r'SubTotal\s*[:=]?\s*(\d+\.\d{2})', re.IGNORECASE)
    pre_tax_pattern = re.compile(r'PreTax\s*[:=]?\s*(\d+\.\d{2})', re.IGNORECASE)
    vat_pattern = re.compile(r'VAT\s*[:=]?\s*(\d+\.\d{2})', re.IGNORECASE)
    final_amount_due_pattern = re.compile(r'Amount Due\s*[:=]?\s*(\d+\.\d{2})', re.IGNORECASE)

    entities = []

    def add_matches(pattern, entity_type, text):
        for match in pattern.finditer(text):
            entities.append({
                'Text': match.group(),
                'Type': entity_type,
                'Score': 1.0,
                'BeginOffset': match.start(),
                'EndOffset': match.end()
            })

    add_matches(company_pattern, 'COMPANY', extracted_text)
    add_matches(item_price_pattern, 'ITEM_PRICE', extracted_text)
    add_matches(subtotal_pattern, 'SUBTOTAL', extracted_text)
    add_matches(pre_tax_pattern, 'PRE_TAX', extracted_text)
    add_matches(vat_pattern, 'VAT', extracted_text)
    add_matches(final_amount_due_pattern, 'FINAL_AMOUNT_DUE', extracted_text)

    df = pd.DataFrame(entities)
    df = df[['Score', 'Type', 'Text', 'BeginOffset', 'EndOffset']]

    detected_entities = {
        "COMPANY": None,
        "ITEMS": [],
        "SUBTOTAL": None,
        "PRE_TAX": None,
        "VAT": None,
        "FINAL_AMOUNT_DUE": None
    }

    for _, row in df.iterrows():
        if row['Type'] == 'ITEM_PRICE':
            detected_entities["ITEMS"].append(row['Text'])
        elif row['Type'] in detected_entities and detected_entities[row['Type']] is None:
            detected_entities[row['Type']] = row['Text']
    
    return df.to_dict(orient='records')
