const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

if (!configuredApiUrl) {

  throw new Error(

    "NEXT_PUBLIC_API_URL is not defined in the environment variables",

  );

}

const API_URL = configuredApiUrl.replace(/\/+$/, "");

async function fetchApi(
  url: string,
  options?: RequestInit,
): Promise<Response> {
  try {
    return await fetch(url, options);
  } catch (reason) {
    const detail = reason instanceof Error ? ` (${reason.message})` : "";
    throw new Error(
      `Unable to connect to the backend at ${API_URL}${detail}. Verify the backend deployment and NEXT_PUBLIC_API_URL.`,
    );
  }
}

export type Category = {

  id: number;

  name: string;

  slug: string;

  description: string;

  created_at: string;

};

export type User = {

  id: number;

  username: string;

  email: string;

  display_name: string;

  bio: string;

  is_active: boolean;

  is_admin: boolean;

};

export type Thread = {

  id: number;

  title: string;

  slug: string;

  content: string;

  category_id: number;

  views: number;

  created_at: string;

  updated_at: string;

};

export type Reply = {

  id: number;

  content: string;

  thread_id: number;

  created_at: string;

};

async function request<T>(

  endpoint: string,

  options?: RequestInit,

): Promise<T> {

  const response = await fetchApi(`${API_URL}${endpoint}`, {

    ...options,

    headers: {

      "Content-Type": "application/json",

      ...(options?.headers ?? {}),

    },

    cache: "no-store",

  });

  if (!response.ok) {

    const error = await response.text();

    throw new Error(error || "API request failed");

  }

  return response.json();

}

const apiFetch = request;

function getAuthHeaders(): HeadersInit {

  if (typeof window === "undefined") {

    return {};

  }

  const token = localStorage.getItem("apexive_token");

  if (!token) {

    return {};

  }

  return {

    Authorization: `Bearer ${token}`,

  };

}

export function getCategories() {

  return request<Category[]>("/api/categories");

}

export function getThreads() {

  return request<Thread[]>("/api/threads");

}

export function getThread(threadId: number) {

  return request<Thread>(`/api/threads/${threadId}`);

}

export function getReplies(threadId: number) {

  return request<Reply[]>(`/api/replies/thread/${threadId}`);

}

export function createCategory(data: {

  name: string;

  slug: string;

  description: string;

}) {

  return request<Category>("/api/categories", {

    method: "POST",

    body: JSON.stringify(data),

    headers: {

      ...getAuthHeaders(),

    },

  });

}

export function createThread(data: {

  title: string;

  slug: string;

  content: string;

  category_id: number;

}) {

  return request<Thread>("/api/threads", {

    method: "POST",

    body: JSON.stringify(data),

    headers: {

      ...getAuthHeaders(),

    },

  });

}

export function createReply(data: {

  content: string;

  thread_id: number;

}) {

  return request<Reply>("/api/replies", {

    method: "POST",

    body: JSON.stringify(data),

    headers: {

      ...getAuthHeaders(),

    },

  });

}

export type Article = {

  id: number;

  title: string;

  slug: string;

  excerpt: string;

  content: string;

  category: string;

  author_id: number;

  cover_image_url: string | null;

  read_time_minutes: number;

  views: number;

  is_published: boolean;

  is_featured: boolean;

  created_at: string;

  updated_at: string;

};

export type Project = {

  id: number;

  name: string;

  slug: string;

  description: string;

  content: string;

  category: string;

  creator_id: number;

  repository_url: string | null;

  website_url: string | null;

  logo_url: string | null;

  status: string;

  stars: number;

  views: number;

  is_featured: boolean;

  created_at: string;

  updated_at: string;

};

export type Resource = {

  id: number;

  title: string;

  slug: string;

  description: string;

  content: string;

  resource_type: string;

  category: string;

  author_id: number;

  file_url: string | null;

  file_size: string | null;

  downloads: number;

  is_featured: boolean;

  is_published: boolean;

  created_at: string;

  updated_at: string;

};

export async function getArticles(): Promise<Article[]> {

  const response = await fetchApi(`${API_URL}/api/articles`, {

    cache: "no-store",

  });

  if (!response.ok) {

    throw new Error("Failed to load articles");

  }

  return response.json();

}

export async function getArticle(slug: string): Promise<Article> {
  const response = await fetchApi(

    `${API_URL}/api/articles/${encodeURIComponent(slug)}`,

    {

      cache: "no-store",

    },

  );

  if (!response.ok) {

    throw new Error("Article not found");

  }

  return response.json();

}

export async function getFeaturedArticles(): Promise<Article[]> {

  const response = await fetchApi(`${API_URL}/api/articles/featured`, {

    cache: "no-store",

  });

  if (!response.ok) {

    throw new Error("Failed to load featured articles");

  }

  return response.json();

}

export async function getProjects(): Promise<Project[]> {

  const response = await fetchApi(`${API_URL}/api/projects`, {

    cache: "no-store",

  });

  if (!response.ok) {

    throw new Error("Failed to load projects");

  }

  return response.json();

}

export async function getProject(slug: string): Promise<Project> {

  const response = await fetchApi(

    `${API_URL}/api/projects/${encodeURIComponent(slug)}`,

    {

      cache: "no-store",

    },

  );

  if (!response.ok) {

    throw new Error("Project not found");

  }

  return response.json();

}

export async function getFeaturedProjects(): Promise<Project[]> {

  const response = await fetchApi(`${API_URL}/api/projects/featured`, {

    cache: "no-store",

  });

  if (!response.ok) {

    throw new Error("Failed to load featured projects");

  }

  return response.json();

}

export async function getResources(): Promise<Resource[]> {

  const response = await fetchApi(`${API_URL}/api/resources`, {

    cache: "no-store",

  });

  if (!response.ok) {

    throw new Error("Failed to load resources");

  }

  return response.json();

}

export async function getResource(slug: string): Promise<Resource> {

  const response = await fetchApi(

    `${API_URL}/api/resources/${encodeURIComponent(slug)}`,

    {

      cache: "no-store",

    },

  );

  if (!response.ok) {

    throw new Error("Resource not found");

  }

  return response.json();

}

export async function getFeaturedResources(): Promise<Resource[]> {

  const response = await fetchApi(`${API_URL}/api/resources/featured`, {

    cache: "no-store",

  });

  if (!response.ok) {

    throw new Error("Failed to load featured resources");

  }

  return response.json();

}

export async function createArticle(payload: {

  title: string;

  slug: string;

  excerpt: string;

  content: string;

  category: string;

  cover_image_url?: string | null;

  read_time_minutes: number;

  is_published: boolean;

  is_featured: boolean;

}) {

  return apiFetch<Article>("/api/articles", {

    method: "POST",

    body: JSON.stringify(payload),

    headers: {

      ...getAuthHeaders(),

    },

  });

}

export async function createProject(payload: {

  name: string;

  slug: string;

  description: string;

  content: string;

  category: string;

  repository_url?: string | null;

  website_url?: string | null;

  logo_url?: string | null;

  status: string;

  is_featured: boolean;

}) {

  return apiFetch<Project>("/api/projects", {

    method: "POST",

    body: JSON.stringify(payload),

    headers: {

      ...getAuthHeaders(),

    },

  });

}

export async function createResource(payload: {

  title: string;

  slug: string;

  description: string;

  content: string;

  resource_type: string;

  category: string;

  file_url?: string | null;

  file_size?: string | null;

  is_featured: boolean;

  is_published: boolean;

}) {

  return apiFetch<Resource>("/api/resources", {

    method: "POST",

    body: JSON.stringify(payload),

    headers: {

      ...getAuthHeaders(),

    },

  });

}

export default API_URL;