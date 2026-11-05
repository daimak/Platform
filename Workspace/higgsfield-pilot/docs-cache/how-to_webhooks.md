> ## Documentation Index
> Fetch the complete documentation index at: https://docs.higgsfield.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Webhooks

> Receive terminal generation results without continuous polling.

Pass an HTTPS endpoint in the `hf_webhook` query parameter when submitting generation. Higgsfield sends one or more HTTP `POST` deliveries after the request reaches `completed`, `failed`, or `nsfw`.

## Configure a webhook

```bash theme={"theme":{"light":"github-light","dark":"github-dark"}}
curl --request POST \
  --url "https://api.higgsfield.ai/higgsfield-ai/soul/v2/standard?hf_webhook=https%3A%2F%2Fexample.com%2Fwebhooks%2Fhiggsfield" \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
  --header "Content-Type: application/json" \
  --data '{
    "prompt": "Editorial portrait in soft daylight"
  }'
```

Your endpoint must be publicly reachable over HTTPS, accept a JSON request body, and respond within ten seconds.

## Payload envelope

All deliveries use the same top-level envelope. Successful output is nested in `payload`.

```json Completed image theme={"theme":{"light":"github-light","dark":"github-dark"}}
{
  "request_id": "9417a243-e457-4075-895b-b68f3cda5303",
  "status": "completed",
  "error": null,
  "expires_at": "2026-10-31T12:05:12.481Z",
  "payload": {
    "images": [
      {
        "url": "https://cdn.example.com/generated-image.jpg",
        "content_type": "image/jpeg"
      }
    ]
  }
}
```

```json Completed video theme={"theme":{"light":"github-light","dark":"github-dark"}}
{
  "request_id": "9417a243-e457-4075-895b-b68f3cda5303",
  "status": "completed",
  "error": null,
  "payload": {
    "video": {
      "url": "https://cdn.example.com/generated-video.mp4",
      "content_type": "video/mp4"
    }
  }
}
```

```json Failed theme={"theme":{"light":"github-light","dark":"github-dark"}}
{
  "request_id": "9417a243-e457-4075-895b-b68f3cda5303",
  "status": "failed",
  "error": "Generation failed",
  "payload": null
}
```

```json NSFW theme={"theme":{"light":"github-light","dark":"github-dark"}}
{
  "request_id": "9417a243-e457-4075-895b-b68f3cda5303",
  "status": "nsfw",
  "error": null,
  "payload": null
}
```

Audio responses contain `payload.audio`. Some video and 3D operations can also include `zip`, `mov`, `jsx`, `fbx`, or `ply` artifacts.

`expires_at` is the time after which the request's files are deleted and the URLs in `payload` stop working; download them before then. See [Data retention and deletion](https://docs.higgsfield.ai/docs/enterprise/data-retention.md).

## Verify signatures

Webhook deliveries are signed using the [Standard Webhooks](https://www.standardwebhooks.com/) specification. Verify every delivery before trusting its contents: anyone who knows your endpoint URL can send it a request.

Each signed delivery includes three headers:

| Header | Value |
| - | - |
| `webhook-id` | Unique event identifier. It stays the same across retries of the same event. |
| `webhook-timestamp` | Unix time in seconds when the delivery was signed. |
| `webhook-signature` | One or more space-separated signatures in the form `v1,<base64>`. |

### Get your signing secret

Open **Settings** in [Higgsfield Console](https://console.higgsfield.ai) and reveal the webhook signing secret. It starts with `whsec_`. The secret is created the first time it is revealed; until then, deliveries for your account are not signed.

One secret covers every API key and request of the account. In an organization, only admins can reveal or rotate it. Store it with your other server-side credentials and never expose it in browser or mobile code.

### Verify with a library

Use an official Standard Webhooks library. It checks the signature and rejects timestamps outside a five-minute tolerance. Verify the raw request body before parsing JSON: re-serialized JSON does not match the signature.

```python Python theme={"theme":{"light":"github-light","dark":"github-dark"}}
import os

from standardwebhooks import Webhook, WebhookVerificationError

webhook = Webhook(os.environ["HF_WEBHOOK_SECRET"])

try:
    event = webhook.verify(raw_body, headers)
except WebhookVerificationError:
    return Response(status=400)
```

```ts TypeScript theme={"theme":{"light":"github-light","dark":"github-dark"}}
import { Webhook } from "standardwebhooks";

const webhook = new Webhook(process.env.HF_WEBHOOK_SECRET!);

let event;
try {
  event = webhook.verify(rawBody, req.headers);
} catch {
  return res.status(400).send();
}
```

Install the library with `pip install standardwebhooks` or `npm install standardwebhooks`. Libraries for other languages are listed in the [Standard Webhooks repository](https://github.com/standard-webhooks/standard-webhooks).

### Verify manually

1. Remove the `whsec_` prefix from the secret and base64-decode the rest to get the HMAC key.
2. Build the signed content `{webhook-id}.{webhook-timestamp}.{raw body}`.
3. Compute HMAC-SHA256 of the signed content with the key and base64-encode the result.
4. Compare it with each `v1,` entry of `webhook-signature` using a constant-time comparison. Accept the delivery if any entry matches.
5. Reject deliveries whose `webhook-timestamp` is more than five minutes from your current time.

### Rotate the secret

Rotate the secret in **Settings** if it may have been exposed. The new secret takes effect immediately, and the previous secret keeps working for 24 hours. During that window `webhook-signature` carries one signature per secret, so update your server before the previous secret expires. At most two secrets are valid at the same time.

> [!NOTE]
>
> Integrations that pass a secret with the webhook in the request body still receive it in the `X-Webhook-Secret-Key` header. That header will be retired; switch to signature verification.

## Delivery and retries

* Return any `2xx` response after durably recording the event.
* Network failures and `5xx` responses are retried for up to two hours.
* `4xx` responses are treated as permanent and are not retried.
* Duplicate deliveries are possible. Deduplicate by `webhook-id`, or by `request_id` and terminal `status` for unsigned deliveries.
* If delivery fails permanently, retrieve the result through the authenticated status endpoint.
* No deliveries are made after a request's data is [deleted](https://docs.higgsfield.ai/docs/enterprise/data-retention.md). With retention shorter than the retry window, keep polling as a fallback.

Reject request bodies that do not match the documented envelope, but acknowledge valid duplicate deliveries with `2xx`.


## Related topics

- [Webhook security](https://docs.higgsfield.ai/docs/enterprise/webhook-security.md)
- [Headers](https://docs.higgsfield.ai/docs/api-reference/headers.md)
- [Data retention and deletion](https://docs.higgsfield.ai/docs/enterprise/data-retention.md)
- [How the API works](https://docs.higgsfield.ai/docs/how-to/introduction.md)
- [Organizations and roles](https://docs.higgsfield.ai/docs/enterprise/organizations.md)


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.