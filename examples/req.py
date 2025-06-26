
# github api example using scriptpy
import json
from typing import Callable



url = "https://api.github.com/repos/matan-h/Transfer/commits"
# raw_json = $(f"curl -q {url}")
raw_json = $(f"curl -s {url}")
# print($(f"echo {raw_json}"))

commits = json.loads(raw_json)


messages = commits | .get("commit") | .get("message")
filtered_messages:list = messages | .startswith("feat")
print(filtered_messages.count(True))
