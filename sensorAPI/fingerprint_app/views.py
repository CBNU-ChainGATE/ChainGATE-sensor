from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .fingerprint import Fingerprint

# Initialize the fingerprint object (make sure the port and other parameters are correct)
fingerprint = Fingerprint()

@csrf_exempt
@require_http_methods(["POST"])
def enroll_finger(request):
    try:
        data = json.loads(request.body)
        location = data.get('location')
        if location is None:
            return HttpResponseBadRequest("Missing 'location' parameter")

        success = fingerprint.enroll_finger(location)
        return JsonResponse({'success': success})

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format")

@csrf_exempt
@require_http_methods(["POST"])
def find_finger(request):
    try:
        success = fingerprint.find_finger()
        if success:
            finger_id = fingerprint.finger.finger_id
            confidence = fingerprint.finger.confidence
            result = {
                        "finger_id": finger_id,
                        "confidence": confidence,
                    }
        return JsonResponse({'result': result})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def delete_finger(request):
    try:
        data = json.loads(request.body)
        location = data.get('location')
        if location is None:
            return HttpResponseBadRequest("Missing 'location' parameter")

        success = fingerprint.delete_finger(location)
        return JsonResponse({'success': success})

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format")

@csrf_exempt
@require_http_methods(["POST"])
def clear_library(request):
    try:
        success = fingerprint.clear_library()
        return JsonResponse({'success': success})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def save_fingerprint_image(request):
    try:
        from datetime import datetime

        now = datetime.now()
        formatted_date_time = now.strftime("%Y-%m-%d_%H-%M")
        filename = f'library_{formatted_date_time}.png'
        #data = json.loads(request.body)
        #filename = 'library.png'
        
        if not filename:
            return HttpResponseBadRequest("Missing 'filename' parameter")

        success = fingerprint.save_fingerprint_image(filename)
        return JsonResponse({'success': success})

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format")

