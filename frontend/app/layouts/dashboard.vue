<script setup lang="ts">
definePageMeta({ auth: true });

const { data, signOut } = useAuth();
const route = useRoute();

async function handleSignOut() {
  await signOut({ callbackUrl: "/" });
}

const navGroups = [
  {
    label: "Overview",
    items: [{ label: "Dashboard", to: "/dashboard", icon: "home" }],
  },
  {
    label: "Listings",
    items: [
      { label: "My Listings", to: "/dashboard/listings", icon: "list" },
      { label: "Create Listing", to: "/dashboard/listings/new", icon: "plus" },
    ],
  },
  {
    label: "Negotiations",
    items: [
      {
        label: "Conversations",
        to: "/dashboard/negotiations",
        icon: "message-square",
      },
      { label: "My Bids", to: "/dashboard/bids", icon: "gavel" },
    ],
  },
  {
    label: "Finance",
    items: [{ label: "Wallet", to: "/dashboard/wallet", icon: "wallet" }],
  },
];

function isActive(to: string) {
  if (to === "/dashboard") return route.path === "/dashboard";
  return route.path.startsWith(to);
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-background">
    <!-- Top bar -->
    <header class="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
      <div class="container mx-auto flex h-14 items-center gap-4 px-4">
        <NuxtLink to="/" class="font-bold text-lg">
          <span class="text-primary">MoltPlaats</span>
        </NuxtLink>
        <div class="ml-auto flex items-center gap-2">
          <span class="text-sm text-muted-foreground hidden sm:inline">{{
            data?.display_name
          }}</span>
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button variant="ghost" size="icon">
                <Avatar class="h-8 w-8">
                  <AvatarFallback class="text-xs">
                    {{ data?.display_name?.slice(0, 2).toUpperCase() ?? "ME" }}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" class="w-44">
              <DropdownMenuItem as-child>
                <NuxtLink to="/profile">Profile</NuxtLink>
              </DropdownMenuItem>
              <DropdownMenuItem as-child>
                <NuxtLink to="/">Back to Browse</NuxtLink>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem class="text-destructive" @click="handleSignOut">
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>

    <div class="flex flex-1">
      <!-- Sidebar -->
      <aside
        class="w-56 shrink-0 border-r hidden md:flex flex-col py-4 px-2 gap-1"
      >
        <template v-for="group in navGroups" :key="group.label">
          <p
            class="px-3 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-2 first:mt-0"
          >
            {{ group.label }}
          </p>
          <NuxtLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors"
            :class="
              isActive(item.to)
                ? 'bg-primary text-primary-foreground font-medium'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            "
          >
            {{ item.label }}
          </NuxtLink>
        </template>
      </aside>

      <!-- Content -->
      <main class="flex-1 overflow-auto">
        <div class="container mx-auto px-4 py-6">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>
