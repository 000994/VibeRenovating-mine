from models.database import Database

db = Database()
keys = db.get_all_api_keys()

if not keys:
    print("数据库中没有任何 API Key")
else:
    for provider, info in keys.items():
        ak = info.get("api_key", "")
        sk = info.get("secret_key", "")
        print(f"{provider}: api_key={ak[:10]}... secret_key={'有' if sk else '无'}")
