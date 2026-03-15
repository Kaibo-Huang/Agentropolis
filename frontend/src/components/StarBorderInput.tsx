"use client";

import { type InputHTMLAttributes } from "react";

/**
 * Text input with star-border and arrow submit button.
 */
export default function StarBorderInput({
  className = "",
  onSubmit,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { onSubmit?: () => void }) {
  return (
    <span className={`star-border-input-wrap ${className}`}>
      <input
        type="text"
        className="star-border-input"
        onKeyDown={(e) => {
          if (e.key === "Enter" && onSubmit) {
            e.preventDefault();
            onSubmit();
          }
          props.onKeyDown?.(e);
        }}
        {...props}
      />
      <button
        type="button"
        className="star-border-submit"
        onClick={onSubmit}
        aria-label="Send"
        title="Send"
      >
        <span aria-hidden>→</span>
      </button>
    </span>
  );
}
