import time
import requests


def retry_request(url, headers=None, retries=3):
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=20)

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            print(f"Retry {i+1}: {e}")
            time.sleep(2)

    return None