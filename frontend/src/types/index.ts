// ── Auth ──────────────────────────────────────────────────────
export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  has_face_encoding: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ── Courses ───────────────────────────────────────────────────
export interface Course {
  id: string;
  title: string;
  description: string;
  subject: string;
  difficulty: number;
  is_active: boolean;
  created_at: string;
  total_lessons: number;
  completed_lessons: number;
  progress_pct: number;
}

export interface Lesson {
  id: string;
  course_id: string;
  title: string;
  content: string;
  order_index: number;
  lesson_type: string;
  completed: boolean;
}

// ── Assessment ────────────────────────────────────────────────
export interface Question {
  id: string;
  question_text: string;
  options: string[];
  topic_tag: string;
  difficulty: string;
}

export interface QuizData {
  course_id: string;
  difficulty_level: string;
  questions: Question[];
  total_questions: number;
  time_limit_mins: number;
}

export interface QuestionResult {
  question_id: string;
  question_text: string;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  explanation: string | null;
}

export interface QuizResult {
  id: string;
  course_id: string;
  score: number;
  total_questions: number;
  correct_count: number;
  difficulty_level: string;
  taken_at: string;
  question_results: QuestionResult[];
  next_difficulty: string;
  performance_message: string;
}

// ── Analytics ─────────────────────────────────────────────────
export interface TopicStat {
  topic_tag: string;
  display_name: string;
  accuracy_pct: number;
  sessions_count: number;
  difficulty_level: string;
  last_score: number;
  trend: string;
}

export interface TrendPoint {
  week_label: string;
  accuracy: number;
  sessions: number;
}

export interface AnalyticsDashboard {
  overall_accuracy: number;
  total_sessions: number;
  total_lessons_done: number;
  current_streak: number;
  strongest_topics: TopicStat[];
  weakest_topics: TopicStat[];
  all_topics: TopicStat[];
  weekly_trend: TrendPoint[];
  topics_mastered: number;
  topics_needs_work: number;
}

export interface Recommendation {
  recommendation_text: string;
  focus_topics: string[];
  suggested_difficulty: string;
  generated_at: string;
}

// ── Chat ──────────────────────────────────────────────────────
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}