> ## Documentation Index
> Fetch the complete documentation index at: https://docs.higgsfield.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# File uploads

> Upload images, video, or audio for use as model input.

Use a presigned upload URL when your input media is not already available through a public HTTPS URL.

## 1. Create an upload URL

```bash theme={"theme":{"light":"github-light","dark":"github-dark"}}
UPLOAD=$(curl --silent --show-error --fail-with-body \
  --request POST \
  --url https://api.higgsfield.ai/files/generate-upload-url \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
  --header "Content-Type: application/json" \
  --data '{"content_type":"image/jpeg"}')

echo "$UPLOAD" | jq
```

```json theme={"theme":{"light":"github-light","dark":"github-dark"}}
{
  "public_url": "https://cdn.example.com/input/example.jpeg",
  "upload_url": "https://storage.example.com/presigned-upload-url",
  "content_type": "image/jpeg",
  "upload_headers": {
    "Content-Type": "image/jpeg",
    "x-amz-tagging": "retention=temporary"
  }
}
```

The upload URL expires after one hour.

## 2. Upload the file

Send the file to `upload_url` with every header returned in `upload_headers`.

```bash theme={"theme":{"light":"github-light","dark":"github-dark"}}
curl --request PUT \
  --url "$(echo "$UPLOAD" | jq --raw-output '.upload_url')" \
  --header "Content-Type: $(echo "$UPLOAD" | jq --raw-output '.upload_headers["Content-Type"]')" \
  --header "x-amz-tagging: $(echo "$UPLOAD" | jq --raw-output '.upload_headers["x-amz-tagging"]')" \
  --upload-file ./input.jpg
```

Do not send Higgsfield API credentials to the presigned storage URL.

## 3. Use the public URL

Pass `public_url` in the model parameter that accepts an input URL, such as `image_url`, `video_url`, or `audio_url`.

## Supported content types

* `image/jpeg`, `image/jpg`, `image/png`, `image/webp`, `image/gif`
* `audio/wav`, `audio/x-wav`
* `video/mp4`

The content type used for the upload must match the value used to create the presigned URL.


## Related topics

- [Client libraries](https://docs.higgsfield.ai/docs/how-to/sdk.md)
- [Data retention and deletion](https://docs.higgsfield.ai/docs/enterprise/data-retention.md)
- [Higgsfield API](https://docs.higgsfield.ai/docs/index.md)
- [Idempotent requests](https://docs.higgsfield.ai/docs/concepts/idempotency.md)
- [FAQ](https://docs.higgsfield.ai/docs/help/faq.md)


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.