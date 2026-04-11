import { Routes, Route } from "react-router-dom";
import { PatientSearchPage } from "./pages/PatientSearchPage";
import { PatientCreatePage } from "./pages/PatientCreatePage";
import { PatientDetailPage } from "./pages/PatientDetailPage";
import { PatientEditPage } from "./pages/PatientEditPage";

export default function PatientRoutes() {
  return (
    <Routes>
      <Route index element={<PatientSearchPage />} />
      <Route path="new" element={<PatientCreatePage />} />
      <Route path=":patientId" element={<PatientDetailPage />} />
      <Route path=":patientId/update" element={<PatientEditPage />} />
    </Routes>
  );
}
