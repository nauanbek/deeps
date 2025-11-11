#!/bin/bash
# Generate SSL certificates for Redis
#
# Usage: ./generate-redis-certs.sh
#
# This script generates self-signed certificates for Redis TLS.
# For production, use proper CA-signed certificates.

set -e

CERT_DIR="/etc/redis/certs"
VALIDITY_DAYS=365

echo "=== Redis SSL Certificate Generation ==="
echo "Certificate directory: $CERT_DIR"
echo "Validity: $VALIDITY_DAYS days"
echo ""

# Create certificate directory
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

# Generate private key and certificate in one step
echo "Generating private key and self-signed certificate..."
openssl req -x509 -newkey rsa:4096 \
    -keyout redis.key \
    -out redis.crt \
    -days $VALIDITY_DAYS \
    -nodes \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=redis.local"

# Set permissions
chmod 600 redis.key
chmod 644 redis.crt
chown redis:redis redis.key redis.crt 2>/dev/null || true

echo ""
echo "✅ SSL certificates generated successfully!"
echo ""
echo "Files created:"
echo "  - $CERT_DIR/redis.key (private key)"
echo "  - $CERT_DIR/redis.crt (certificate)"
echo ""
echo "Next steps:"
echo "1. Add to redis.conf: include /path/to/redis-ssl.conf"
echo "2. Set a strong password in redis-ssl.conf"
echo "3. Restart Redis: systemctl restart redis"
echo "4. Test connection: redis-cli --tls --cert redis.crt --key redis.key --cacert redis.crt"
