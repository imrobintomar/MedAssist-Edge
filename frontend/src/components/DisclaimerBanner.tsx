import React from "react";
import { ShieldAlert } from "lucide-react";

export const DisclaimerBanner: React.FC = () => (
  <div className="w-full rounded-xl px-4 py-3 flex items-start gap-3"
    style={{ background: "linear-gradient(135deg, #fffbeb, #fef3c7)", border: "1px solid #fbbf24" }}>
    <ShieldAlert className="shrink-0 mt-0.5" size={17} style={{ color: "#b45309" }} />
    <p className="text-sm leading-snug" style={{ color: "#92400e" }}>
      <span className="font-semibold">Clinical Decision Support Only.</span>{" "}
      All AI-generated output must be reviewed by a qualified clinician before any clinical
      action is taken. This system does not diagnose, prescribe, or issue medical orders.
      The clinician retains full clinical responsibility.
    </p>
  </div>
);
