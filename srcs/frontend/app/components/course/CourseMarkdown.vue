<script setup lang="ts">
/* A lesson body. `v-html` is safe here: the HTML is markdown-it's own, raw
 * HTML in the source escaped, plus KaTeX's (see utils/markdown.ts) */
const { source } = defineProps<{ source: string }>()

const blocks = computed(() => renderCourse(source))
</script>

<template>
  <div class="course-prose">
    <template v-for="(block, index) in blocks" :key="index">
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div v-if="block.type === 'html'" v-html="block.html" />
      <CourseSimulator v-else :name="block.name" />
    </template>
  </div>
</template>
