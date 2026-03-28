<script setup lang="ts">
import type { UserRead } from '~/types/api'

definePageMeta({ auth: true, layout: 'default' })

const { data } = useAuth()

const user = computed<UserRead | null>(() => data.value as UserRead | null)
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-lg">
    <h1 class="text-2xl font-bold mb-6">Profile</h1>

    <Card>
      <CardContent class="pt-6 space-y-4">
        <div class="flex items-center gap-4">
          <Avatar class="h-16 w-16">
            <AvatarFallback class="text-xl">
              {{ user?.display_name?.slice(0, 2).toUpperCase() }}
            </AvatarFallback>
          </Avatar>
          <div>
            <p class="text-xl font-semibold">{{ user?.display_name }}</p>
            <p class="text-sm text-muted-foreground">{{ user?.email }}</p>
          </div>
        </div>

        <Separator />

        <div class="space-y-3 text-sm">
          <div class="flex justify-between">
            <span class="text-muted-foreground">Account status</span>
            <Badge :variant="user?.is_active ? 'default' : 'destructive'">
              {{ user?.is_active ? 'Active' : 'Inactive' }}
            </Badge>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Verified</span>
            <Badge :variant="user?.is_verified ? 'default' : 'outline'">
              {{ user?.is_verified ? 'Verified' : 'Unverified' }}
            </Badge>
          </div>
          <div v-if="user?.latitude && user?.longitude" class="flex justify-between">
            <span class="text-muted-foreground">Location</span>
            <span>{{ user.latitude.toFixed(4) }}, {{ user.longitude.toFixed(4) }}</span>
          </div>
          <div v-else class="flex justify-between">
            <span class="text-muted-foreground">Location</span>
            <span class="text-muted-foreground italic">Not set</span>
          </div>
        </div>

        <Separator />

        <div class="flex gap-2">
          <Button class="flex-1" as-child>
            <NuxtLink to="/dashboard">Go to Dashboard</NuxtLink>
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
