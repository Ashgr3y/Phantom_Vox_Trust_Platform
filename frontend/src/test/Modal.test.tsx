import { fireEvent, render, screen } from "@testing-library/react";
import { Modal } from "../components/Modal";

describe("Modal", () => {
  it("closes with Escape and exposes dialog semantics", () => {
    const close = vi.fn();
    render(<Modal open title="Secure verification" onClose={close}><button>Approve</button></Modal>);
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
    fireEvent.keyDown(document, { key: "Escape" });
    expect(close).toHaveBeenCalledTimes(1);
  });
});
