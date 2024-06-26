import requests
import json
import math
from base64 import b64encode
from hashlib import sha256
from hmac import new as hmac_new
from time import time

# Replace these with your API key and secret
API_KEY = 'VqjFWqvS4xGkLqaZg7Vr13My '
API_SECRET = 'kyeNKmmZkIj1qKkc2ehlvo3BQhDvbKpaYh4pPDI3ccywL73r'


def generate_nonce():
    return str(int(time() * 1000))

def generate_auth_header(method, url, nonce):
    auth = b64encode(hmac_new(API_SECRET.encode(), f'{method} {url} {nonce}'.encode(), sha256).digest()).decode()
    return f'Bearer {API_KEY}:{auth}'

def create_document():
    url = 'https://cad.onshape.com/api/documents'
    headers = {
        'Content-Type': 'application/json',
        'On-Nonce': generate_nonce(),
    }
    headers['On-Authorization'] = generate_auth_header('POST', url, headers['On-Nonce'])

    data = {
        "name": "Wind Turbine Design",
        "ownerType": 0
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        document = response.json()
        return document
    else:
        print(f'Error creating document: {response.text}')
        return None

document = create_document()

if document:
    document_id = document["id"]
    print(f'Document ID: {document_id}')
    print(f'Document URL: https://cad.onshape.com/documents/{document_id}')

    # Create a workspace
    url = f'https://cad.onshape.com/api/documents/{document_id}/workspaces'
    headers['On-Nonce'] = generate_nonce()
    headers['On-Authorization'] = generate_auth_header('POST', url, headers['On-Nonce'])

    data = {
        "name": "Workspace 1"
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        workspace = response.json()
        workspace_id = workspace["id"]
        print(f'Workspace ID: {workspace_id}')
    else:
        print(f'Error creating workspace: {response.text}')
        workspace_id = None
else:
    workspace_id = None

def create_turbine(document_id, workspace_id, holeDiameter, shaftDiameter, outerDiameter, bladeThickness, bladeDepth, turbineHeight, bladeCount, twistCount):
    if not document_id or not workspace_id:
        print("Invalid document or workspace ID.")
        return

    url = f'https://cad.onshape.com/api/partstudios/d/{document_id}/w/{workspace_id}/e/{element_id}/features'
    headers = {
        'Content-Type': 'application/json',
        'On-Nonce': generate_nonce(),
    }
    headers['On-Authorization'] = generate_auth_header('POST', url, headers['On-Nonce'])

    # Create the shaft (cylinder)
    features = [
        {
            "featureType": "cylinder",
            "parameters": {
                "diameter": shaftDiameter,
                "height": turbineHeight,
                "position": {"x": 0, "y": 0, "z": 0}
            }
        }
    ]

    # Create the hexagon
    radius = holeDiameter / 2.0
    hexagon_points = []
    for i in range(6):
        angle_deg = 60 * i - 30
        angle_rad = math.radians(angle_deg)
        x = radius * math.cos(angle_rad)
        y = radius * math.sin(angle_rad)
        hexagon_points.append({"x": x, "y": y})

    features.append({
        "featureType": "polygon",
        "parameters": {
            "vertices": hexagon_points,
            "height": turbineHeight,
            "operation": "join"
        }
    })

    data = {"features": features}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        print('Turbine inner structure created successfully.')
    else:
        print(f'Error creating turbine: {response.text}')

# Example usage
if document_id and workspace_id:
    create_turbine(document_id, workspace_id, 5, 10, 20, 1, 5, 100, 3, 2)