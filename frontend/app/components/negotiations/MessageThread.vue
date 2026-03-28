<script setup lang="ts">
import type { MessageRead } from '~/types/api'
import { toast } from 'vue-sonner'

const props = defineProps<{
  conversationId: string
  messages: MessageRead[]
  currentUserId?: string
  sellerId?: string
}>()

const emit = defineEmits<{
  messageSent: [msg: MessageRead]
  bidAction: []
}>()

const { apiFetch } = useApi()
const newMessage = ref('')
const sending = ref(false)
const threadEl = ref<HTMLElement>()

function formatTime(d: string) {
  return new Date(d).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('nl-NL', { dateStyle: 'medium' })
}

function isMine(msg: MessageRead) {
  return msg.sender_id === props.currentUserId
}

async function sendMessage() {
  if (!newMessage.value.trim()) return
  sending.value = true
  try {
    const msg = await apiFetch<MessageRead>(`/api/negotiations/conversations/${props.conversationId}/messages`, {
      method: 'POST',
      body: { body: newMessage.value.trim() },
    })
    newMessage.value = ''
    emit('messageSent', msg)
    await nextTick()
    threadEl.value?.scrollTo({ top: threadEl.value.scrollHeight, behavior: 'smooth' })
  }
  catch {
    toast.error('Failed to send message')
  }
  finally { sending.value = false }
}

// Group messages by date
const grouped = computed(() => {
  const groups: { date: string; messages: MessageRead[] }[] = []
  let currentDate = ''
  for (const msg of props.messages) {
    const d = formatDate(msg.created_at)
    if (d !== currentDate) {
      currentDate = d
      groups.push({ date: d, messages: [] })
    }
    groups[groups.length - 1].messages.push(msg)
  }
  return groups
})

onMounted(() => {
  nextTick(() => {
    if (threadEl.value) threadEl.value.scrollTop = threadEl.value.scrollHeight
  })
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Message list -->
    <div ref="threadEl" class="flex-1 overflow-y-auto space-y-4 p-4 min-h-0">
      <div v-for="group in grouped" :key="group.date">
        <!-- Date separator -->
        <div class="flex items-center gap-3 my-4">
          <Separator class="flex-1" />
          <span class="text-xs text-muted-foreground shrink-0">{{ group.date }}</span>
          <Separator class="flex-1" />
        </div>

        <!-- Messages -->
        <div v-for="msg in group.messages" :key="msg.id" class="flex flex-col gap-1">
          <!-- Bid card inline -->
          <div v-if="msg.bid" class="max-w-sm" :class="isMine(msg) ? 'ml-auto' : ''">
            <p class="text-xs text-muted-foreground mb-1" :class="isMine(msg) ? 'text-right' : ''">
              {{ isMine(msg) ? 'You' : 'Other party' }} · {{ formatTime(msg.created_at) }}
            </p>
            <BidCard
              :bid="msg.bid"
              :current-user-id="currentUserId"
              :seller-id="sellerId"
              show-actions
              @accepted="emit('bidAction')"
              @rejected="emit('bidAction')"
              @countered="emit('bidAction')"
            />
          </div>

          <!-- Regular message -->
          <div
            v-else
            class="flex flex-col max-w-[75%]"
            :class="isMine(msg) ? 'ml-auto items-end' : 'items-start'"
          >
            <div
              class="rounded-2xl px-4 py-2 text-sm"
              :class="isMine(msg)
                ? 'bg-primary text-primary-foreground rounded-br-sm'
                : msg.actor_type === 'agent'
                  ? 'bg-muted border border-dashed text-muted-foreground italic rounded-bl-sm'
                  : 'bg-accent rounded-bl-sm'"
            >
              <span v-if="msg.actor_type === 'agent'" class="text-xs font-semibold block mb-0.5">Agent</span>
              {{ msg.body }}
            </div>
            <span class="text-xs text-muted-foreground mt-0.5">{{ formatTime(msg.created_at) }}</span>
          </div>
        </div>
      </div>

      <div v-if="messages.length === 0" class="text-center text-muted-foreground text-sm py-8">
        No messages yet. Start the conversation!
      </div>
    </div>

    <!-- Composer -->
    <div class="border-t p-4">
      <form class="flex gap-2" @submit.prevent="sendMessage">
        <Input
          v-model="newMessage"
          placeholder="Type a message..."
          :disabled="sending"
          class="flex-1"
        />
        <Button type="submit" :disabled="sending || !newMessage.trim()">
          {{ sending ? '...' : 'Send' }}
        </Button>
      </form>
    </div>
  </div>
</template>
