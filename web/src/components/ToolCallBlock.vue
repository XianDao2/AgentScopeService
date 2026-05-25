<template>
  <div class="tool-call-block" :class="`status-${status}`">
    <div class="tool-call-header">
      <el-icon class="status-icon">
        <Loading v-if="status === 'calling'" class="is-loading" />
        <CircleCheckFilled v-else-if="status === 'completed'" />
        <CircleCloseFilled v-else />
      </el-icon>
      <span class="tool-name">{{ name }}</span>
      <el-tag :type="tagType" size="small">{{ statusLabel }}</el-tag>
    </div>
    <div class="tool-call-body" v-if="expanded">
      <div class="tool-section" v-if="arguments">
        <div class="section-label">参数</div>
        <pre class="section-content">{{ formatArguments }}</pre>
      </div>
      <div class="tool-section" v-if="result">
        <div class="section-label">结果</div>
        <pre class="section-content">{{ result }}</pre>
      </div>
    </div>
    <div class="expand-btn" @click="expanded = !expanded">
      {{ expanded ? '收起' : '展开详情' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Loading, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  name: string
  arguments: string
  result?: string
  status: 'calling' | 'completed' | 'failed'
}>()

const expanded = ref(false)

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    calling: '调用中',
    completed: '已完成',
    failed: '失败',
  }
  return map[props.status] || props.status
})

const tagType = computed(() => {
  const map: Record<string, string> = {
    calling: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[props.status] || 'info'
})

const formatArguments = computed(() => {
  try {
    return JSON.stringify(JSON.parse(props.arguments), null, 2)
  } catch {
    return props.arguments
  }
})
</script>

<style scoped>
.tool-call-block {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin: 8px 0;
  overflow: hidden;
}
.tool-call-block.status-calling {
  border-color: #e6a23c;
}
.tool-call-block.status-completed {
  border-color: #67c23a;
}
.tool-call-block.status-failed {
  border-color: #f56c6c;
}
.tool-call-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
}
.status-icon {
  font-size: 16px;
}
.status-calling .status-icon {
  color: #e6a23c;
}
.status-completed .status-icon {
  color: #67c23a;
}
.status-failed .status-icon {
  color: #f56c6c;
}
.tool-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}
.tool-call-body {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
}
.tool-section {
  margin-bottom: 8px;
}
.tool-section:last-child {
  margin-bottom: 0;
}
.section-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
  font-weight: 500;
}
.section-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  color: #606266;
  background: #fafafa;
  padding: 8px;
  border-radius: 4px;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}
.expand-btn {
  text-align: center;
  padding: 6px;
  font-size: 12px;
  color: #409eff;
  cursor: pointer;
  border-top: 1px solid #e4e7ed;
}
.expand-btn:hover {
  background: #ecf5ff;
}
</style>
