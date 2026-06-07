import { Suspense } from "react";

import { OutfitLoadingContent } from "./outfit-loading-content";

export default function OutfitLoadingPage() {
  return (
    <Suspense fallback={null}>
      <OutfitLoadingContent />
    </Suspense>
  );
}