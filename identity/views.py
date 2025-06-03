from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models, transaction
from .models import Contact
from django.utils import timezone
import json

@csrf_exempt
def identify(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed.'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON input.'}, status=400)

    email = data.get('email')
    phone_number = data.get('phoneNumber')

    if not email and not phone_number:
        return JsonResponse({'error': 'Email or phone number is required.'}, status=400)

    with transaction.atomic():
        # Step 1: Direct matches
        initial_matches = Contact.objects.filter(
            models.Q(email=email) | models.Q(phone_number=phone_number)
        )

        if initial_matches.exists():
            ids_to_explore = set(initial_matches.values_list('id', flat=True)) | set(initial_matches.values_list('linked_id', flat=True))
            ids_to_explore.discard(None)

            while True:
                expanded = Contact.objects.filter(
                    models.Q(id__in=ids_to_explore) | models.Q(linked_id__in=ids_to_explore)
                )
                new_ids = set(expanded.values_list('id', flat=True)) | set(expanded.values_list('linked_id', flat=True))
                new_ids.discard(None)

                if new_ids.issubset(ids_to_explore):
                    break
                ids_to_explore |= new_ids

            contacts = Contact.objects.filter(
                models.Q(id__in=ids_to_explore) | models.Q(linked_id__in=ids_to_explore)
            ).order_by('created_at')

            primary_contact = contacts.filter(link_precedence='primary').first() or contacts.first()

            for contact in contacts:
                if contact.id != primary_contact.id and contact.link_precedence != 'secondary':
                    contact.link_precedence = 'secondary'
                    contact.linked_id = primary_contact.id
                    contact.updated_at = timezone.now()
                    contact.save()

            existing = contacts.filter(email=email, phone_number=phone_number).exists()
            if not existing:
                Contact.objects.create(
                    email=email,
                    phone_number=phone_number,
                    link_precedence='secondary',
                    linked_id=primary_contact.id
                )

            final_contacts = Contact.objects.filter(
                models.Q(id=primary_contact.id) | models.Q(linked_id=primary_contact.id)
            )

            emails = set(c.email for c in final_contacts if c.email)
            phone_numbers = set(c.phone_number for c in final_contacts if c.phone_number)
            secondary_ids = [c.id for c in final_contacts if c.link_precedence == 'secondary']

            response = {
                'contact': {
                    'primaryContactId': primary_contact.id,
                    'emails': list(emails),
                    'phoneNumbers': list(phone_numbers),
                    'secondaryContactIds': secondary_ids
                }
            }
        else:
            new_contact = Contact.objects.create(
                email=email,
                phone_number=phone_number,
                link_precedence='primary'
            )
            response = {
                'contact': {
                    'primaryContactId': new_contact.id,
                    'emails': [email] if email else [],
                    'phoneNumbers': [phone_number] if phone_number else [],
                    'secondaryContactIds': []
                }
            }

    return JsonResponse(response, status=200)