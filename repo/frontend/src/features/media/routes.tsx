import { Routes, Route } from "react-router-dom";
import { MediaLibraryPage } from "./pages/MediaLibraryPage";
import { MediaUploadPage } from "./pages/MediaUploadPage";
import { MediaDetailPage } from "./pages/MediaDetailPage";
import { RepostFlowPage } from "./pages/RepostFlowPage";

export default function MediaRoutes() {
  return (
    <Routes>
      <Route index element={<MediaLibraryPage />} />
      <Route path="upload" element={<MediaUploadPage />} />
      <Route path=":mediaId" element={<MediaDetailPage />} />
      <Route path=":mediaId/repost" element={<RepostFlowPage />} />
    </Routes>
  );
}
