import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import NegotiationSession, DialogueTurn, OfferHistory
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

BUYER_RESERVATION_PRICE = 25_000_000


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def start_session(request):
    active_session = NegotiationSession.objects.filter(
        user=request.user,
        status=NegotiationSession.STATUS_ACTIVE
    ).first()

    if active_session:
        return JsonResponse({
            'error': 'You already have an active negotiation session.',
            'session_id': active_session.pk
        }, status=400)

    session = NegotiationSession.objects.create(user=request.user)

    return JsonResponse({
        'session_id': session.pk,
        'status': session.status,
        'turn_count': session.turn_count,
        'created_at': session.created_at.isoformat(),
        'message': 'Session started. You are the buyer. Good luck!'
    }, status=201)


@login_required
@require_http_methods(["GET"])
def get_session(request, session_id):
    try:
        session = NegotiationSession.objects.get(pk=session_id, user=request.user)
    except NegotiationSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found or access denied.'}, status=404)

    turns = list(session.turns.values(
        'speaker', 'message', 'turn_number', 'created_at'
    ).order_by('turn_number', 'created_at'))

    offers = list(session.offers.values(
        'sender', 'offer_value', 'turn_number', 'concession_amount',
        'concession_percentage', 'created_at'
    ).order_by('turn_number', 'created_at'))

    response_data = {
        'session_id': session.pk,
        'status': session.status,
        'turn_count': session.turn_count,
        'max_turns': 5,
        'turns_remaining': max(0, 5 - session.turn_count),
        'dialogue': turns,
        'offers': offers,
        'created_at': session.created_at.isoformat(),
    }

    if session.status == NegotiationSession.STATUS_COMPLETED:
        response_data.update({
            'outcome': session.outcome,
            'final_price': session.final_price,
            'human_profit': session.human_profit,
            'ai_profit': session.ai_profit,
            'ended_at': session.ended_at.isoformat() if session.ended_at else None,
        })

    return JsonResponse(response_data, status=200)


def validate_turn(session):
    if session.status != NegotiationSession.STATUS_ACTIVE:
        return False, 'This session is already completed.'
    if session.turn_count >= 5:
        return False, 'Maximum number of turns (5) reached. Please submit your final offer.'
    return True, None


def increment_turn(session):
    session.turn_count += 1
    session.save(update_fields=['turn_count'])
    return session.turn_count


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def submit_final_offer(request, session_id):
    try:
        session = NegotiationSession.objects.get(pk=session_id, user=request.user)
    except NegotiationSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found or access denied.'}, status=404)

    if session.status != NegotiationSession.STATUS_ACTIVE:
        return JsonResponse({'error': 'This session is already completed.'}, status=400)

    try:
        body = json.loads(request.body)
        final_offer = float(body.get('final_offer'))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'error': 'Invalid body. Expected JSON with "final_offer" (number).'}, status=400)

    if final_offer <= 0:
        return JsonResponse({'error': 'Final offer must be a positive number.'}, status=400)

    acceptance_threshold = session.ai_reservation_price * 0.95
    accepted = final_offer >= acceptance_threshold

    if accepted:
        human_profit = BUYER_RESERVATION_PRICE - final_offer
        ai_profit = final_offer - session.ai_reservation_price
        outcome = NegotiationSession.OUTCOME_ACCEPTED
        ai_message = f"I accept your offer of ${final_offer:,.0f}. We have a deal!"
    else:
        human_profit = 0.0
        ai_profit = 0.0
        outcome = NegotiationSession.OUTCOME_DECLINED
        ai_message = f"I cannot accept ${final_offer:,.0f}. This is below what I can accept."

    session.outcome = outcome
    session.final_price = final_offer
    session.human_profit = human_profit
    session.ai_profit = ai_profit
    session.status = NegotiationSession.STATUS_COMPLETED
    session.ended_at = timezone.now()
    session.save()

    return JsonResponse({
        'outcome': outcome,
        'final_price': final_offer,
        'ai_decision': ai_message,
        'human_profit': human_profit,
        'ai_profit': ai_profit,
        'session_id': session.pk,
        'ended_at': session.ended_at.isoformat(),
    }, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def SignupView(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'User already exists'}, status=400)

        user = User.objects.create_user(username=username, password=password)

        return JsonResponse({'message': 'User created successfully'}, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def LoginView(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is None:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

        login(request, user)

        return JsonResponse({'message': 'Login successful'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def submit_final_offer(request, session_id):
    return JsonResponse({'message': 'Final offer submitted'}, status=200)