import { Suspense } from "react";
import { RequireAuth } from "@/components/auth/RequireAuth";

import { OutfitLoadingContent } from "./outfit-loading-content";

export default function OutfitLoadingPage() {
  return (
    <RequireAuth>
      <Suspense fallback={null}>
        <OutfitLoadingContent />
      </Suspense>
    </RequireAuth>
  );
}
