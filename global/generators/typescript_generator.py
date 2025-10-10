#!/usr/bin/env python3
"""
TypeScript Generator for Valheim World Engine
Generates Next.js frontend applications, React components, and TypeScript utilities
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class TypeScriptGenerator:
    """Generator for TypeScript/Next.js frontend applications and components"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.templates_dir = self.base_path / "templates" / "typescript"
        self.output_dir = self.base_path / "output" / "typescript"
        
    def create_nextjs_app(self, app_name: str, description: str = "", 
                         version: str = "1.0.0", author: str = "VWE") -> Dict[str, str]:
        """Generate a complete Next.js application structure"""
        
        # Create app directory structure
        app_dir = self.output_dir / app_name
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (app_dir / "src").mkdir(exist_ok=True)
        (app_dir / "src" / "app").mkdir(exist_ok=True)
        (app_dir / "src" / "components").mkdir(exist_ok=True)
        (app_dir / "src" / "lib").mkdir(exist_ok=True)
        (app_dir / "src" / "types").mkdir(exist_ok=True)
        (app_dir / "src" / "hooks").mkdir(exist_ok=True)
        (app_dir / "src" / "utils").mkdir(exist_ok=True)
        (app_dir / "public").mkdir(exist_ok=True)
        (app_dir / "styles").mkdir(exist_ok=True)
        (app_dir / "tests").mkdir(exist_ok=True)
        
        files_created = {}
        
        # 1. Package.json
        package_json = self._generate_package_json(app_name, description, version, author)
        package_file = app_dir / "package.json"
        package_file.write_text(json.dumps(package_json, indent=2))
        files_created["package_json"] = str(package_file)
        
        # 2. Next.js config
        next_config = self._generate_next_config()
        next_config_file = app_dir / "next.config.js"
        next_config_file.write_text(next_config)
        files_created["next_config"] = str(next_config_file)
        
        # 3. TypeScript config
        ts_config = self._generate_ts_config()
        ts_config_file = app_dir / "tsconfig.json"
        ts_config_file.write_text(json.dumps(ts_config, indent=2))
        files_created["ts_config"] = str(ts_config_file)
        
        # 4. Main layout
        layout_content = self._generate_layout(app_name)
        layout_file = app_dir / "src" / "app" / "layout.tsx"
        layout_file.write_text(layout_content)
        files_created["layout"] = str(layout_file)
        
        # 5. Home page
        page_content = self._generate_page(app_name)
        page_file = app_dir / "src" / "app" / "page.tsx"
        page_file.write_text(page_content)
        files_created["page"] = str(page_file)
        
        # 6. API route
        api_content = self._generate_api_route(app_name)
        api_file = app_dir / "src" / "app" / "api" / "health" / "route.ts"
        api_file.parent.mkdir(exist_ok=True)
        api_file.write_text(api_content)
        files_created["api_route"] = str(api_file)
        
        # 7. Main component
        component_content = self._generate_main_component(app_name)
        component_file = app_dir / "src" / "components" / f"{app_name}.tsx"
        component_file.write_text(component_content)
        files_created["main_component"] = str(component_file)
        
        # 8. Types
        types_content = self._generate_types(app_name)
        types_file = app_dir / "src" / "types" / f"{app_name.lower()}.ts"
        types_file.write_text(types_content)
        files_created["types"] = str(types_file)
        
        # 9. Custom hook
        hook_content = self._generate_custom_hook(app_name)
        hook_file = app_dir / "src" / "hooks" / f"use{app_name}.ts"
        hook_file.write_text(hook_content)
        files_created["custom_hook"] = str(hook_file)
        
        # 10. Utility functions
        utils_content = self._generate_utils(app_name)
        utils_file = app_dir / "src" / "utils" / f"{app_name.lower()}.ts"
        utils_file.write_text(utils_content)
        files_created["utils"] = str(utils_file)
        
        # 11. Global styles
        styles_content = self._generate_global_styles()
        styles_file = app_dir / "styles" / "globals.css"
        styles_file.write_text(styles_content)
        files_created["styles"] = str(styles_file)
        
        # 12. Environment config
        env_content = self._generate_env_config()
        env_file = app_dir / ".env.local"
        env_file.write_text(env_content)
        files_created["env_config"] = str(env_file)
        
        # 13. README
        readme_content = self._generate_readme(app_name, description, version, author)
        readme_file = app_dir / "README.md"
        readme_file.write_text(readme_content)
        files_created["readme"] = str(readme_file)
        
        # 14. Test file
        test_content = self._generate_tests(app_name)
        test_file = app_dir / "tests" / f"{app_name.lower()}.test.tsx"
        test_file.write_text(test_content)
        files_created["tests"] = str(test_file)
        
        # 15. Dockerfile
        dockerfile_content = self._generate_dockerfile(app_name)
        dockerfile_file = app_dir / "Dockerfile"
        dockerfile_file.write_text(dockerfile_content)
        files_created["dockerfile"] = str(dockerfile_file)
        
        return files_created
    
    def _generate_package_json(self, app_name: str, description: str, 
                              version: str, author: str) -> Dict[str, Any]:
        """Generate package.json file"""
        return {
            "name": app_name.lower().replace(" ", "-"),
            "version": version,
            "description": description or f"A Next.js application for Valheim World Engine",
            "author": author,
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
                "test": "jest",
                "test:watch": "jest --watch",
                "type-check": "tsc --noEmit"
            },
            "dependencies": {
                "next": "^14.0.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "@types/node": "^20.0.0",
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "typescript": "^5.0.0",
                "tailwindcss": "^3.3.0",
                "autoprefixer": "^10.4.0",
                "postcss": "^8.4.0",
                "@headlessui/react": "^1.7.0",
                "@heroicons/react": "^2.0.0",
                "clsx": "^2.0.0",
                "framer-motion": "^10.16.0",
                "axios": "^1.6.0",
                "swr": "^2.2.0",
                "zustand": "^4.4.0",
                "react-hook-form": "^7.47.0",
                "@hookform/resolvers": "^3.3.0",
                "zod": "^3.22.0",
                "date-fns": "^2.30.0",
                "lodash": "^4.17.0",
                "@types/lodash": "^4.14.0"
            },
            "devDependencies": {
                "eslint": "^8.0.0",
                "eslint-config-next": "^14.0.0",
                "@typescript-eslint/eslint-plugin": "^6.0.0",
                "@typescript-eslint/parser": "^6.0.0",
                "prettier": "^3.0.0",
                "prettier-plugin-tailwindcss": "^0.5.0",
                "jest": "^29.0.0",
                "@testing-library/react": "^13.4.0",
                "@testing-library/jest-dom": "^6.0.0",
                "jest-environment-jsdom": "^29.0.0"
            }
        }
    
    def _generate_next_config(self) -> str:
        """Generate Next.js configuration"""
        return '''/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['localhost'],
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
'''
    
    def _generate_ts_config(self) -> Dict[str, Any]:
        """Generate TypeScript configuration"""
        return {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "es6"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [
                    {
                        "name": "next"
                    }
                ],
                "baseUrl": ".",
                "paths": {
                    "@/*": ["./src/*"],
                    "@/components/*": ["./src/components/*"],
                    "@/lib/*": ["./src/lib/*"],
                    "@/types/*": ["./src/types/*"],
                    "@/hooks/*": ["./src/hooks/*"],
                    "@/utils/*": ["./src/utils/*"]
                }
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"]
        }
    
    def _generate_layout(self, app_name: str) -> str:
        """Generate root layout component"""
        return f'''import type {{ Metadata }} from 'next';
import {{ Inter }} from 'next/font/google';
import './globals.css';

const inter = Inter({{ subsets: ['latin'] }});

export const metadata: Metadata = {{
  title: '{app_name}',
  description: 'A Next.js application for Valheim World Engine',
}};

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  return (
    <html lang="en">
      <body className={{inter.className}}>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white shadow">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <h1 className="text-xl font-semibold text-gray-900">
                    {app_name}
                  </h1>
                </div>
                <nav className="flex items-center space-x-4">
                  <a
                    href="/"
                    className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Home
                  </a>
                  <a
                    href="/about"
                    className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    About
                  </a>
                </nav>
              </div>
            </div>
          </header>
          <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            {{children}}
          </main>
        </div>
      </body>
    </html>
  );
}}
'''
    
    def _generate_page(self, app_name: str) -> str:
        """Generate home page component"""
        return f'''import {app_name} from '@/components/{app_name}';

export default function Home() {{
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome to {app_name}
        </h1>
        <p className="text-lg text-gray-600 mb-6">
          A Next.js application generated by Valheim World Engine TypeScript generator.
        </p>
        <{app_name} />
      </div>
    </div>
  );
}}
'''
    
    def _generate_api_route(self, app_name: str) -> str:
        """Generate API route"""
        return f'''import {{ NextRequest, NextResponse }} from 'next/server';

export async function GET(request: NextRequest) {{
  try {{
    return NextResponse.json({{
      status: 'healthy',
      service: '{app_name}',
      timestamp: new Date().toISOString(),
    }});
  }} catch (error) {{
    return NextResponse.json(
      {{ error: 'Internal server error' }},
      {{ status: 500 }}
    );
  }}
}}

export async function POST(request: NextRequest) {{
  try {{
    const body = await request.json();
    
    return NextResponse.json({{
      message: 'Request processed successfully',
      data: body,
      timestamp: new Date().toISOString(),
    }});
  }} catch (error) {{
    return NextResponse.json(
      {{ error: 'Invalid request body' }},
      {{ status: 400 }}
    );
  }}
}}
'''
    
    def _generate_main_component(self, app_name: str) -> str:
        """Generate main component"""
        return f''''use client';

import {{ useState, useEffect }} from 'react';
import {{ use{app_name} }} from '@/hooks/use{app_name}';
import {{ {app_name}Data }} from '@/types/{app_name.lower()}';

interface {app_name}Props {{
  initialData?: {app_name}Data;
}}

export default function {app_name}({{ initialData }}: {app_name}Props) {{
  const {{ data, loading, error, refetch }} = use{app_name}();
  const [count, setCount] = useState(0);

  useEffect(() => {{
    if (initialData) {{
      console.log('Initial data received:', initialData);
    }}
  }}, [initialData]);

  const handleIncrement = () => {{
    setCount(prev => prev + 1);
  }};

  const handleDecrement = () => {{
    setCount(prev => Math.max(0, prev - 1));
  }};

  if (loading) {{
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading...</span>
      </div>
    );
  }}

  if (error) {{
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Error loading data
            </h3>
            <div className="mt-2 text-sm text-red-700">
              {{error}}
            </div>
            <div className="mt-4">
              <button
                onClick={{refetch}}
                className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-2 rounded-md text-sm font-medium"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }}

  return (
    <div className="space-y-6">
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            {app_name} Component
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            <p>
              This is a sample component generated by the VWE TypeScript generator.
              It demonstrates state management, API integration, and error handling.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Counter Example
          </h3>
          <div className="mt-4 flex items-center space-x-4">
            <button
              onClick={{handleDecrement}}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              -
            </button>
            <span className="text-2xl font-bold text-gray-900">{{count}}</span>
            <button
              onClick={{handleIncrement}}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              +
            </button>
          </div>
        </div>
      </div>

      {{data && (
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              API Data
            </h3>
            <div className="mt-2">
              <pre className="bg-gray-100 p-4 rounded-md text-sm overflow-x-auto">
                {{JSON.stringify(data, null, 2)}}
              </pre>
            </div>
          </div>
        </div>
      )}}
    </div>
  );
}}
'''
    
    def _generate_types(self, app_name: str) -> str:
        """Generate TypeScript types"""
        return f'''export interface {app_name}Data {{
  id: string;
  name: string;
  description?: string;
  status: {app_name}Status;
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}}

export enum {app_name}Status {{
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}}

export interface {app_name}Request {{
  name: string;
  description?: string;
  metadata?: Record<string, any>;
}}

export interface {app_name}Response {{
  data: {app_name}Data;
  message: string;
  success: boolean;
}}

export interface {app_name}ListResponse {{
  data: {app_name}Data[];
  total: number;
  page: number;
  limit: number;
}}

export interface ApiError {{
  error: string;
  message: string;
  code?: string;
  details?: Record<string, any>;
}}

export interface HealthCheck {{
  status: 'healthy' | 'unhealthy';
  service: string;
  timestamp: string;
  version?: string;
}}

export interface PaginationParams {{
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}}

export interface SearchParams {{
  query?: string;
  filters?: Record<string, any>;
  pagination?: PaginationParams;
}}
'''
    
    def _generate_custom_hook(self, app_name: str) -> str:
        """Generate custom React hook"""
        return f'''import {{ useState, useEffect, useCallback }} from 'react';
import {{ {app_name}Data, {app_name}Request, ApiError }} from '@/types/{app_name.lower()}';
import {{ {app_name.lower()}Api }} from '@/utils/{app_name.lower()}';

interface Use{app_name}Return {{
  data: {app_name}Data | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  create: (request: {app_name}Request) => Promise<{app_name}Data | null>;
  update: (id: string, request: Partial<{app_name}Request>) => Promise<{app_name}Data | null>;
  remove: (id: string) => Promise<boolean>;
}}

export function use{app_name}(initialData?: {app_name}Data): Use{app_name}Return {{
  const [data, setData] = useState<{app_name}Data | null>(initialData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {{
    setLoading(true);
    setError(null);
    
    try {{
      const result = await {app_name.lower()}Api.getHealth();
      setData(result as any); // Type assertion for demo
    }} catch (err) {{
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      console.error('Error fetching {app_name.lower()} data:', err);
    }} finally {{
      setLoading(false);
    }}
  }}, []);

  const create = useCallback(async (request: {app_name}Request): Promise<{app_name}Data | null> => {{
    setLoading(true);
    setError(null);
    
    try {{
      const result = await {app_name.lower()}Api.create(request);
      setData(result);
      return result;
    }} catch (err) {{
      const errorMessage = err instanceof Error ? err.message : 'Failed to create {app_name.lower()}';
      setError(errorMessage);
      console.error('Error creating {app_name.lower()}:', err);
      return null;
    }} finally {{
      setLoading(false);
    }}
  }}, []);

  const update = useCallback(async (id: string, request: Partial<{app_name}Request>): Promise<{app_name}Data | null> => {{
    setLoading(true);
    setError(null);
    
    try {{
      const result = await {app_name.lower()}Api.update(id, request);
      setData(result);
      return result;
    }} catch (err) {{
      const errorMessage = err instanceof Error ? err.message : 'Failed to update {app_name.lower()}';
      setError(errorMessage);
      console.error('Error updating {app_name.lower()}:', err);
      return null;
    }} finally {{
      setLoading(false);
    }}
  }}, []);

  const remove = useCallback(async (id: string): Promise<boolean> => {{
    setLoading(true);
    setError(null);
    
    try {{
      await {app_name.lower()}Api.delete(id);
      setData(null);
      return true;
    }} catch (err) {{
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete {app_name.lower()}';
      setError(errorMessage);
      console.error('Error deleting {app_name.lower()}:', err);
      return false;
    }} finally {{
      setLoading(false);
    }}
  }}, []);

  const refetch = useCallback(async () => {{
    await fetchData();
  }}, [fetchData]);

  useEffect(() => {{
    if (!initialData) {{
      fetchData();
    }}
  }}, [fetchData, initialData]);

  return {{
    data,
    loading,
    error,
    refetch,
    create,
    update,
    remove,
  }};
}}
'''
    
    def _generate_utils(self, app_name: str) -> str:
        """Generate utility functions"""
        return f'''import axios, {{ AxiosResponse }} from 'axios';
import {{ {app_name}Data, {app_name}Request, {app_name}Response, ApiError }} from '@/types/{app_name.lower()}';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({{
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {{
    'Content-Type': 'application/json',
  }},
}});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {{
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {{
      config.headers.Authorization = `Bearer ${{token}}`;
    }}
    return config;
  }},
  (error) => {{
    return Promise.reject(error);
  }}
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {{
    return response;
  }},
  (error) => {{
    if (error.response?.status === 401) {{
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }}
    return Promise.reject(error);
  }}
);

export class {app_name}Api {{
  static async getHealth(): Promise<{app_name}Data> {{
    try {{
      const response = await apiClient.get('/api/health');
      return response.data;
    }} catch (error) {{
      throw new Error('Failed to fetch health status');
    }}
  }}

  static async create(request: {app_name}Request): Promise<{app_name}Data> {{
    try {{
      const response = await apiClient.post<{app_name}Response>('/api/{app_name.lower()}/', request);
      return response.data.data;
    }} catch (error) {{
      if (axios.isAxiosError(error) && error.response) {{
        const apiError: ApiError = error.response.data;
        throw new Error(apiError.message || 'Failed to create {app_name.lower()}');
      }}
      throw new Error('Failed to create {app_name.lower()}');
    }}
  }}

  static async getById(id: string): Promise<{app_name}Data> {{
    try {{
      const response = await apiClient.get<{app_name}Response>(`/api/{app_name.lower()}/${{id}}`);
      return response.data.data;
    }} catch (error) {{
      if (axios.isAxiosError(error) && error.response) {{
        const apiError: ApiError = error.response.data;
        throw new Error(apiError.message || 'Failed to fetch {app_name.lower()}');
      }}
      throw new Error('Failed to fetch {app_name.lower()}');
    }}
  }}

  static async update(id: string, request: Partial<{app_name}Request>): Promise<{app_name}Data> {{
    try {{
      const response = await apiClient.put<{app_name}Response>(`/api/{app_name.lower()}/${{id}}`, request);
      return response.data.data;
    }} catch (error) {{
      if (axios.isAxiosError(error) && error.response) {{
        const apiError: ApiError = error.response.data;
        throw new Error(apiError.message || 'Failed to update {app_name.lower()}');
      }}
      throw new Error('Failed to update {app_name.lower()}');
    }}
  }}

  static async delete(id: string): Promise<void> {{
    try {{
      await apiClient.delete(`/api/{app_name.lower()}/${{id}}`);
    }} catch (error) {{
      if (axios.isAxiosError(error) && error.response) {{
        const apiError: ApiError = error.response.data;
        throw new Error(apiError.message || 'Failed to delete {app_name.lower()}');
      }}
      throw new Error('Failed to delete {app_name.lower()}');
    }}
  }}

  static async list(params?: {{ page?: number; limit?: number }}): Promise<{app_name}Data[]> {{
    try {{
      const response = await apiClient.get<{app_name}Data[]>('/api/{app_name.lower()}/', {{
        params,
      }});
      return response.data;
    }} catch (error) {{
      if (axios.isAxiosError(error) && error.response) {{
        const apiError: ApiError = error.response.data;
        throw new Error(apiError.message || 'Failed to list {app_name.lower()}s');
      }}
      throw new Error('Failed to list {app_name.lower()}s');
    }}
  }}
}}

// Utility functions
export function formatDate(date: string | Date): string {{
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {{
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }});
}}

export function formatStatus(status: string): string {{
  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
}}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {{
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {{
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  }};
}}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {{
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {{
    if (!inThrottle) {{
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }}
  }};
}}
'''
    
    def _generate_global_styles(self) -> str:
        """Generate global CSS styles"""
        return '''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    font-family: system-ui, sans-serif;
  }
  
  body {
    @apply text-gray-900 bg-gray-50;
  }
}

@layer components {
  .btn {
    @apply inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2;
  }
  
  .btn-primary {
    @apply btn text-white bg-blue-600 hover:bg-blue-700 focus:ring-blue-500;
  }
  
  .btn-secondary {
    @apply btn text-gray-700 bg-white hover:bg-gray-50 focus:ring-blue-500 border-gray-300;
  }
  
  .btn-danger {
    @apply btn text-white bg-red-600 hover:bg-red-700 focus:ring-red-500;
  }
  
  .card {
    @apply bg-white overflow-hidden shadow rounded-lg;
  }
  
  .card-header {
    @apply px-4 py-5 sm:px-6 border-b border-gray-200;
  }
  
  .card-body {
    @apply px-4 py-5 sm:p-6;
  }
  
  .form-input {
    @apply block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm;
  }
  
  .form-label {
    @apply block text-sm font-medium text-gray-700 mb-1;
  }
  
  .form-error {
    @apply mt-1 text-sm text-red-600;
  }
}

@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
  
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
}

/* Custom animations */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

/* Loading spinner */
.spinner {
  @apply animate-spin rounded-full border-2 border-gray-300 border-t-blue-600;
}

/* Focus styles */
.focus-ring {
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
}
'''
    
    def _generate_env_config(self) -> str:
        """Generate environment configuration"""
        return '''# Next.js Environment Variables
# Copy this file to .env.local and update the values

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=VWE Frontend
NEXT_PUBLIC_APP_VERSION=1.0.0

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_DEBUG=true

# External Services
NEXT_PUBLIC_MAP_TILE_URL=https://tile.openstreetmap.org/{z}/{x}/{y}.png
NEXT_PUBLIC_MAP_ATTRIBUTION=© OpenStreetMap contributors

# Development
NODE_ENV=development
'''
    
    def _generate_readme(self, app_name: str, description: str, 
                        version: str, author: str) -> str:
        """Generate README for the application"""
        return f'''# {app_name}

{description or f"A Next.js application for Valheim World Engine"}

## Version
{version}

## Author
{author}

## Description
This application was generated using the Valheim World Engine TypeScript generator.

## Features
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- React Hook Form for form handling
- SWR for data fetching
- Zustand for state management
- Framer Motion for animations
- Jest and Testing Library for testing
- ESLint and Prettier for code quality

## Getting Started

### Prerequisites
- Node.js 18.0 or later
- npm or yarn package manager

### Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
```

2. Set up environment variables:
```bash
cp .env.local.example .env.local
# Edit .env.local with your configuration
```

3. Run the development server:
```bash
npm run dev
# or
yarn dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run test` - Run tests
- `npm run test:watch` - Run tests in watch mode
- `npm run type-check` - Run TypeScript type checking

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   └── {app_name}.tsx    # Main component
├── hooks/                 # Custom React hooks
│   └── use{app_name}.ts  # Main hook
├── lib/                   # Library code
├── types/                 # TypeScript type definitions
│   └── {app_name.lower()}.ts
├── utils/                 # Utility functions
│   └── {app_name.lower()}.ts
└── styles/               # Global styles
    └── globals.css
```

## API Integration

The application includes a complete API client with:
- Axios for HTTP requests
- Request/response interceptors
- Error handling
- TypeScript types for all API responses

## State Management

The application uses:
- React hooks for local state
- SWR for server state
- Zustand for global state (if needed)

## Styling

The application uses Tailwind CSS with:
- Custom component classes
- Responsive design utilities
- Dark mode support (ready to implement)
- Custom animations

## Testing

The application includes:
- Jest for unit testing
- React Testing Library for component testing
- Mock API responses
- Test utilities

## Deployment

### Using Docker
```bash
docker build -t {app_name.lower()} .
docker run -p 3000:3000 {app_name.lower()}
```

### Using Vercel
1. Push to GitHub
2. Connect to Vercel
3. Deploy automatically

### Using other platforms
```bash
npm run build
npm run start
```

## Configuration

The application can be configured using environment variables:
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_APP_NAME` - Application name
- `NEXT_PUBLIC_APP_VERSION` - Application version

## License
Generated by Valheim World Engine - See project license for details.
'''
    
    def _generate_tests(self, app_name: str) -> str:
        """Generate test file"""
        return f'''import {{ render, screen, fireEvent, waitFor }} from '@testing-library/react';
import {{ jest }} from '@jest/globals';
import {app_name} from '@/components/{app_name}';

// Mock the custom hook
jest.mock('@/hooks/use{app_name}', () => ({{
  use{app_name}: jest.fn(),
}}));

const mockUse{app_name} = require('@/hooks/use{app_name}').use{app_name};

describe('{app_name} Component', () => {{
  const mockData = {{
    id: '1',
    name: 'Test {app_name}',
    description: 'Test description',
    status: 'completed',
    createdAt: '2023-01-01T00:00:00Z',
    updatedAt: '2023-01-01T00:00:00Z',
  }};

  beforeEach(() => {{
    jest.clearAllMocks();
  }});

  it('renders loading state', () => {{
    mockUse{app_name}.mockReturnValue({{
      data: null,
      loading: true,
      error: null,
      refetch: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    }});

    render(<{app_name} />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  }});

  it('renders error state', () => {{
    const mockRefetch = jest.fn();
    mockUse{app_name}.mockReturnValue({{
      data: null,
      loading: false,
      error: 'Test error',
      refetch: mockRefetch,
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    }});

    render(<{app_name} />);
    
    expect(screen.getByText('Error loading data')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
    
    const retryButton = screen.getByText('Try again');
    fireEvent.click(retryButton);
    expect(mockRefetch).toHaveBeenCalled();
  }});

  it('renders component with data', () => {{
    mockUse{app_name}.mockReturnValue({{
      data: mockData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    }});

    render(<{app_name} />);
    
    expect(screen.getByText('{app_name} Component')).toBeInTheDocument();
    expect(screen.getByText('Counter Example')).toBeInTheDocument();
    expect(screen.getByText('API Data')).toBeInTheDocument();
  }});

  it('handles counter increment', () => {{
    mockUse{app_name}.mockReturnValue({{
      data: mockData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    }});

    render(<{app_name} />);
    
    const incrementButton = screen.getByText('+');
    const countDisplay = screen.getByText('0');
    
    fireEvent.click(incrementButton);
    expect(countDisplay).toHaveTextContent('1');
    
    fireEvent.click(incrementButton);
    expect(countDisplay).toHaveTextContent('2');
  }});

  it('handles counter decrement', () => {{
    mockUse{app_name}.mockReturnValue({{
      data: mockData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    }});

    render(<{app_name} />);
    
    const incrementButton = screen.getByText('+');
    const decrementButton = screen.getByText('-');
    const countDisplay = screen.getByText('0');
    
    // Increment first
    fireEvent.click(incrementButton);
    expect(countDisplay).toHaveTextContent('1');
    
    // Then decrement
    fireEvent.click(decrementButton);
    expect(countDisplay).toHaveTextContent('0');
    
    // Decrement should not go below 0
    fireEvent.click(decrementButton);
    expect(countDisplay).toHaveTextContent('0');
  }});

  it('displays API data when available', () => {{
    mockUse{app_name}.mockReturnValue({{
      data: mockData,
      loading: false,
      error: null,
      refetch: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      remove: jest.fn(),
    }});

    render(<{app_name} />);
    
    expect(screen.getByText('API Data')).toBeInTheDocument();
    expect(screen.getByText(JSON.stringify(mockData, null, 2))).toBeInTheDocument();
  }});
}});
'''
    
    def _generate_dockerfile(self, app_name: str) -> str:
        """Generate Dockerfile"""
        return f'''FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js collects completely anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line in case you want to disable telemetry during the build.
# ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
# Uncomment the following line in case you want to disable telemetry during runtime.
# ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# server.js is created by next build from the standalone output
# https://nextjs.org/docs/pages/api-reference/next-config-js/output
CMD ["node", "server.js"]
'''
    
    def create_map_viewer(self, app_name: str = "MapViewer") -> Dict[str, str]:
        """Generate a specialized map viewer application"""
        return self.create_nextjs_app(
            app_name=app_name,
            description="Interactive map viewer for Valheim worlds",
            version="1.0.0",
            author="VWE"
        )
    
    def create_dashboard(self, app_name: str = "Dashboard") -> Dict[str, str]:
        """Generate a specialized dashboard application"""
        return self.create_nextjs_app(
            app_name=app_name,
            description="Administrative dashboard for VWE",
            version="1.0.0",
            author="VWE"
        )


def main():
    """Example usage of the TypeScript generator"""
    generator = TypeScriptGenerator()
    
    # Generate a basic Next.js app
    print("Generating basic Next.js application...")
    files = generator.create_nextjs_app(
        app_name="VWE_ExampleApp",
        description="Example application generated by VWE TypeScript generator",
        version="1.0.0",
        author="VWE"
    )
    
    print("Generated files:")
    for file_type, file_path in files.items():
        print(f"  {file_type}: {file_path}")
    
    # Generate specialized applications
    print("\\nGenerating map viewer application...")
    generator.create_map_viewer()
    
    print("\\nGenerating dashboard application...")
    generator.create_dashboard()
    
    print("\\nTypeScript generator example complete!")


if __name__ == "__main__":
    main()
