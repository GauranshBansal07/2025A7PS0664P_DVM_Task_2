from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Ticket

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_ticket(request):

    ticket_id = request.data.get('ticket_id')
    gate_type = request.data.get('gate_type')

    try:
        ticket = Ticket.objects.get(ticket_id=ticket_id)
    except Ticket.DoesNotExist:
        return Response({"status": "error", "message": "Ticket not found ❌"}, status=404)

    if ticket.status == 'CANCELLED':
        return Response({"status": "error", "message": "Ticket was CANCELLED 🚫"}, status=400)
    
    if ticket.status == 'USED':
        return Response({"status": "error", "message": "Ticket already USED 🏁"}, status=400)

    if gate_type == 'entry':
        if ticket.entry_time:
            return Response({"status": "error", "message": "Already inside! (Double Entry) ⚠️"}, status=400)
        
        ticket.entry_time = timezone.now()
        ticket.save()
        return Response({"status": "success", "message": "Gate Open: Welcome! 🟢"})

    elif gate_type == 'exit':
        if not ticket.entry_time:
             return Response({"status": "error", "message": "You never scanned in! (Fraud?) ⚠️"}, status=400)
        
        ticket.status = 'USED'
        ticket.exit_time = timezone.now()
        ticket.save()
        return Response({"status": "success", "message": "Gate Open: Goodbye! 👋"})

    return Response({"status": "error", "message": "Invalid gate_type"}, status=400)