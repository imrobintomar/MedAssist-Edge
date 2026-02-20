import React, { useState } from "react";
import { Copy, Check } from "lucide-react";

interface Props {
  text: string;
  label?: string;
}

export const CopyButton: React.FC<Props> = ({ text, label = "Copy" }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const el = document.createElement("textarea");
      el.value = text;
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg border transition-all duration-200 ${
        copied
          ? "bg-safe-50 border-safe-300 text-safe-700"
          : "bg-slate-50 border-slate-200 text-slate-500 hover:bg-clinical-50 hover:border-clinical-200 hover:text-clinical-600"
      }`}
    >
      {copied ? <Check size={11} /> : <Copy size={11} />}
      {copied ? "Copied!" : label}
    </button>
  );
};
