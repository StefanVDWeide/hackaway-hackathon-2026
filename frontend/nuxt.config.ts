// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },

  modules: [
    "@nuxt/eslint",
    "@nuxtjs/tailwindcss",
    "shadcn-nuxt",
    "@sidebase/nuxt-auth",
  ],

  runtimeConfig: {
    // Server-only: backend URL used by Nitro proxy + nuxt-auth
    // Override with NUXT_API_BASE_URL env var
    apiBaseUrl: "http://localhost:8000",
  },

  nitro: {
    routeRules: {
      "/api/**": {
        proxy: `${process.env.NUXT_API_BASE_URL ?? "http://localhost:8000"}/**`,
      },
    },
  },

  auth: {
    globalAppMiddleware: false,
    provider: {
      type: "local",
      endpoints: {
        signIn: { path: "/users/login", method: "post" },
        signUp: { path: "/users/register", method: "post" },
        getSession: { path: "/users/me", method: "get" },
        signOut: false,
      },
      token: {
        signInResponseTokenPointer: "/access_token",
        type: "Bearer",
        cookieName: "auth.token",
        headerName: "Authorization",
        maxAgeInSeconds: 3600,
        sameSiteAttribute: "lax",
      },
      session: {
        dataType: {
          id: "string",
          email: "string",
          display_name: "string",
          latitude: "number | null",
          longitude: "number | null",
          is_active: "boolean",
          is_verified: "boolean",
        },
      },
      pages: {
        login: "/login",
      },
    },
  },

  shadcn: {
    prefix: "",
    componentDir: "@/components/ui",
  },
});
