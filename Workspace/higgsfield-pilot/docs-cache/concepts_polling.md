> ## Documentation Index
> Fetch the complete documentation index at: https://docs.higgsfield.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Polling

> Poll request status without creating unnecessary load or duplicate generations.

Poll the `status_url` returned by the submission response until the request reaches a terminal state.

## Recommended strategy

1. Start with a two-second interval.
2. Increase the interval gradually up to ten seconds.
3. Add random jitter when many workers poll concurrently.
4. Stop on `completed`, `failed`, `nsfw`, or `canceled`.
5. Set an application-level timeout appropriate for the selected model.

```python theme={"theme":{"light":"github-light","dark":"github-dark"}}
import random
import time

import httpx

terminal_statuses = {"completed", "failed", "nsfw", "canceled"}
delay = 2.0

while True:
    response = httpx.get(
        status_url,
        headers={"Authorization": f"Key {key_id}:{key_secret}"},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    if result["status"] in terminal_statuses:
        break

    time.sleep(delay + random.uniform(0, 0.5))
    delay = min(delay * 1.5, 10.0)
```

## Retry decisions

| Response | Recommended action |
| - | - |
| `200` with a non-terminal status | Continue polling with backoff. |
| `401` | Stop and fix the credentials. |
| `404` | Stop and verify the request ID and account. |
| `5xx` or network failure | Retry the status request with exponential backoff. |

For long-running production workloads, use [webhooks](https://docs.higgsfield.ai/docs/how-to/webhooks.md) and keep polling as a recovery path.


## Related topics

- [Client libraries](https://docs.higgsfield.ai/docs/how-to/sdk.md)
- [Ads Studio — Generate ads API](https://docs.higgsfield.ai/docs/models/ads-studio/generate.md)
- [Webhooks](https://docs.higgsfield.ai/docs/how-to/webhooks.md)
- [Recraft V4.1 Pro — Text to image API](https://docs.higgsfield.ai/docs/models/recraft-v4-1-pro/generate.md)
- [Recraft V4.1 Utility Pro — Text to image API](https://docs.higgsfield.ai/docs/models/recraft-v4-1-utility-pro/text-to-image.md)


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.