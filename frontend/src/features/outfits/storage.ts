export function getOutfitSuggestionStorageKey(
  userId: string,
  outfitId: string,
) {
  return `climo:outfit-suggestion:${userId}:${outfitId}`;
}
