# This script supports multiple miners, and runs with asyncronous api calls.
# This script uses modified code from PyTater https://github.com/Crypto2099/PyTater

import asyncio
import hashlib
import httpx
import json
import os
import random
import zlib

from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

miner_id_1 = os.getenv('miner_id_1')
miner_id_2 = os.getenv('miner_id_2')
all_miners = [miner_id_1, miner_id_2]





def random_color(miner_id, block_hash: str):
    seed = zlib.crc32(bytes(block_hash + miner_id, 'ascii'))
    random.seed(seed)
    random_number = random.randint(0, 16777215)
    hex_number = '{0:06X}'.format(random_number)
    return '#' + hex_number


async def get_status(miner_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'https://starch.one/api/miner/{miner_id}', timeout=10)
    except:
        print("Could not fetch status")
        return None, None
    try:
        payload = response.json()
    except:
        print("Could not decode status")
        return None, None
    try:
        starch_balance = payload['balance']
        block_count = payload['blocks']
        return starch_balance, block_count
    except:
        return None, None

async def get_pending():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get('https://starch.one/api/pending_blocks', timeout=10)
    except:
        print("Could not fetch pending!")
        return []
    try:
        response = res.json()
    except json.decoder.JSONDecodeError:
        print(f"Could not decode pending!")
        return []
    if len(response.get('pending_blocks', [])) != 0:
        pending_blocks = response['pending_blocks']
        return pending_blocks
    else:
        return []

def get_miner_blocks(miner_id, pending_blocks):
    miner_block, miner_block_hash = None, None
    for block in pending_blocks:
        if block['miner_id'] == miner_id:
            miner_block = block
            miner_block_hash = block['previous_hash']
            break
    return miner_block, miner_block_hash






async def get_chain_config(block_height):
    last_block, last_block_hash = None, None
    # logging.info("Getting chain config...")
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get('https://starch.one/api/blockchain_config', timeout=10)
    except:
        # 15639bc8e9...974951272c
        print("Could not fetch configuration!")
        return block_height, last_block, last_block_hash
    try:
        response = res.json()
    except:
        print("Could not decode configuration!")
        return block_height, block_height, last_block, last_block_hash
    try:
        if response.get('blockchain_size', 0) > block_height:
            block_height = response['blockchain_size']
            last_block = response['last_block']
            last_block_hash = last_block['hash']
            return block_height, last_block, last_block_hash
        else:
            return block_height, last_block, last_block_hash
    except:
        return block_height, last_block, last_block_hash

def solve(last_block_hash, miner_id):
    color = random_color(miner_id, last_block_hash)
    print(f"Solving New Block:\nHash: {last_block_hash}\nMiner ID: {miner_id}\nColor: {color}")
    solution = last_block_hash + " " + miner_id + " " + color
    m = hashlib.sha256()
    m.update(bytes(solution, 'ascii'))
    new_hash = m.hexdigest()
    print(f"Block hash: {new_hash}")
    return {'hash': new_hash, 'color': color, 'miner_id': miner_id}

async def submit_block(new_block):
    print("Unearthing $STRCH treasures with potato prowess... Mining spudtastic crypto gold.")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post('https://starch.one/api/submit_block', json=new_block, timeout=10)
    except:
        print("Could not submit block?!")
        return False
    print("New block submitted to the chain!")
    return True

async def run_miner():
    total_runs = 0
    block_height = 0
    submitted_blocks = 0
    while True:
        total_runs += 1
        while True:
            current_block_height, current_block, current_block_hash = await get_chain_config(block_height)
            if current_block_height == 0:
                await asyncio.sleep(10)
                continue
            break
        if current_block_height > block_height:
            block_height = current_block_height
            print(f'Block Height: {block_height}')
            while True:
                pending_blocks = await get_pending()
                if len(pending_blocks) == 0:
                    await asyncio.sleep(10)
                    continue
                break
            for miner_id in all_miners:
                miner_block, miner_block_hash = get_miner_blocks(miner_id, pending_blocks)
                if miner_block is None:
                    new_block = solve(current_block_hash, miner_id)
                    while True:
                        submit_success = await submit_block(new_block)
                        await asyncio.sleep(10)
                        if submit_success:
                            break
                    submitted_blocks += 1
                    if block_height != 0 and block_height % 10 == 0:
                        starch_balance, block_count = await get_status(miner_id)
                        print(f'Miner Stats for Miner ID #{miner_id}:\nStarch Balance: {starch_balance}\nBlock Count: {block_count}')
        current_time = datetime.now().strftime("%m-%d-%Y %Hh%Mm%Ss UTC")
        print(f'Miner Running.  Mining for {len(all_miners)} miner(s).\nCurrent Time: {current_time}\nSubmitted Blocks Since Starting: {submitted_blocks}\nTotal Runs: {total_runs}')
        await asyncio.sleep(35)

asyncio.run(run_miner())