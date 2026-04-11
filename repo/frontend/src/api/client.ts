import axios from "axios";
import { LS_KEYS } from "@/lib/constants";

function getWorkstationId(): string {
  let id = localStorage.getItem(LS_KEYS.WORKSTATION_ID);
  if (!id) {
    // Generate a UUID without external dependency
    id = crypto.randomUUID?.() ?? generateUUID();
    localStorage.setItem(LS_KEYS.WORKSTATION_ID, id);
  }
  return id;
}

function generateUUID(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

const apiClient = axios.create({
  baseURL: "/api/v1/",
  withCredentials: true,
  xsrfCookieName: "medrights_csrf",
  xsrfHeaderName: "X-CSRFToken",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add workstation ID
apiClient.interceptors.request.use((config) => {
  config.headers["X-Workstation-ID"] = getWorkstationId();
  return config;
});

// Response interceptor to handle 401 session expiry
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      axios.isAxiosError(error) &&
      error.response?.status === 401 &&
      (error.response?.data?.error === "session_expired" || error.response?.data?.code === "session_expired")
    ) {
      // Dispatch a custom event that the AuthContext can listen for
      window.dispatchEvent(new CustomEvent("auth:session-expired"));
    }
    return Promise.reject(error);
  }
);

export default apiClient;
