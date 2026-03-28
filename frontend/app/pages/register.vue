<script setup lang="ts">
import { toast } from 'vue-sonner'

definePageMeta({
  auth: { unauthenticatedOnly: true, navigateAuthenticatedTo: '/dashboard' },
  layout: 'default',
})

const { signUp, signIn } = useAuth()
const email = ref('')
const password = ref('')
const displayName = ref('')
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    await signUp({
      email: email.value,
      password: password.value,
      display_name: displayName.value,
    })
    // Auto sign-in after successful registration
    await signIn({ email: email.value, password: password.value }, { callbackUrl: '/dashboard' })
    toast.success('Account created!')
  }
  catch (e: unknown) {
    const detail = (e as { data?: { detail?: string } })?.data?.detail
    error.value = detail === 'Email already registered' ? 'That email is already in use' : 'Registration failed'
    toast.error(error.value)
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
        <CardTitle>Create account</CardTitle>
        <CardDescription>Join the marketplace</CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-4" @submit.prevent="handleRegister">
          <div class="space-y-1.5">
            <Label for="name">Display name</Label>
            <Input id="name" v-model="displayName" placeholder="Your name" required autocomplete="name" />
          </div>
          <div class="space-y-1.5">
            <Label for="email">Email</Label>
            <Input id="email" v-model="email" type="email" placeholder="you@example.com" required autocomplete="email" />
          </div>
          <div class="space-y-1.5">
            <Label for="password">Password</Label>
            <Input id="password" v-model="password" type="password" placeholder="••••••••" required autocomplete="new-password" />
          </div>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <Button type="submit" class="w-full" :disabled="loading">
            {{ loading ? 'Creating account...' : 'Create account' }}
          </Button>
        </form>
      </CardContent>
      <CardFooter class="justify-center text-sm text-muted-foreground">
        Already have an account?&nbsp;
        <NuxtLink to="/login" class="text-primary hover:underline">Sign in</NuxtLink>
      </CardFooter>
    </Card>
  </div>
</template>
