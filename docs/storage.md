# FacturaGuard Storage

FacturaGuard supports a storage abstraction for uploaded CSV/XML/ZIP files.

## Local storage

Default for development:

```txt
FILE_STORAGE_BACKEND=local
FILE_STORAGE_PATH=./storage
```

Docker Compose maps this to a named volume.

## S3-compatible storage

Use this for production with AWS S3, MinIO, Cloudflare R2, DigitalOcean Spaces, etc.

```txt
FILE_STORAGE_BACKEND=s3
S3_ENDPOINT_URL=
S3_REGION_NAME=eu-central-1
S3_BUCKET_NAME=facturaguard-documents
S3_ACCESS_KEY_ID=<key>
S3_SECRET_ACCESS_KEY=<secret>
```

For AWS S3, `S3_ENDPOINT_URL` can be empty.

For MinIO/R2/Spaces, set the endpoint URL provided by the vendor.

## Stored object path

Local:

```txt
/path/to/storage/organizations/<organization_id>/<uuid>.xml
```

S3:

```txt
s3://<bucket>/organizations/<organization_id>/<uuid>.xml
```

## Security notes

- Never expose storage paths directly to the browser.
- Always download through authenticated backend endpoints.
- Use private buckets.
- Add lifecycle rules for retention if needed.
- Add malware scanning before production use.
