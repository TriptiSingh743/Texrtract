from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from .forms import ContactForm
import os
import json
import pandas as pd
import re
import boto3
from dotenv import load_dotenv
from twilio.rest import Client


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

def home(request):
    return render(request, 'home.html')


def document_type_selection(request):
    return render(request, 'types.html')


def upload_page(request):
    return render(request, 'upload_page.html')

# Initialize Textract and Comprehend clients
textract_client = boto3.client('textract')
comprehend_client = boto3.client('comprehend')

from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import boto3
import json
import re
import pandas as pd
from django.http import JsonResponse
from dotenv import load_dotenv
from .utils import (
    extract_text_from_image,
    process_passport,
    process_identity_card,
    process_aadhar_card,
    process_payment_receipt
)
from rest_framework.decorators import api_view


from rest_framework.response import Response
from rest_framework import status
from .serializers import UploadedImageSerializer
from .models import UploadedImage

from django.core.exceptions import ValidationError

def validate_image_format(image):
    valid_image_formats = ['image/jpeg', 'image/png']
    if image.content_type not in valid_image_formats:
        raise ValidationError('Unsupported file format. Please upload a JPEG or PNG image.')


from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import UploadedImage
from .serializers import UploadedImageSerializer
import boto3
from django.conf import settings
import os

@api_view(['POST'])
def upload_image(request):
    if 'image' not in request.FILES:
        print("Image file missing in the request.")
        return Response({"error": "No image file provided."}, status=status.HTTP_400_BAD_REQUEST)
    
    if 'document_type' not in request.data:
        print("Document type missing in the request.")
        return Response({"error": "No document type provided."}, status=status.HTTP_400_BAD_REQUEST)

    image = request.FILES['image']
    document_type = request.data.get('document_type', 'unknown')

    print("Received image:", image.name)
    print("Received document type:", document_type)

    try:
        # Process and save image
        uploaded_image = UploadedImage(image=image)
        uploaded_image.save()

        # Extract text and handle document type processing
        image_path = uploaded_image.image.path
        extracted_text = extract_text_from_image(image_path)

        if document_type == 'passport':
            entities = process_passport(extracted_text)
        elif document_type == 'identity_card':
            entities = process_identity_card(extracted_text)
        elif document_type == 'aadhar_card':
            entities = process_aadhar_card(extracted_text)
        elif document_type == 'payment_receipt':
            entities = process_payment_receipt(extracted_text)
        else:
            print("Invalid document type provided.")
            return Response({"error": "Invalid document type provided."}, status=status.HTTP_400_BAD_REQUEST)

        response_data = {
            "id": uploaded_image.id,
            "image": uploaded_image.image.url,
            "uploaded_at": uploaded_image.uploaded_at.isoformat(),
            "extracted_text": extracted_text,
            "detected_entities": entities,
            'show_entities_button': True,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error processing upload:", str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def entities(request):
    extracted_text = request.session.get('extracted_text', '')
    entities_json = request.session.get('entities', '[]')
    entities = json.loads(entities_json) if entities_json else []
    document_type = request.session.get('document_type', 'Unknown')

    return render(request, 'detected_entities.html', {
        'extracted_text': extracted_text,
        'entities': entities,
        'document_type': document_type
    })


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            # Send SMS to admin
            client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
            sms_message = f"New contact from {name} ({email}): {message}"
            client.messages.create(
                body=sms_message,
                from_=os.getenv('TWILIO_PHONE_NUMBER'),
                to=os.getenv('ADMIN_PHONE_NUMBER')
            )

            return redirect('success')  # Redirect to a success page

    else:
        form = ContactForm()

    return render(request, 'home.html', {'form': form})


def success_view(request):
    return render(request, 'success.html')
