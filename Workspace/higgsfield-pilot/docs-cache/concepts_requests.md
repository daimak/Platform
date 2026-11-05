> ## Documentation Index
> Fetch the complete documentation index at: https://docs.higgsfield.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Requests and lifecycle

> Understand asynchronous generation requests and their terminal states.

Generation is asynchronous. A successful submission creates a request and returns immediately while the work continues in the background.

## Request lifecycle

| Status | Terminal | Meaning |
| - | :-: | - |
| `queued` | No | The request is waiting to start and may still be canceled. |
| `in_progress` | No | Generation has started and can no longer be canceled. |
| `completed` | Yes | Output URLs are available in the response. |
| `failed` | Yes | Generation failed. The response may include an `error`. |
| `nsfw` | Yes | Input or output was rejected by content moderation. |
| `canceled` | Yes | The request was canceled before processing started. |

Store the `request_id` as soon as a request is accepted. It is the stable identifier used by polling, cancellation, webhook deduplication, and support.

> [!TIP]
>
> Send an [`Idempotency-Key`](https://docs.higgsfield.ai/docs/concepts/idempotency) with generation submissions so an ambiguous timeout can be retried without creating a duplicate request.

## Initial response

```json theme={"theme":{"light":"github-light","dark":"github-dark"}}
{
  "status": "queued",
  "request_id": "d7e6c0f3-6699-4f6c-bb45-2ad7fd9158ff",
  "status_url": "https://api.higgsfield.ai/requests/d7e6c0f3-6699-4f6c-bb45-2ad7fd9158ff/status",
  "cancel_url": "https://api.higgsfield.ai/requests/d7e6c0f3-6699-4f6c-bb45-2ad7fd9158ff/cancel",
  "expires_after": 604800
}
```

Use the URLs from the response instead of constructing them manually. `expires_after` is how long, in seconds, the request's data is kept after it finishes. See [Data retention and deletion](https://docs.higgsfield.ai/docs/enterprise/data-retention.md).

## Completed output

The output field depends on the model's output type.

```json Image theme={"theme":{"light":"github-light","dark":"github-dark"}}
{
  "status": "completed",
  "request_id": "d7e6c0f3-6699-4f6c-bb45-2ad7fd9158ff",
  "expires_at": "2026-10-31T12:05:12.481Z",
  "images": [
    { "url": "https://cdn.example.com/image-1.jpg" },
    { "url": "https://cdn.example.com/image-2.jpg" }
  ]
}
```

```json Video theme={"theme":{"light":"github-light","dark":"github-dark"}}
{
  "status": "completed",
  "request_id": "d7e6c0f3-6699-4f6c-bb45-2ad7fd9158ff",
  "video": {
    "url": "https://cdn.example.com/video.mp4"
  }
}
```

```json Audio theme={"theme":{"light":"github-light","dark":"github-dark"}}
{
  "status": "completed",
  "request_id": "d7e6c0f3-6699-4f6c-bb45-2ad7fd9158ff",
  "audio": {
    "url": "https://cdn.example.com/audio.mp3"
  },
  "audios": [
    { "url": "https://cdn.example.com/audio.mp3" }
  ]
}
```

Some video and 3D operations can return additional artifacts such as `zip`, `mov`, `jsx`, `fbx`, or `ply`.

Once a request finishes, its status response includes `expires_at`: the time after which its files are deleted and output URLs stop working.

## Cancel a request

Cancellation is available only while every job in the request remains queued.

```bash theme={"theme":{"light":"github-light","dark":"github-dark"}}
curl --request POST \
  --url "https://api.higgsfield.ai/requests/${REQUEST_ID}/cancel" \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}"
```

A successful cancellation returns `202 Accepted` with an empty body. If processing has started, the API returns `400 Bad Request`.

## Delete a request

Delete a finished request's files, prompt and parameters immediately:

```bash theme={"theme":{"light":"github-light","dark":"github-dark"}}
curl --request DELETE \
  --url "https://api.higgsfield.ai/requests/${REQUEST_ID}" \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}"
```

The API returns `200 OK` with `{"request_id": "...", "status": "deleted"}`, also when the request was already deleted. A request that is still `queued` or `in_progress` returns `409 Conflict`. Billing records are kept.

> [!NOTE]
>
> Request data is kept for seven days after the request finishes, or less if you [shorten the retention](https://docs.higgsfield.ai/docs/enterprise/data-retention.md). Copy completed media to your own storage if you need it for longer.


## Related topics

- [How the API works](https://docs.higgsfield.ai/docs/how-to/introduction.md)
- [Model API Reference](https://docs.higgsfield.ai/docs/models.md)
- [Quickstart](https://docs.higgsfield.ai/docs/quickstart.md)
- [FAQ](https://docs.higgsfield.ai/docs/help/faq.md)
- [Support](https://docs.higgsfield.ai/docs/help/support.md)


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.