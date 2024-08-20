import json
import os
from datetime import datetime, timedelta

CACHE_FILE = 'model_cache.json'
CACHE_EXPIRY_DAYS = 7

def load_cached_models(service_name):
    print(f"Loading cached models for {service_name}...")
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        
        if service_name in cache:
            last_updated = datetime.fromisoformat(cache[service_name]['last_updated'])
            if datetime.now() - last_updated < timedelta(days=CACHE_EXPIRY_DAYS):
                print(f"Cache hit for {service_name}: {cache[service_name]['models']}")
                return cache[service_name]['models']
    
    print(f"No valid cache found for {service_name}.")
    return None

def save_cached_models(service_name, models):
    print(f"Saving models to cache for {service_name}: {models}")
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
    
    cache[service_name] = {
        'models': models,
        'last_updated': datetime.now().isoformat()
    }
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)
    print(f"Cache updated for {service_name}.")