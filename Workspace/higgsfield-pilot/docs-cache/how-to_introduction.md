> ## Documentation Index
> Fetch the complete documentation index at: https://docs.higgsfield.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# How the API works

> Learn the common authentication and asynchronous request lifecycle shared by Higgsfield image and video models.

The Higgsfield API uses an asynchronous request lifecycle:

1. Submit JSON parameters to a model endpoint.
2. Store the returned `request_id`.
3. Poll `status_url` or wait for a webhook.
4. Download output when the request becomes `completed`.

> [card] [Start with the Quickstart](https://docs.higgsfield.ai/docs/quickstart.md)
>
> Run a complete request using cURL.

> [card] [Understand requests](https://docs.higgsfield.ai/docs/concepts/requests.md)
>
> Learn statuses, output shapes, cancellation, and retention.

**Base URL:** `https://api.higgsfield.ai`

Every request requires server-side [authentication](https://docs.higgsfield.ai/docs/authentication.md). For production integrations, read the [polling](https://docs.higgsfield.ai/docs/concepts/polling.md), [webhook](https://docs.higgsfield.ai/docs/how-to/webhooks.md), and [error handling](https://docs.higgsfield.ai/docs/concepts/errors.md) guides.


## Related topics

- [FAQ](https://docs.higgsfield.ai/docs/help/faq.md)
- [Webhook security](https://docs.higgsfield.ai/docs/enterprise/webhook-security.md)
- [Model API Reference](https://docs.higgsfield.ai/docs/models.md)
- [Capacity and concurrency](https://docs.higgsfield.ai/docs/enterprise/capacity.md)
- [Enterprise API](https://docs.higgsfield.ai/docs/enterprise/overview.md)


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.