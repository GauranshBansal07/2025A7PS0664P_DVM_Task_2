from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import TicketPurchaseForm, SignUpForm, AddFundsForm, EditProfileForm
from .models import Ticket, Station, SystemSettings, StationOnLine, MetroLine
from .utils import find_shortest_path, generate_otp, send_otp_email, send_ticket_confirmation, finalize_ticket_booking
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
import random, json
from dateutil.parser import parse
from django.contrib.auth import login, logout, authenticate

User = get_user_model()

def home(request):
    settings, _ = SystemSettings.objects.get_or_create(id=1)
    
    # 1. Fetch all active lines
    lines = MetroLine.objects.filter(is_active=True).prefetch_related('stationonline_set__station')

    # 2. Build Graph Data
    nodes = []
    edges = []
    added_station_ids = set()

    for line in lines:
        # Get stations sorted by the order they were added (default ID sort)
        # We rely on 'id' since we are ignoring the manual 'order' field
        stops = list(line.stationonline_set.all().order_by('id'))
        
        for i in range(len(stops)):
            current_stop = stops[i]
            station = current_stop.station
            
            # A. Add Node (Station) if not already added
            if station.id not in added_station_ids:
                nodes.append({
                    'id': station.id,
                    'label': station.name,
                    'shape': 'dot',
                    'size': 20 if current_stop.is_interchange else 10,
                    'color': '#000000' if current_stop.is_interchange else '#666666',
                    'font': {'size': 14, 'color': '#000000', 'face': 'arial'}
                })
                added_station_ids.add(station.id)

            # B. Add Edge (Connection) to the NEXT station in the list
            if i < len(stops) - 1:
                next_stop = stops[i + 1]
                edges.append({
                    'from': station.id,
                    'to': next_stop.station.id,
                    'color': {'color': line.color, 'highlight': line.color},
                    'width': 5, # Thickness of the line
                    'title': line.name # Hover text
                })

    # Convert to JSON string for the template
    graph_data = json.dumps({'nodes': nodes, 'edges': edges})

    return render(request, 'core/home.html', {
        'is_open': settings.is_metro_open,
        'graph_data': graph_data, # Passing the data here
    })

@login_required
def buy_ticket(request):
    # 1. Check if Metro is open
    sys_settings, _ = SystemSettings.objects.get_or_create(id=1)
    if not sys_settings.is_metro_open:
        messages.error(request, "⛔ Metro services are currently CLOSED.")
        return redirect('home')

    if request.method == 'POST':
        source_id = request.POST.get('source')
        dest_id = request.POST.get('destination')
        
        if not source_id or not dest_id:
            messages.error(request, "Please select both a Source and a Destination.")
            return redirect('buy_ticket')
        
        try:
            source = Station.objects.get(id=source_id)
            destination = Station.objects.get(id=dest_id)
        except Station.DoesNotExist:
            messages.error(request, "Invalid station selection.")
            return redirect('buy_ticket')
        
        if source == destination:
            messages.error(request, "Source and Destination cannot be the same.")
            return redirect('buy_ticket')

        # 2. Pathfinding Logic (Requirement: Shortest Route)
        path, lines, stops = find_shortest_path(source.name, destination.name)
        if not path:
             messages.error(request, "No route found between these stations.")
             return redirect('buy_ticket')

        # 3. Generate Route Description (Improved Transfer Detection)
        # We use a helper to ensure it looks professional on the ticket
        from .utils import get_navigation_instructions
        route_desc = get_navigation_instructions(path, lines)

        # 4. Price Calculation (Requirement: Based on Shortest Route)
        # Using 2.0 base + 0.5 per stop is usually more realistic than 2.0 per stop, 
        # but sticking to your logic:
        raw_price = 2.0 + (stops * 2.0)
        price = Decimal(raw_price)

        # 5. Balance Check
        if request.user.balance < price:
            needed_amount = price - request.user.balance
            messages.error(request, f"Insufficient Balance! Need ${needed_amount:.2f} more.")
            return redirect('buy_ticket')

        # 6. OTP & SESSION LOGIC
        ticket_data = {
            'source_id': source.id,
            'destination_id': destination.id,
            'price': float(price), 
            'route_desc': route_desc  # This now contains the transfer instructions
        }
        request.session['ticket_data'] = ticket_data

        if request.user.is_staff:
            ticket = finalize_ticket_booking(request, ticket_data)
            messages.success(request, "Ticket Purchased (Offline Mode).")
            return redirect('ticket_confirmation', ticket_id=ticket.ticket_id)
        else:
            otp = generate_otp()
            request.session['purchase_otp'] = otp
            request.session['otp_created_at'] = str(timezone.now())

            try:
                send_otp_email(request.user.email, otp)
                print(f"DEBUG: OTP sent to {request.user.email} is: {otp}") 
            except Exception as e:
                messages.error(request, f"Email system error: {e}")
                return redirect('buy_ticket')
            
            return redirect('verify_otp_page')

    # GET Request: Sort stations alphabetically for better UX
    stations = Station.objects.all().order_by('name')
    return render(request, 'core/buy_ticket.html', {'stations': stations})

@login_required
def ticket_confirmation(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    return render(request, 'core/ticket_confirmation.html', {'ticket': ticket})

def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            EmailAddress.objects.create(
                user=user,
                email=user.email,
                primary=True,
                verified=False 
            )

            login(request, user, backend='django.contrib.auth.backends.ModelBackend') 
            
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            next_url = request.POST.get('next')
            if next_url and next_url.strip():
                return redirect(next_url)
            return redirect('home')
            
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def add_funds(request):
    if request.method == 'POST':
        form = AddFundsForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            request.user.balance = Decimal(request.user.balance) + Decimal(amount)
            request.user.save()
            messages.success(request, f"Successfully added ${amount} to your wallet!")
            return redirect('buy_ticket')
    else:
        form = AddFundsForm()
    
    return render(request, 'core/add_funds.html', {'form': form})

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/my_tickets.html', {'tickets': tickets})

@login_required
def cancel_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id, user=request.user)
    
    if request.method == 'POST':
        if ticket.status == 'ACTIVE':
            request.user.balance = Decimal(request.user.balance) + ticket.price
            request.user.save()
            
            ticket.status = 'CANCELLED'
            ticket.save()
            
            messages.success(request, f"Ticket cancelled. ${ticket.price} refunded to your wallet.")
        else:
            messages.error(request, "Cannot cancel this ticket (it is used, expired, or already cancelled).")
            
    return redirect('my_tickets')

@login_required
def scanner_view(request):
    user_tickets = Ticket.objects.filter(user=request.user).order_by('-created_at')
    
    all_users = User.objects.all() if request.user.is_superuser else None
    stations = Station.objects.all() if request.user.is_superuser else None

    context = {
        'user_tickets': user_tickets,
        'all_users': all_users,
        'stations': stations
    }
    return render(request, 'core/scanner.html', context)

@login_required
def admin_create_ticket(request):
    if not request.user.is_superuser or request.method != 'POST':
        return redirect('home')
    
    # 1. Get Data safely
    try:
        user_id = request.POST.get('user_id')
        source_id = request.POST.get('source_id')
        dest_id = request.POST.get('dest_id')
        
        passenger = User.objects.get(id=user_id)
        source = Station.objects.get(id=source_id)
        destination = Station.objects.get(id=dest_id)
    except (ValueError, User.DoesNotExist, Station.DoesNotExist):
        messages.error(request, "Invalid data selected.")
        return redirect('scanner')
    
    # 2. Calculate Route
    path, lines, stops = find_shortest_path(source.name, destination.name)
    
    # 3. Generate Detailed "Start/Switch" Instructions
    # (Exact same logic as buy_ticket)
    instructions = []
    route_desc = "Direct Trip"

    if lines and len(lines) > 0:
        current_line = lines[0]
        instructions.append(f"Start on {current_line}")
        
        # Loop to find where the line changes
        for i in range(len(lines) - 1):
            if lines[i] != lines[i+1]:
                # The station at path[i+1] is the transfer point
                transfer_station = path[i+1]
                next_line = lines[i+1]
                instructions.append(f"Switch to {next_line} at {transfer_station}")

        route_desc = ". ".join(instructions) + "."
    
    # 4. Price & Save
    raw_price = 2.0 + (stops * 2.0)
    price = Decimal(raw_price)

    Ticket.objects.create(
        user=passenger,
        source=source,
        destination=destination,
        price=price,
        status='USED', 
        route_info=route_desc, # Now saves: "Start on Green. Switch to Orange at Lionel-Groulx."
        entry_time=timezone.now(),
        exit_time=timezone.now()
    )
        
    messages.success(request, "Ticket created manually.")
    return redirect('scanner')

@staff_member_required
def admin_analytics(request):
    today = timezone.now().date()
    stations = Station.objects.all()
    stats = []

    for station in stations:
        entries = Ticket.objects.filter(source=station, entry_time__date=today).count()
        exits = Ticket.objects.filter(destination=station, exit_time__date=today).count()
        
        stats.append({
            'name': station.name,
            'entries': entries,
            'exits': exits,
            'total': entries + exits
        })
    
    context = {
        'stats': stats,
        'today': today,
        'title': 'Daily Footfall Analytics'
    }
    return render(request, 'admin/admin_analytics.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('home') 
    else:
        form = EditProfileForm(instance=request.user)

    return render(request, 'core/edit_profile.html', {'form': form})

@login_required
def verify_otp_page(request):

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('purchase_otp')
        otp_time_str = request.session.get('otp_created_at')
        ticket_data = request.session.get('ticket_data')

        if not ticket_data or not session_otp or not otp_time_str:
            messages.error(request, "Session expired or invalid request. Please start your purchase again.")
            return redirect('buy_ticket')

        try:
            otp_time = parse(otp_time_str)
            if timezone.now() > otp_time + timedelta(minutes=5):
                request.session.pop('purchase_otp', None)
                request.session.pop('otp_created_at', None)
                messages.error(request, "The OTP has expired. Please try again.")
                return redirect('buy_ticket')
        except Exception as e:
            messages.error(request, "An error occurred during verification.")
            return redirect('buy_ticket')

        if entered_otp == session_otp:
            ticket = finalize_ticket_booking(request, ticket_data)
            
            messages.success(request, "OTP Verified! Your ticket has been booked successfully.")
            return redirect('ticket_confirmation', ticket_id=ticket.ticket_id)
        else:
            messages.error(request, "Invalid OTP code. Please check your email and try again.")
    
    return render(request, 'core/verify_otp.html')