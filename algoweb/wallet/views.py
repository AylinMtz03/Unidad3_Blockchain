from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
from algosdk.v2client import algod

def index(request):
    return render(request, 'wallet/index.html')

def get_balance(request):
    address = request.GET.get('address', '')
    if not address:
        return JsonResponse({"error": "Missing address"}, status=400)

    algod_client = algod.AlgodClient("", "https://testnet-api.algonode.cloud")
    try:
        account_info = algod_client.account_info(address)
        balance = account_info.get('amount', 0) / 1_000_000  # convertir microAlgos a Algos
        return JsonResponse({"address": address, "balance": balance})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)