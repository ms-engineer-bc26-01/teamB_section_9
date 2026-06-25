export type ClothingItem = {
  id: string;
  user_id: string;
  name: string;
  category: string;
  color: string | null;
  pattern: string | null;
  size: string | null;
  season: string[];
  tpo_tags: string[];
  image_url: string | null;
  thumbnail_url: string | null;
  memo: string | null;
  is_favorite: boolean;
  wear_count: number;
  last_worn_at: string | null;
  attributes: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ClothesListResponse = {
  items: ClothingItem[];
  total: number;
};

export type ClothingCreateRequest = {
  name: string;
  category: string;
  color?: string | null;
  pattern?: string | null;
  size?: string | null;
  season?: string[];
  tpo_tags?: string[];
  image_url?: string | null;
  thumbnail_url?: string | null;
  memo?: string | null;
  is_favorite?: boolean;
};

export type ClothingUploadUrlRequest = {
  filename: string;
  content_type: "image/jpeg" | "image/png" | "image/webp";
};

export type ClothingUploadUrlResponse = {
  upload_url: string;
  storage_path: string;
  image_url: string;
};
