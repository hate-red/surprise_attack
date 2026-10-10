import { AppShell } from "@/widgets/app-shell/ui/app-shell";
import { SpecificationWorkspace } from "@/widgets/specification-workspace/ui/specification-workspace";

export default function Page() {
  return (
    <AppShell>
      <SpecificationWorkspace />
    </AppShell>
  );
}
