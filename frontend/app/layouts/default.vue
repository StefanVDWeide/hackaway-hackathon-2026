<script setup lang="ts">
const router = useRouter()
const { status, data, signOut } = useAuth()

const isAuthenticated = computed(() => status.value === 'authenticated')

const searchQuery = ref('')

function handleSearch() {
  if (searchQuery.value.trim()) {
    router.push({ path: '/search', query: { query: searchQuery.value.trim() } })
  }
}

async function handleSignOut() {
  await signOut({ callbackUrl: '/' })
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-background">
    <!-- Navbar -->
    <header class="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div class="container mx-auto flex h-14 items-center gap-4 px-4">
        <!-- Logo -->
        <NuxtLink to="/" class="flex items-center gap-2 font-bold text-lg shrink-0">
          <span class="text-primary">Hackaway</span>
          <span class="text-muted-foreground font-normal hidden sm:inline">Market</span>
        </NuxtLink>

        <!-- Search bar -->
        <form class="flex-1 max-w-xl" @submit.prevent="handleSearch">
          <div class="relative">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
            </svg>
            <Input
              v-model="searchQuery"
              placeholder="Search listings..."
              class="pl-9 h-9"
            />
          </div>
        </form>

        <!-- Nav links -->
        <nav class="hidden md:flex items-center gap-1 text-sm">
          <Button variant="ghost" size="sm" as-child>
            <NuxtLink to="/">Browse</NuxtLink>
          </Button>
        </nav>

        <!-- Auth buttons -->
        <div class="flex items-center gap-2 ml-auto shrink-0">
          <template v-if="!isAuthenticated">
            <Button variant="ghost" size="sm" as-child>
              <NuxtLink to="/login">Sign in</NuxtLink>
            </Button>
            <Button size="sm" as-child>
              <NuxtLink to="/register">Register</NuxtLink>
            </Button>
          </template>

          <template v-else>
            <Button variant="ghost" size="sm" as-child>
              <NuxtLink to="/dashboard/listings/new">+ Sell</NuxtLink>
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="ghost" size="sm" class="gap-2">
                  <Avatar class="h-7 w-7">
                    <AvatarFallback class="text-xs">
                      {{ data?.display_name?.slice(0, 2).toUpperCase() ?? 'ME' }}
                    </AvatarFallback>
                  </Avatar>
                  <span class="hidden md:inline">{{ data?.display_name }}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" class="w-48">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem as-child>
                  <NuxtLink to="/dashboard">Dashboard</NuxtLink>
                </DropdownMenuItem>
                <DropdownMenuItem as-child>
                  <NuxtLink to="/dashboard/listings">My Listings</NuxtLink>
                </DropdownMenuItem>
                <DropdownMenuItem as-child>
                  <NuxtLink to="/dashboard/negotiations">Negotiations</NuxtLink>
                </DropdownMenuItem>
                <DropdownMenuItem as-child>
                  <NuxtLink to="/dashboard/wallet">Wallet</NuxtLink>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem as-child>
                  <NuxtLink to="/profile">Profile</NuxtLink>
                </DropdownMenuItem>
                <DropdownMenuItem class="text-destructive" @click="handleSignOut">
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </template>
        </div>
      </div>
    </header>

    <!-- Main content -->
    <main class="flex-1">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="border-t py-6 text-center text-sm text-muted-foreground">
      Hackaway Market &copy; 2026
    </footer>

    <Sonner />
  </div>
</template>
