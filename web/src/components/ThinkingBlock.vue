<template>
  <div class="thinking-block">
    <div class="thinking-header" @click="expanded = !expanded">
      <el-icon class="thinking-icon"><CaretRight :class="{ rotated: expanded }" /></el-icon>
      <span class="thinking-label">思考过程</span>
      <el-tag size="small" type="info" v-if="!expanded">{{ previewText }}</el-tag>
    </div>
    <el-collapse-transition>
      <div v-show="expanded" class="thinking-content">
        <pre>{{ content }}</pre>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { CaretRight } from '@element-plus/icons-vue'

const props = defineProps<{
  content: string
}>()

const expanded = ref(false)

const previewText = computed(() => {
  if (!props.content) return ''
  const text = props.content.replace(/\n/g, ' ').trim()
  return text.length > 50 ? text.slice(0, 50) + '...' : text
})
</script>

<style scoped>
.thinking-block {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin: 8px 0;
  overflow: hidden;
}
.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  background: #f5f7fa;
  user-select: none;
}
.thinking-header:hover {
  background: #ecf5ff;
}
.thinking-icon {
  transition: transform 0.3s;
  font-size: 14px;
}
.thinking-icon.rotated {
  transform: rotate(90deg);
}
.thinking-label {
  font-size: 13px;
  color: #909399;
  font-weight: 500;
}
.thinking-content {
  padding: 12px 16px;
  background: #fafafa;
  border-top: 1px solid #e4e7ed;
}
.thinking-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  color: #606266;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}
</style>
