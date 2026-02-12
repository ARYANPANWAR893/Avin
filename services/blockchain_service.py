import uuid

def write_proof_to_blockchain(mission_id, before_hash, after_hash):

    # later: connect to your local chain node

    tx_id = str(uuid.uuid4())

    return {
        "tx_id": tx_id,
        "mission_id": mission_id
    }