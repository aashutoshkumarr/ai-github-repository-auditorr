import { cn } from "../src/lib/utils";

describe("shadcn utility and component baseline", () => {
  it("should merge tailwind classes properly", () => {
    const result = cn("px-2 py-1", "bg-red-500", "px-4");
    expect(result).toContain("px-4");
    expect(result).not.toContain("px-2");
  });

  it("should handle conditional class evaluation", () => {
    const isActive = true;
    const result = cn("base-class", isActive && "active-class");
    expect(result).toContain("active-class");
  });
});
