import os

def legacy_parser(data):
    # Deeply nested logic without tests
    if data:
        if isinstance(data, dict):
            if "items" in data:
                if len(data["items"]) > 0:
                    for item in data["items"]:
                        if item.get("active"):
                            print(item)
    return data
