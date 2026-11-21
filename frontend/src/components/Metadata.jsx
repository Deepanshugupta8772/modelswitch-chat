import React from "react";

const MetadataValue = ({ label, testId, value }) => (
  <span className="metadata-item">
    <span className="metadata-label">{label}</span>
    <span data-testid={testId}>{value}</span>
  </span>
);

export default function Metadata({ metadata }) {
  const sourceClass =
    metadata.resolution_source === "LLM_CACHE" ? "cache" : "live";

  return (
    <div className="metadata-row" aria-label="Reply metadata">
      <span
        className={`source-badge source-badge--${sourceClass}`}
        data-testid="meta-source"
      >
        {metadata.resolution_source}
      </span>
      <MetadataValue
        label="Model"
        testId="meta-model"
        value={metadata.model}
      />
      <MetadataValue
        label="Time"
        testId="meta-latency"
        value={`${metadata.latency_ms} ms`}
      />
      <MetadataValue
        label="In"
        testId="meta-input-tokens"
        value={metadata.input_tokens}
      />
      <MetadataValue
        label="Out"
        testId="meta-output-tokens"
        value={metadata.output_tokens}
      />
    </div>
  );
}
