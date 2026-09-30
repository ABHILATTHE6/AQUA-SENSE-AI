# Ingestion Layer

The ingestion layer separates provider-specific retrieval from AQUA-SENSE's canonical data contract.

## Flow

`Provider → SourceAdapter → RawRecord → raw partition → normalization → validation → processed layer`

## Rules

1. Preserve raw provider payloads.
2. Attach retrieval provenance.
3. Never silently overwrite source data.
4. Normalize only after raw capture.
5. Validate canonical observations before analytical use.
6. Keep adapters independently testable.
