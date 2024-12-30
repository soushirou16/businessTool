import time
import requests

addresses = [
    "53 Rue de Seine, 75006 Paris, France",
    "96 Rue Saint-martin, 75004 Paris, France",
    "5 Rue Des Deux Boules, 75001 Paris, France",
    "9 Quai Saint-michel, 75005 Paris, France",
    "1 Rue Ernest Cresson, 75014 Paris, France",
    "16 Rue de Gergovie, 75014 Paris, France",
    "21 Rue Jules Michelet, 92170 Vanves, France",
    "72 Rue Sadi Carnot, 92170 Vanves, France",
    "16 Rue Antoine Fratacci, 92170 Vanves, France",
    "2 Rue Vieille Forge, 92170 Vanves, France"
]

url = 'https://api.geoapify.com/v1/batch/geocode/search?apiKey=b4c75e67dae1497492698c563da01626'

response = requests.post(url, json=addresses, headers={
    'Accept': 'application/json',
    'Content-Type': 'application/json'
})

if response.status_code != 202:
    print(f"Error: {response.status_code}, {response.text}")
else:
    result = response.json()
    print(f"Full response: {result}")  # Debug: Print the entire response
    job_id = result['id']
    job_url = result['url']
    print(f"Job ID: {job_id}")
    print(f"Job URL: {job_url}")
    print(f"Job ID type: {type(job_id)}")  # Debug: Check the type of job_id

    # Get the results asynchronously
    def get_async_result(url, timeout, max_attempts):
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            print(f"Attempt: {attempts}")
            res = requests.get(f"{url}&id={str(job_id)}", headers={  # Ensure job_id is treated as string
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
            if res.status_code == 200:
                return res.json()
            elif res.status_code == 202:
                # Wait before trying again
                time.sleep(timeout / 1000)  # Convert timeout from ms to seconds
            else:
                raise Exception(f"Error fetching result: {res.status_code}, {res.text}")
        raise Exception("Max attempts reached")

    # Get the result after a successful job completion
    try:
        result_data = get_async_result(job_url, timeout=60000, max_attempts=100)  # Check every minute, max 100 attempts
        print(result_data)
    except Exception as e:
        print(f"Error: {e}")
