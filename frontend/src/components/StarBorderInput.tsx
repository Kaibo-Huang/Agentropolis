"use client";

import { type InputHTMLAttributes } from "react";

/**
 * Text input with an animated star-border (rotating conic gradient).
 * Inspired by https://reactbits.dev/animations/star-border
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
    </span>
  );
}
