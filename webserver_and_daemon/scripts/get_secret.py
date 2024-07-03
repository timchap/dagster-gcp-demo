import os

from google.cloud import secretmanager_v1 as sm


def __main__():
    client = sm.SecretManagerServiceClient()

    secret_name = os.environ['DATABASE_PASSWORD_SECRET_NAME']
    request = sm.AccessSecretVersionRequest(name=secret_name)
    resp = client.access_secret_version(request)
    print(resp.payload.data.decode('UTF-8'))


if __name__ == '__main__':
    __main__()
