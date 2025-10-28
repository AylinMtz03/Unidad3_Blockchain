from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Wallet
from .models import Wallet, Contacto
from django.shortcuts import render
from django.http import JsonResponse
from algosdk.v2client import algod, indexer
from algosdk import account


def envio(request):
    return render(request, 'wallet/envio.html')

def index(request):
    """Página de consulta simple (plantilla index.html)"""
    return render(request, 'wallet/index.html')

def info(request):
    """Página de información del usuario (plantilla info.html)"""
    return render(request, 'wallet/info.html')

def contacto(request):
    """Página de contactos o formulario de contacto (plantilla contacto.html)"""
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        return render(request, "wallet/no_wallet.html")

    contactos = Contacto.objects.filter(wallet=wallet)
    return render(request, 'wallet/contacto.html', {'contactos': contactos})

def login_view(request):
    """Vista de login (index principal)"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('mi_wallet')
        else:
            return render(request, 'wallet/login.html', {'error': 'Credenciales incorrectas'})
    return render(request, 'wallet/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

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
    

@login_required
def mi_wallet(request):
    """Muestra los datos del dueño de la wallet (usuario autenticado)"""
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        return render(request, "wallet/no_wallet.html")

    algod_client = algod.AlgodClient("", "https://testnet-api.algonode.cloud")
    account_info = algod_client.account_info(wallet.address)

    datos = {
        "user": request.user,
        "address": wallet.address,
        "balance": account_info.get('amount', 0) / 1_000_000,
        "txs": len(account_info.get('assets', [])),
    }

    return render(request, "wallet/mi_wallet.html", datos)

@login_required
def transacciones(request):
    """Consulta transacciones reales de la wallet del usuario (en testnet)"""
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        return render(request, "wallet/no_wallet.html")

    # Cliente del indexer público (para leer transacciones)
    client = indexer.IndexerClient("", "https://testnet-idx.algonode.cloud")

    try:
        # Consultar las últimas transacciones enviadas o recibidas por la dirección
        response = client.search_transactions_by_address(wallet.address, limit=10)
        txs = response.get("transactions", [])
    except Exception as e:
        txs = []
        error = f"Error al obtener transacciones: {e}"
        return render(request, "wallet/transacciones.html", {"txs": txs, "error": error})

    # Convertir datos para mostrar en la plantilla
    transacciones = []
    for tx in txs:
        tipo = tx.get("tx-type", "desconocido")
        monto = tx.get("payment-transaction", {}).get("amount", 0) / 1_000_000
        receptor = tx.get("payment-transaction", {}).get("receiver", "")
        remitente = tx.get("sender", "")
        fecha = tx.get("round-time", 0)
        transacciones.append({
            "tipo": tipo,
            "monto": monto,
            "receptor": receptor,
            "remitente": remitente,
            "fecha": fecha,
        })

    return render(request, "wallet/transacciones.html", {
        "transacciones": transacciones,
        "address": wallet.address,
    })

@login_required
def configuracion(request):
    return render(request, "wallet/configuracion.html")

@login_required
def registrar_wallet(request):
    """Crea una nueva wallet Algorand y la asocia al usuario"""
    if request.method == "POST":
        # Verificamos si ya tiene wallet
        if Wallet.objects.filter(user=request.user).exists():
            return render(request, "wallet/registrar_wallet.html", {
                "error": "Ya tienes una wallet registrada."
            })

        # Generamos la wallet
        private_key, address = account.generate_account()

        # Guardamos en la base de datos
        Wallet.objects.create(
            user=request.user,
            address=address,
            private_key=private_key
        )

        return redirect("mi_wallet")

    return render(request, "wallet/registrar_wallet.html")


@login_required
def agregar_contacto(request):
    """Formulario para agregar un contacto asociado a la wallet del usuario."""
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        return render(request, "wallet/no_wallet.html")

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        contact_wallet = request.POST.get('contact_wallet')
        if nombre and email:
            Contacto.objects.create(nombre=nombre, email=email, wallet=wallet, contact_wallet=contact_wallet)
            return redirect('contacto')
        else:
            return render(request, 'wallet/agregar_contacto.html', {'mensaje': 'Completa todos los campos.', 'wallet_address': wallet.address})

    return render(request, 'wallet/agregar_contacto.html', {'wallet_address': wallet.address})