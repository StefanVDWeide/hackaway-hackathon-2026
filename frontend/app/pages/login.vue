<script setup lang="ts">
import { toast } from 'vue-sonner'

definePageMeta({
  auth: { unauthenticatedOnly: true, navigateAuthenticatedTo: '/dashboard' },
  layout: 'default',
})

const { signIn } = useAuth()
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await signIn({ email: email.value, password: password.value }, { callbackUrl: '/dashboard' })
  }
  catch {
    error.value = 'Invalid email or password'
    toast.error('Sign in failed')
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-56px)] px-4">
    <Card class="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Sign in</CardTitle>
        <CardDescription>Enter your credentials to continue</CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-4" @submit.prevent="handleLogin">
          <div class="space-y-1.5">
            <Label for="email">Email</Label>
            <Input id="email" v-model="email" type="email" placeholder="you@example.com" required autocomplete="email" />
          </div>
          <div class="space-y-1.5">
            <Label for="password">Password</Label>
            <Input id="password" v-model="password" type="password" placeholder="••••••••" required autocomplete="current-password" />
          </div>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <Button type="submit" class="w-full" :disabled="loading">
            {{ loading ? 'Signing in...' : 'Sign in' }}
          </Button>
        </form>
      </CardContent>
      <CardFooter class="justify-center text-sm text-muted-foreground">
        No account?&nbsp;
        <NuxtLink to="/register" class="text-primary hover:underline">Register</NuxtLink>
      </CardFooter>
    </Card>
  </div>
</template>
