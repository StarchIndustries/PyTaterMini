import requests, json, time
from hashlib import sha256

host = "https://api.starch.one"
company_id = "FEE600"
color = f"#{company_id}"

def get_miner_ids():
    try:
        return json.loads(requests.get(f"{host}/teams/{company_id}/members").text)
    except Exception as e:
        print(e)
        return {"members": []}

def get_last_block():
    try:
        return json.loads(requests.get(f"{host}/blockchain/last_block").text)
    except Exception as e:
        print(e)
        return {}

def solve(miner_id, last_block):
    last_hash = last_block["hash"]
    string = f'{last_hash} {miner_id} {color}'
    new_hash = sha256(string.encode()).hexdigest()
    return {"hash": new_hash, "miner_id": miner_id, "color": color}

def submit_blocks(blocks):
    try:
        data = {"blocks": blocks}
        return json.loads(requests.post(f"{host}/submit_blocks", json=data).text)
    except Exception as e:
        print(e)
        return []

def mine():
    last_block = get_last_block()
    if last_block == {}:
        return

    blocks = []
    miner_ids = get_miner_ids()["members"]
    for miner_id in miner_ids:
        blocks.append(solve(miner_id, last_block))

    status = submit_blocks(blocks)
    for x in status:
        print(x, status[x]["block"])

print(f"pytater mini : mining for {company_id}")

while True:
    mine()
    time.sleep(49)
