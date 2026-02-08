import { WorkspaceScreen } from "@/app/features/workspace/WorkspaceScreen";
import { Suspense } from "react";

export default function Home() {
  return (
    <Suspense fallback={null}>
      <WorkspaceScreen />
    </Suspense>
  );
}
