/**
 * Axios client — single place for all API calls.
 * Automatically attaches JWT token to every request.
 * Handles 401 → clears auth and redirects to login.
 */
import axios from "axios";

const BASE_URL = "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// ── Request interceptor — attach token ────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor — handle 401 ────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────
export const authApi = {
  register: (form: FormData) =>
    api.post("/auth/register", form, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  faceLogin: (imageBlob: Blob) => {
    const form = new FormData();
    form.append("image", imageBlob, "face.jpg");
    return api.post("/auth/face-login", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  me: () => api.get("/auth/me"),
  logout: () => api.post("/auth/logout"),
};

// ── Courses ───────────────────────────────────────────────────
export const coursesApi = {
  list: () => api.get("/courses"),
  get: (id: string) => api.get(`/courses/${id}`),
  lessons: (courseId: string) => api.get(`/courses/${courseId}/lessons`),
  completeLesson: (courseId: string, lessonId: string) =>
    api.post(`/courses/${courseId}/lessons/${lessonId}/complete`),
};

// ── Assessments ───────────────────────────────────────────────
export const assessmentsApi = {
  getQuiz: (courseId: string, count = 10) =>
    api.get(`/assessments/quiz/${courseId}?count=${count}`),
  getMockTest: (courseId: string) =>
    api.get(`/assessments/mock-test/${courseId}`),
  submitQuiz: (data: {
    course_id: string;
    answers: { question_id: string; selected_answer: string }[];
    time_taken_seconds: number;
  }) => api.post("/assessments/quiz/submit", data),
  history: () => api.get("/assessments/history"),
};

// ── AI ────────────────────────────────────────────────────────
export const aiApi = {
  // Returns a Response stream — handled separately in AIChatPanel
  chatStream: async (message: string, history: { role: string; content: string }[]) => {
    const token = localStorage.getItem("access_token");
    return fetch(`${BASE_URL}/ai/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message, history }),
    });
  },
  transcribe: (audioBlob: Blob) => {
    const form = new FormData();
    form.append("audio", audioBlob, "audio.webm");
    return api.post("/ai/transcribe", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  recommend: () => api.get("/ai/recommend"),
};

// ── Analytics ─────────────────────────────────────────────────
export const analyticsApi = {
  dashboard: () => api.get("/analytics/me"),
  trend: () => api.get("/analytics/me/trend"),
  recommendations: () => api.get("/analytics/me/recommendations"),
};