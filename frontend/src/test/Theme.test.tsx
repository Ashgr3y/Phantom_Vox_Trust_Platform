import { fireEvent, render, screen } from "@testing-library/react";
import { useTheme } from "../hooks/useTheme";

function Harness() {
  const { theme, toggle } = useTheme();
  return <button onClick={toggle}>Theme: {theme}</button>;
}

describe("theme preference", () => {
  it("switches and persists the selected theme", () => {
    localStorage.clear();
    render(<Harness />);
    fireEvent.click(screen.getByRole("button"));
    expect(localStorage.getItem("phantom-vox-theme")).toBe("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
