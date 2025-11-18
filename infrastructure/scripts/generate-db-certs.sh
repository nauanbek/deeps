#!/bin/bash
# Generate SSL certificates for PostgreSQL
#
# Usage: ./generate-db-certs.sh
#
# This script generates self-signed certificates for PostgreSQL SSL.
# For production, use proper CA-signed certificates.

set -e

CERT_DIR="/var/lib/postgresql/data/certs"
VALIDITY_DAYS=365

echo "=== PostgreSQL SSL Certificate Generation ==="
echo "Certificate directory: $CERT_DIR"
echo "Validity: $VALIDITY_DAYS days"
echo ""

# Create certificate directory
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

# Generate private key
echo "Generating private key..."
openssl genrsa -out server.key 2048
chmod 600 server.key
chown postgres:postgres server.key

# Generate certificate signing request
echo "Generating certificate signing request..."
openssl req -new -key server.key -out server.csr \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=postgres.local"

# Generate self-signed certificate
echo "Generating self-signed certificate..."
openssl x509 -req -in server.csr -signkey server.key \
    -out server.crt -days $VALIDITY_DAYS

# Set permissions
chmod 644 server.crt
chown postgres:postgres server.crt

# Clean up CSR
rm server.csr

echo ""
echo "✅ SSL certificates generated successfully!"
echo ""
echo "Files created:"
echo "  - $CERT_DIR/server.key (private key)"
echo "  - $CERT_DIR/server.crt (certificate)"
echo ""
echo "Next steps:"
echo "1. Add to postgresql.conf: include = 'postgresql-ssl.conf'"
echo "2. Update pg_hba.conf: hostssl entries for SSL connections"
echo "3. Restart PostgreSQL: systemctl restart postgresql"
echo "4. Test connection: psql 'postgresql://user@host/db?sslmode=require'"
