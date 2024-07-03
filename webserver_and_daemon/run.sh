set -e

# Print env
env

# If DATABASE_PASSWORD_SECRET_NAME is set, fetch the secret from GCP and set it as an environment variable
if [ -n "$DATABASE_PASSWORD_SECRET_NAME" ]; then
  echo "Fetching secret from GCP"
  password=$(./.venv/bin/python scripts/get_secret.py)
  export DATABASE_PASSWORD=$password
fi

echo "Running command: $@"
"$@"
