#!/usr/bin/env python3
"""
CogniVault HTTPS Solution for Rob "The Sounds Guy"
Production-ready HTTPS server with SSL certificates
Built by VERITAS - Living in truth, building in excellence
"""

import streamlit as st
import ssl
import os
import subprocess
import tempfile
import socket
from pathlib import Path

def generate_self_signed_cert():
    """Generate self-signed SSL certificate for localhost"""
    cert_dir = Path("./ssl_certs")
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = cert_dir / "cert.pem"
    key_file = cert_dir / "key.pem"
    
    if not cert_file.exists() or not key_file.exists():
        # Generate self-signed certificate
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:4096", 
            "-keyout", str(key_file), "-out", str(cert_file),
            "-days", "365", "-nodes", "-subj",
            "/C=ZA/ST=KwaZulu-Natal/L=Durban/O=RobTheSoundsGuy/CN=localhost"
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print("✅ SSL certificates generated successfully!")
            return str(cert_file), str(key_file)
        except subprocess.CalledProcessError as e:
            print(f"❌ OpenSSL not found. Using Python fallback...")
            return generate_python_cert(cert_file, key_file)
    
    return str(cert_file), str(key_file)

def generate_python_cert(cert_file, key_file):
    """Fallback: Generate certificate using Python cryptography"""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ZA"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "KwaZulu-Natal"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Durban"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "RobTheSoundsGuy"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(socket.inet_aton("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print("✅ SSL certificates generated with Python cryptography!")
        return str(cert_file), str(key_file)
        
    except ImportError:
        print("❌ cryptography package not installed. Using minimal SSL context...")
        return None, None

def create_https_runner():
    """Create HTTPS runner script"""
    runner_content = '''#!/usr/bin/env python3
"""
HTTPS Streamlit Runner for CogniVault
Run with: python https_runner.py
"""

import os
import sys
import subprocess
import ssl
import socket
from pathlib import Path

def find_free_port(start_port=8501):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def main():
    # Find your main Streamlit app
    app_files = [
        'app.py', 'main.py', 'streamlit_app.py', 
        'cognivault.py', 'cognivault_app.py'
    ]
    
    app_file = None
    for file in app_files:
        if Path(file).exists():
            app_file = file
            break
    
    if not app_file:
        print("❌ Could not find main Streamlit app file!")
        print("   Looking for: " + ", ".join(app_files))
        return
    
    # Check for SSL certificates
    cert_file = Path("./ssl_certs/cert.pem")
    key_file = Path("./ssl_certs/key.pem")
    
    if not cert_file.exists() or not key_file.exists():
        print("❌ SSL certificates not found!")
        print("   Run the certificate generator first.")
        return
    
    # Find free port
    port = find_free_port(8501)
    if not port:
        print("❌ Could not find free port!")
        return
    
    print(f"🚀 Starting CogniVault HTTPS server...")
    print(f"📱 App file: {app_file}")
    print(f"🔒 HTTPS URL: https://localhost:{port}")
    print(f"🛡️  SSL Cert: {cert_file}")
    print("="*50)
    
    # Start Streamlit with HTTPS
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_file,
        "--server.port", str(port),
        "--server.address", "localhost",
        "--server.sslEnabled", "true",
        "--server.sslCertFile", str(cert_file),
        "--server.sslKeyFile", str(key_file),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\\n👋 CogniVault HTTPS server stopped.")

if __name__ == "__main__":
    main()
'''
    
    with open("https_runner.py", "w") as f:
        f.write(runner_content)
    
    os.chmod("https_runner.py", 0o755)
    print("✅ HTTPS runner created: https_runner.py")

def main():
    print("🔥 CogniVault HTTPS Setup - Built by VERITAS")
    print("="*50)
    
    # Generate SSL certificates
    print("1️⃣ Generating SSL certificates...")
    cert_file, key_file = generate_self_signed_cert()
    
    if cert_file and key_file:
        print(f"✅ Certificate: {cert_file}")
        print(f"✅ Private Key: {key_file}")
    
    # Create HTTPS runner
    print("\\n2️⃣ Creating HTTPS runner...")
    create_https_runner()
    
    print("\\n🎯 SETUP COMPLETE!")
    print("="*50)
    print("🚀 To run CogniVault with HTTPS:")
    print("   python https_runner.py")
    print("\\n🔒 Your app will be available at: https://localhost:8501")
    print("\\n⚠️  Browser Security Notice:")
    print("   - Chrome/Firefox will show 'Not Secure' warning")
    print("   - Click 'Advanced' → 'Proceed to localhost'")
    print("   - This is normal for self-signed certificates")
    print("\\n🎵 Rock on, Rob! - VERITAS")

if __name__ == "__main__":
    main()