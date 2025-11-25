"""
Broker configurations with available servers
Add more brokers as needed
"""

BROKER_CONFIGS = {
    "XM": {
        "name": "XM Global",
        "servers": [
            {"name": "XMGlobal-MT5", "description": "XM Global Server"},
            {"name": "XMGlobal-MT5 2", "description": "XM Global Server 2"},
            {"name": "XMGlobal-MT5 3", "description": "XM Global Server 3"},
        ]
    },
    "Exness": {
        "name": "Exness",
        "servers": [
            {"name": "Exness-MT5Real", "description": "Exness Real Server"},
            {"name": "Exness-MT5Real2", "description": "Exness Real Server 2"},
            {"name": "Exness-MT5Real3", "description": "Exness Real Server 3"},
            {"name": "Exness-MT5Trial", "description": "Exness Demo Server"},
        ]
    },
    "FXTM": {
        "name": "FXTM (ForexTime)",
        "servers": [
            {"name": "ForexTimeFXTM-Server", "description": "FXTM Main Server"},
            {"name": "ForexTimeFXTM-Server2", "description": "FXTM Server 2"},
        ]
    },
    "IC Markets": {
        "name": "IC Markets",
        "servers": [
            {"name": "ICMarketsSC-MT5", "description": "IC Markets Seychelles"},
            {"name": "ICMarketsSC-MT5-2", "description": "IC Markets Seychelles 2"},
        ]
    },
    "Pepperstone": {
        "name": "Pepperstone",
        "servers": [
            {"name": "Pepperstone-MT5-Live01", "description": "Pepperstone Live 1"},
            {"name": "Pepperstone-MT5-Live02", "description": "Pepperstone Live 2"},
            {"name": "Pepperstone-MT5-Demo", "description": "Pepperstone Demo"},
        ]
    },
}

def get_broker_servers(broker_name: str):
    """Get available servers for a broker"""
    broker = BROKER_CONFIGS.get(broker_name)
    if not broker:
        return None
    return broker["servers"]

def get_all_brokers():
    """Get all available brokers"""
    return [
        {
            "broker_name": key,
            "display_name": value["name"],
            "servers": value["servers"]
        }
        for key, value in BROKER_CONFIGS.items()
    ]
