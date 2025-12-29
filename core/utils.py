from collections import deque
from .models import Station, StationOnLine, Ticket
import random
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal

def find_shortest_path(start_station_name, end_station_name):
    if start_station_name == end_station_name:
        return None, None, 0

    # 1. Build the Graph (Correctly handling multiple lines between same stations)
    graph = {}
    all_connections = StationOnLine.objects.select_related('station', 'line').all()
    
    lines_map = {} 
    for conn in all_connections:
        lines_map.setdefault(conn.line.name, []).append(conn)

    for line_name, connections in lines_map.items():
        # Ensure stations are in order based on their index
        connections.sort(key=lambda x: x.order)
        for i in range(len(connections)):
            curr_st = connections[i].station.name
            if curr_st not in graph: graph[curr_st] = []

            # Add neighbors as tuples: (neighbor_name, line_name)
            if i > 0:
                prev_st = connections[i-1].station.name
                graph[curr_st].append((prev_st, line_name))
            if i < len(connections) - 1:
                next_st = connections[i+1].station.name
                graph[curr_st].append((next_st, line_name))

    # 2. BFS for Shortest Path
    queue = deque([(start_station_name, [start_station_name], [])]) 
    visited = {start_station_name}

    while queue:
        curr, path, path_lines = queue.popleft()

        if curr == end_station_name:
            return path, path_lines, (len(path) - 1)

        # Iterate through list of tuples (neighbor, line)
        for neighbor, line_used in graph.get(curr, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor], path_lines + [line_used]))

    return None, None, 0

def get_navigation_instructions(path, lines):
    if not path or not lines:
        return "Direct Trip"
        
    instructions = []
    # lines[0] is the line used to get from path[0] to path[1]
    current_line = lines[0]
    instructions.append(f"🟢 Start at {path[0]} on the {current_line}")

    for i in range(1, len(lines)):
        # If the line used for the NEXT leg is different, we transferred at path[i]
        if lines[i] != current_line:
            instructions.append(f"🔄 Transfer at {path[i]} to the {lines[i]}")
            current_line = lines[i]
    
    instructions.append(f"🏁 Arrive at {path[-1]}")
    return "\n".join(instructions)

def generate_otp():
    """Generates a 6-digit numeric string."""
    return str(random.randint(100000, 999999))

def send_otp_email(user_email, otp):
    """Sends the OTP verification code to the user's email."""
    subject = 'Verify your Metro Ticket Purchase'
    message = f'Your OTP for ticket verification is: {otp}. It expires in 5 minutes.'
    send_mail(
        subject, 
        message, 
        settings.EMAIL_HOST_USER, 
        [user_email], 
        fail_silently=False
    )

def finalize_ticket_booking(request, data):
    """
    Actually creates the ticket, deducts balance, and sends confirmation.
    'data' should contain source_id, destination_id, price, and route_desc.
    """
    user = request.user
    price = Decimal(str(data['price']))
    
    # 1. Deduct Balance
    user.balance -= price
    user.save()

    # 2. Get Station Objects
    source = Station.objects.get(id=data['source_id'])
    dest = Station.objects.get(id=data['destination_id'])
    
    # 3. Create the actual Ticket record
    ticket = Ticket.objects.create(
        user=user,
        source=source,
        destination=dest,
        price=price,
        route_info=data.get('route_desc', 'Direct Trip'),
        status='ACTIVE'
    )

    # 4. Requirement: Send email notification on successful purchase
    send_ticket_confirmation(user.email, ticket)

    # 5. Clean up OTP and temporary ticket data from session
# Ensure these lines are at the end of finalize_ticket_booking in utils.py
    request.session.pop('ticket_data', None)
    request.session.pop('purchase_otp', None)
    request.session.pop('otp_created_at', None)

    return ticket

def send_ticket_confirmation(user_email, ticket):
    subject = f'Ticket Purchased Successfully - {ticket.ticket_id}'
    message = (
        f"Success! Your ticket has been booked.\n\n"
        f"Ticket ID: {ticket.ticket_id}\n"
        f"From: {ticket.source.name}\n"
        f"To: {ticket.destination.name}\n"
        f"Price: ${ticket.price}\n\n"
        f"Route Info: {ticket.route_info}\n\n"
        f"Thank you for using our Metro service!"
    )
    send_mail(
        subject, 
        message, 
        settings.EMAIL_HOST_USER, 
        [user_email], 
        fail_silently=False
    )

