import { render, screen } from "@testing-library/react";
import { RiskBadge } from "../components/RiskBadge";

describe("RiskBadge", () => {
  it("renders an explicit critical label instead of relying on color", () => {
    render(<RiskBadge state="CRITICAL" />);
    expect(screen.getByText("Critical")).toBeInTheDocument();
  });

  it("renders the insufficient-audio abstention state", () => {
    render(<RiskBadge state="INSUFFICIENT_AUDIO" />);
    expect(screen.getByText("Insufficient audio")).toBeInTheDocument();
  });
});
