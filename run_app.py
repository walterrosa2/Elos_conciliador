# run_app.py — versão com suporte ao Ngrok
import socket
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

def get_local_ip(default="127.0.0.1") -> str:
    """Detecta o IP local da LAN para exibição."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return default

#def iniciar_ngrok(porta=8506) -> str | None:
#    from pyngrok import ngrok
 #   token = os.getenv("NGROK_AUTHTOKEN")
 #   subdomain = os.getenv("NGROK_SUBDOMAIN")
 #   if token:
 #       ngrok.set_auth_token(token)
 #   options = {"addr": f"http://127.0.0.1:{porta}", "bind_tls": True}
 #   if subdomain:
 #       options["subdomain"] = subdomain
 #   url = ngrok.connect(**options)
 #   print(f"🌍 URL pública (Ngrok): {url}")
 #   return str(url)

if __name__ == "__main__":
    # Porta padrão
    port = int(os.getenv("PORT", "8506"))

    # Variável de controle
#    use_ngrok = os.getenv("USE_NGROK", "0").lower() in {"1", "true", "yes"}

    # Detecta IP local apenas para exibir
    ip_lan = get_local_ip()

 #   if use_ngrok:
 #       public_url = iniciar_ngrok(port)
 #       if public_url:
 #           print(f"✅ Aplicação acessível via Ngrok: {public_url}")
 #       else:
 #           print("⚠️ Rodando apenas na rede local (Ngrok falhou).")

    # Exibe os endereços locais
    print(f"🚀 Acesse na LAN:   http://{ip_lan}:{port}")
    print(f"🚀 Acesse local:   http://127.0.0.1:{port}")

    # Inicia o Streamlit apontando para app.py
    subprocess.run([
        "streamlit", "run", "app.py",
        "--server.address", "0.0.0.0",
        "--server.port", str(port),
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ])
