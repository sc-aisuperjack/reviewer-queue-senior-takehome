<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  applyReviewAction,
  fetchReviewItems,
  type ReviewAction,
  type ReviewItem,
} from "./api";

const currentReviewer = "alex";

const terminalStatuses: ReviewItem["status"][] = [
  "approved",
  "rejected",
  "escalated",
];

const items = ref<ReviewItem[]>([]);
const selectedId = ref<string | null>(null);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const pendingAction = ref<ReviewAction | null>(null);

const selectedItem = computed(
  () =>
    items.value.find((item) => item.id === selectedId.value) ??
    items.value[0] ??
    null,
);

const canClaim = computed(() => selectedItem.value?.status === "unassigned");

const canDecide = computed(() => selectedItem.value?.status === "in_review");

const actionHint = computed(() => {
  if (!selectedItem.value) {
    return "No review item is currently selected.";
  }

  if (isTerminalStatus(selectedItem.value.status)) {
    return "This item is closed. No further workflow actions are available.";
  }

  if (canClaim.value) {
    return "This item is unassigned. Claim it before making a decision.";
  }

  if (canDecide.value) {
    return "This item is in review. You can approve, reject, or escalate it.";
  }

  return "No action is currently available for this item.";
});

async function loadItems() {
  isLoading.value = true;
  errorMessage.value = null;

  try {
    items.value = await fetchReviewItems();
    selectedId.value = items.value[0]?.id ?? null;
  } catch (error) {
    errorMessage.value = "Something went wrong loading the queue.";
  } finally {
    isLoading.value = false;
  }
}

async function performAction(action: ReviewAction) {
  if (!selectedItem.value || !isActionAllowed(action)) {
    return;
  }

  pendingAction.value = action;
  errorMessage.value = null;

  try {
    const updated = await applyReviewAction(
      selectedItem.value.id,
      action,
      currentReviewer,
    );

    if (isTerminalStatus(updated.status)) {
      items.value = items.value.filter((item) => item.id !== updated.id);
      selectedId.value = items.value[0]?.id ?? null;
      return;
    }

    items.value = items.value.map((item) =>
      item.id === updated.id ? updated : item,
    );
    selectedId.value = updated.id;
  } catch (error) {
    errorMessage.value = "That action could not be completed.";
  } finally {
    pendingAction.value = null;
  }
}

function isActionAllowed(action: ReviewAction) {
  if (action === "claim") {
    return canClaim.value;
  }

  return canDecide.value;
}

function isTerminalStatus(status: ReviewItem["status"]) {
  return terminalStatuses.includes(status);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

onMounted(loadItems);
</script>

<template>
  <main class="page-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Reviewer workspace</p>
        <h1>Active queue</h1>
      </div>

      <div class="reviewer">Signed in as {{ currentReviewer }}</div>
    </header>

    <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>

    <p v-if="isLoading" class="loading">Loading review items...</p>

    <section v-else class="workspace">
      <aside class="queue-list" aria-label="Review queue">
        <button
          v-for="item in items"
          :key="item.id"
          class="queue-item"
          :class="{ selected: item.id === selectedItem?.id }"
          type="button"
          @click="selectedId = item.id"
        >
          <span class="queue-title">{{ item.title }}</span>
          <span class="queue-meta"
            >{{ item.risk_level }} risk · {{ item.customer_tier }}</span
          >
          <span class="queue-meta"
            >{{ item.status }} ·
            {{ item.assigned_reviewer ?? "unassigned" }}</span
          >
        </button>
      </aside>

      <section v-if="selectedItem" class="detail-panel">
        <div class="detail-header">
          <div>
            <p class="eyebrow">{{ selectedItem.id }}</p>
            <h2>{{ selectedItem.title }}</h2>
          </div>

          <span class="status-pill">{{ selectedItem.status }}</span>
        </div>

        <dl class="facts">
          <div>
            <dt>Submitted</dt>
            <dd>{{ formatDate(selectedItem.submitted_at) }}</dd>
          </div>

          <div>
            <dt>Risk</dt>
            <dd>{{ selectedItem.risk_level }}</dd>
          </div>

          <div>
            <dt>Customer</dt>
            <dd>{{ selectedItem.customer_tier }}</dd>
          </div>

          <div>
            <dt>Assignee</dt>
            <dd>{{ selectedItem.assigned_reviewer ?? "None" }}</dd>
          </div>
        </dl>

        <p class="summary">{{ selectedItem.summary }}</p>

        <p class="notes">{{ selectedItem.notes_count }} notes on this item</p>

        <p class="notes">{{ actionHint }}</p>

        <div class="actions" aria-label="Workflow actions">
          <button
            type="button"
            :disabled="Boolean(pendingAction) || !canClaim"
            @click="performAction('claim')"
          >
            Claim
          </button>

          <button
            type="button"
            :disabled="Boolean(pendingAction) || !canDecide"
            @click="performAction('approve')"
          >
            Approve
          </button>

          <button
            type="button"
            :disabled="Boolean(pendingAction) || !canDecide"
            @click="performAction('reject')"
          >
            Reject
          </button>

          <button
            type="button"
            :disabled="Boolean(pendingAction) || !canDecide"
            @click="performAction('escalate')"
          >
            Escalate
          </button>
        </div>
      </section>

      <section v-else class="detail-panel">
        <p class="summary">There are no active review items.</p>
      </section>
    </section>
  </main>
</template>
